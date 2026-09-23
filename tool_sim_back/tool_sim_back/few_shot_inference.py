# few_shot_inference.py

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import os
import io
import matplotlib

matplotlib.use('Agg')  # 后端绘图模式，不弹窗
import matplotlib.pyplot as plt
import mplfinance as mpf

# ================= 配置 =================
# 确保这里的路径指向你存放参考图片(用于构建原型)的文件夹
DATA_DIR = "public/reference_images"  # 建议把 data/Images 里的每类前5张拷到这里
CLASSES = ['bearish_arc', 'bearish_flag', 'bullish_arc', 'bullish_flag']
IMG_SIZE = 224
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ================= 模型结构 (必须与 main.py 一致) =================
class FewShotKLineModel(nn.Module):
    def __init__(self):
        super(FewShotKLineModel, self).__init__()
        # 注意：这里 weights=None，因为我们会加载自己的 pth
        resnet = models.resnet50(weights=None)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        self.adapter = nn.Sequential(
            nn.Flatten(),
            nn.Linear(2048, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 128)
        )

    def forward(self, x):
        features = self.backbone(x)
        return F.normalize(self.adapter(features), dim=1)


# 预处理
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


class KLinePredictor:
    def __init__(self, model_path):
        self.device = DEVICE
        self.model = self._load_model(model_path)
        self.prototypes = None  # 初始化时为空，需要调用 build_prototypes
        self.classes = CLASSES

    def _load_model(self, model_path):
        print(f"Loading model from {model_path}...")
        model = FewShotKLineModel().to(self.device)
        state_dict = torch.load(model_path, map_location=self.device)
        # 处理可能的 key 不匹配 (如果有 module. 前缀)
        if 'adapter.0.weight' not in state_dict and list(state_dict.keys())[0].startswith('adapter.'):
            model.adapter.load_state_dict(state_dict)
        else:
            # 如果保存的是整个 state_dict (包含 backbone)，可能需要过滤
            # 假设你保存的只是 adapter (如 main.py 所示)
            try:
                model.adapter.load_state_dict(state_dict, strict=False)
            except:
                # 尝试加载整个模型
                model.load_state_dict(state_dict, strict=False)

        model.eval()
        return model

    def build_prototypes(self, ref_data_dir):
        """构建参考系：需要每个类别至少有几张参考图"""
        print(f"Building prototypes from {ref_data_dir}...")
        prototypes = []
        for cls in self.classes:
            cls_path = os.path.join(ref_data_dir, cls)
            if not os.path.exists(cls_path):
                # 如果没有参考图，这就没法工作，给个全0向量避免报错，但在日志警告
                print(f"Warning: No reference images for {cls}")
                prototypes.append(torch.zeros(128).to(self.device))
                continue

            images = [os.path.join(cls_path, f) for f in os.listdir(cls_path)
                      if f.lower().endswith(('.png', '.jpg'))][:5]  # 取前5张

            batch = []
            for p in images:
                img = Image.open(p).convert('RGB')
                batch.append(transform(img))

            if len(batch) > 0:
                batch_tensor = torch.stack(batch).to(self.device)
                with torch.no_grad():
                    feats = self.model(batch_tensor)
                    prototypes.append(feats.mean(dim=0))
            else:
                prototypes.append(torch.zeros(128).to(self.device))

        self.prototypes = torch.stack(prototypes)
        print("Prototypes built.")

    def dataframe_to_image(self, df):
        """核心：将 DataFrame 切片转为模型可读的 Image 对象"""
        # 必须确保格式和训练时一致 (例如黑白、无坐标轴、包含均线)
        # 这里使用 mplfinance 快速绘图

        # 配置 style，使其尽量接近训练数据
        # 假设训练数据是黑白线稿或者标准K线
        mc = mpf.make_marketcolors(up='red', down='green', edge='i', wick='i', volume='in')
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle='', rc={'font.size': 8})

        buf = io.BytesIO()
        # 绘图：不显示坐标轴，不显示Volume
        # 注意：mav=(5,10,20) 要看你训练数据里有没有均线，如果没有就去掉
        mpf.plot(df, type='candle', style=s, mav=(5, 10, 20),
                 axisoff=True, volume=False, savefig=dict(fname=buf, dpi=100, bbox_inches='tight'))

        buf.seek(0)
        img = Image.open(buf).convert('RGB')
        return img

    def predict_segment(self, df_window):
        """预测一个 DataFrame 片段"""
        if self.prototypes is None:
            raise ValueError("Prototypes not built! Call build_prototypes first.")

        # 1. 转图片
        img = self.dataframe_to_image(df_window)

        # 2. 转 Tensor
        img_tensor = transform(img).unsqueeze(0).to(self.device)

        # 3. 推理
        with torch.no_grad():
            query_feat = self.model(img_tensor)  # (1, 128)
            dists = torch.cdist(query_feat, self.prototypes)  # (1, 4)
            scores = F.softmax(-dists, dim=1)  # 距离越小概率越大

            best_idx = torch.argmin(dists).item()
            best_class = self.classes[best_idx]
            confidence = scores[0][best_idx].item()

        return best_class, confidence