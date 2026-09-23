import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import models, transforms
from PIL import Image
import os
import random
import numpy as np

# =================配置参数=================
N_WAY = 2  # 2个类别 (自定义形态 vs 参照背景形态)
IMG_SIZE = 224
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class DynamicKLineDataset:
    """
    自适应元学习任务生成器：动态读取自定义类和背景参照类，构造 Episode
    """

    def __init__(self, root_dir, classes, k_shot, q_query, transform=None):
        self.data = {}
        self.classes = classes
        self.transform = transform
        self.k_shot = k_shot
        self.q_query = q_query

        for cls in classes:
            cls_path = os.path.join(root_dir, cls)
            images = [os.path.join(cls_path, f) for f in os.listdir(cls_path)
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.data[cls] = images

    def get_episode(self):
        support_batch = []
        query_batch = []

        for i, cls in enumerate(self.classes):
            selected_paths = random.sample(self.data[cls], self.k_shot + self.q_query)
            support_paths = selected_paths[:self.k_shot]
            query_paths = selected_paths[self.k_shot:]

            for p in support_paths:
                img = Image.open(p).convert('RGB')
                if self.transform: img = self.transform(img)
                support_batch.append(img)

            for p in query_paths:
                img = Image.open(p).convert('RGB')
                if self.transform: img = self.transform(img)
                query_batch.append(img)

        support_imgs = torch.stack(support_batch).to(DEVICE)
        query_imgs = torch.stack(query_batch).to(DEVICE)
        query_labels = torch.tensor([i for i in range(N_WAY) for _ in range(self.q_query)]).to(DEVICE)

        return support_imgs, query_imgs, query_labels


class FewShotKLineModel(nn.Module):
    def __init__(self):
        super(FewShotKLineModel, self).__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])

        # 解冻骨干的后半部分（layer3 + layer4），让网络学习图表特征
        for param in self.backbone.parameters():
            param.requires_grad = False
        for param in resnet.layer3.parameters():
            param.requires_grad = True
        for param in resnet.layer4.parameters():
            param.requires_grad = True

        self.adapter = nn.Sequential(
            nn.Flatten(),
            nn.Linear(2048, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 128)
        )

    def forward(self, x):
        features = self.backbone(x)
        out = self.adapter(features)
        return F.normalize(out, p=2, dim=1)


def prototypical_loss(support_emb, query_emb, query_labels, k_shot, q_query):
    z_proto = support_emb.view(N_WAY, k_shot, -1).mean(1)  # (N_WAY, Feature_Dim)
    dists = torch.cdist(query_emb, z_proto)  # (Num_Query_Total, N_Way)
    log_p_y = F.log_softmax(-dists, dim=1)
    loss = F.nll_loss(log_p_y, query_labels)
    _, y_hat = log_p_y.max(1)
    acc = (y_hat == query_labels).float().mean()
    return loss, acc


# 图像预处理
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def run_meta_training_pipeline(model_name, positive_dir, k_shot, q_query, epochs=50):
    """
    【AI 元学习微调核心入口】
    """
    print(f"🔥 [AI 元学习训练启动] 正在为模型【{model_name}】启动原型网络训练...")

    # 1. 初始化数据加载器 (2-Way: 正样本 vs 模型专属背景)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_root = os.path.join(current_dir, "data", "Images")

    # 正样本: image_root/{model_name}/, 负样本: image_root/{model_name}/background/
    classes = [model_name, os.path.join(model_name, "background")]
    # 使用动态计算出来的绝对路径
    dataset = DynamicKLineDataset(image_root, classes, k_shot, q_query, transform=transform)

    # 2. 实例化模型并加载基础适配器权重
    model = FewShotKLineModel().to(DEVICE)
    base_adapter_path = os.path.normpath(os.path.join(current_dir, '..', '..', '..', 'kline_adapter.pth'))
    if os.path.exists(base_adapter_path):
        model.adapter.load_state_dict(torch.load(base_adapter_path, map_location=DEVICE))
    model.train()

    # 差分学习率：骨干后层用小学习率，adapter 用大学习率
    optimizer = optim.Adam([
        {'params': model.backbone.parameters(), 'lr': 0.0001},   # 骨干后层，小学习率微调
        {'params': model.adapter.parameters(), 'lr': 0.001},       # adapter，正常学习率
    ])

    # 3. 运行微调
    for epoch in range(epochs):
        s_imgs, q_imgs, q_labels = dataset.get_episode()

        all_imgs = torch.cat([s_imgs, q_imgs], dim=0)
        all_features = model(all_imgs)

        s_features = all_features[:len(s_imgs)]
        q_features = all_features[len(s_imgs):]

        loss, acc = prototypical_loss(s_features, q_features, q_labels, k_shot, q_query)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"   Episode [{epoch + 1}/{epochs}] | Loss: {loss.item():.4f} | Acc: {acc.item() * 100:.2f}%")

    # 4. 保存你专属的适配器神经网络权重 (.pth)
    os.makedirs("custom_modes", exist_ok=True)
    adapter_save_path = os.path.join("custom_modes", f"{model_name}_adapter.pth")
    torch.save(model.adapter.state_dict(), adapter_save_path)
    print(f"💾 个性化权重网络已保存: {adapter_save_path}")

    # 5. 计算并固化正样本的原型中心向量 (.npy)
    model.eval()
    with torch.no_grad():
        pos_paths = [os.path.join(positive_dir, f) for f in os.listdir(positive_dir) if f.endswith('.jpg')]
        pos_tensors = torch.stack([transform(Image.open(p).convert('RGB')) for p in pos_paths]).to(DEVICE)

        final_feats = model(pos_tensors).cpu().numpy()
        prototype = np.mean(final_feats, axis=0)
        prototype /= (np.linalg.norm(prototype) + 1e-8)

        proto_save_path = os.path.join("custom_modes", f"{model_name}.npy")
        np.save(proto_save_path, prototype)
        print(f"💾 专属特征重心(Prototype)已固化: {proto_save_path}")

    return True