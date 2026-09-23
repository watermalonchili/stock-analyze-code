import os
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import glob


class KLineDataset:
    def __init__(self, data_path, n_way=4, k_shot=2, query_size=2):
        self.data_path = data_path
        self.n_way = n_way
        self.k_shot = k_shot
        self.query_size = query_size

        # 增强的数据预处理 - 添加数据增强
        self.transform = transforms.Compose([
            transforms.Grayscale(),
            transforms.Resize((128, 128)),
            transforms.RandomHorizontalFlip(p=0.5),  # 随机水平翻转
            transforms.RandomRotation(5),  # 随机旋转
            transforms.ColorJitter(brightness=0.2, contrast=0.2),  # 亮度和对比度调整
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])

        # 加载数据
        self.classes = ['bullish_arc', 'bearish_arc', 'bullish_flag', 'bearish_flag']
        self.data = self._load_data()
        print(f"数据加载完成: {[f'{cls}: {len(imgs)}张' for cls, imgs in self.data.items()]}")

    def _load_data(self):
        data = {}
        for class_name in self.classes:
            # 查找所有可能的图像文件
            patterns = [
                os.path.join(self.data_path, class_name, "*.png"),
                os.path.join(self.data_path, class_name, "*.jpg"),
                os.path.join(self.data_path, class_name, "*.jpeg"),
                os.path.join(self.data_path, f"*{class_name}*.png"),
                os.path.join(self.data_path, f"*{class_name}*.jpg"),
                os.path.join(self.data_path, f"*{class_name}*.jpeg"),
            ]

            images = []
            for pattern in patterns:
                images.extend(glob.glob(pattern))

            # 去重
            images = list(set(images))
            data[class_name] = images

        return data


def create_episode(dataset, n_way=4, k_shot=2, query_size=2):
    """创建一个训练episode - 适配少量数据"""
    support_images = []
    query_images = []
    support_labels = []
    query_labels = []

    # 检查每个类别的样本数量是否足够
    available_classes = []
    for class_name in dataset.classes:
        if len(dataset.data[class_name]) >= (k_shot + query_size):
            available_classes.append(class_name)

    if len(available_classes) < n_way:
        # 如果类别不足，使用所有可用类别
        n_way = len(available_classes)
        if n_way < 2:  # 至少需要2个类别
            return None, None, None, None

    selected_classes = np.random.choice(available_classes, n_way, replace=False)

    for class_idx, class_name in enumerate(selected_classes):
        class_images = dataset.data[class_name]

        # 如果数据量刚好等于需要的数量，直接使用所有图片
        if len(class_images) == (k_shot + query_size):
            selected_images = class_images
        else:
            # 随机选择图片，允许重复选择（对小样本数据很重要）
            selected_images = np.random.choice(
                class_images,
                k_shot + query_size,
                replace=True  # 允许重复选择同一张图片
            )

        # 支持集
        for img_path in selected_images[:k_shot]:
            try:
                img = Image.open(img_path)
                img = dataset.transform(img)
                support_images.append(img)
                support_labels.append(class_idx)
            except Exception as e:
                print(f"加载图像失败: {img_path}, 错误: {e}")
                continue

        # 查询集
        for img_path in selected_images[k_shot:k_shot + query_size]:
            try:
                img = Image.open(img_path)
                img = dataset.transform(img)
                query_images.append(img)
                query_labels.append(class_idx)
            except Exception as e:
                print(f"加载图像失败: {img_path}, 错误: {e}")
                continue

    if len(support_images) == 0 or len(query_images) == 0:
        return None, None, None, None

    return (torch.stack(support_images),
            torch.stack(query_images),
            torch.tensor(support_labels),
            torch.tensor(query_labels))