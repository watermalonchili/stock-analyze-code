import torch
import torch.nn as nn
import torch.nn.functional as F


class KLineEmbeddingNet(nn.Module):
    """专门为K线图设计的嵌入网络"""

    def __init__(self, input_dim=1, hidden_dim=64, output_dim=128):
        super().__init__()
        self.encoder = nn.Sequential(
            # 第一层卷积
            nn.Conv2d(input_dim, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # 第二层卷积
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # 第三层卷积
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),

            # 全局平均池化
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),

            # 全连接层
            nn.Linear(128, output_dim)
        )

    def forward(self, x):
        return self.encoder(x)



class PrototypicalNetwork(nn.Module):
    def __init__(self, n_way=4, k_shot=5, query_size=5):
        super().__init__()
        self.n_way = n_way
        self.k_shot = k_shot
        self.query_size = query_size
        self.embedding_net = KLineEmbeddingNet()

    def compute_prototypes(self, support_embeddings, support_labels):
        """计算每个类别的原型"""
        prototypes = []
        for class_id in range(self.n_way):
            # 选择当前类别的支持集嵌入
            mask = (support_labels == class_id)
            class_embeddings = support_embeddings[mask]
            # 计算均值作为原型
            prototype = class_embeddings.mean(dim=0)
            prototypes.append(prototype)
        return torch.stack(prototypes)

    def euclidean_distance(self, x, y):
        """计算欧式距离"""
        n = x.size(0)
        m = y.size(0)
        d = x.size(1)

        x = x.unsqueeze(1).expand(n, m, d)
        y = y.unsqueeze(0).expand(n, m, d)

        return torch.pow(x - y, 2).sum(2)

    def forward(self, support_images, support_labels, query_images):
        """前向传播"""
        # 获取所有图像的嵌入
        all_images = torch.cat([support_images, query_images], 0)
        all_embeddings = self.embedding_net(all_images)

        # 分离支持集和查询集嵌入
        support_embeddings = all_embeddings[:len(support_images)]
        query_embeddings = all_embeddings[len(support_images):]

        # 计算原型
        prototypes = self.compute_prototypes(support_embeddings, support_labels)

        # 计算距离
        distances = self.euclidean_distance(query_embeddings, prototypes)

        # 转换为概率（负距离的softmax）
        logits = -distances
        return logits