# few_shot_utils.py
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import os

# 均线颜色配置
MA_COLORS = {
    'MA4': '#000000', 'MA8': '#FF9800', 'MA12': '#E91E63',
    'MA16': '#9C27B0', 'MA20': '#4CAF50', 'MA47': '#2196F3'
}


class FewShotKLineModel(nn.Module):
    def __init__(self):
        super(FewShotKLineModel, self).__init__()
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
        out = self.adapter(features)
        return F.normalize(out, p=2, dim=1)


class KLineAIEngine:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.model = FewShotKLineModel().to(self.device)
        self.model.eval()
        self.base_model_path = model_path

    def prepare_tensor(self, window_df, ma_list, analysis_mode='MA'):
        """根据分析模式生成对应的图片（均线图 或 K线蜡烛图），与训练时一致"""
        plt.figure(figsize=(2.24, 2.24), dpi=100)

        if analysis_mode.upper() == 'KLINE':
            # K线蜡烛图（与训练时 create_kline_skeleton_chart 一致）
            plot_data = window_df.reset_index(drop=True)
            if 'open' not in plot_data.columns:
                plot_data['open'] = plot_data['close'].shift(1).fillna(plot_data['close'].iloc[0])
                plot_data['high'] = plot_data[['open', 'close']].max(axis=1) * 1.01
                plot_data['low'] = plot_data[['open', 'close']].min(axis=1) * 0.99
            up = plot_data[plot_data.close >= plot_data.open]
            down = plot_data[plot_data.close < plot_data.open]
            if not up.empty:
                plt.bar(up.index, up.close - up.open, bottom=up.open, color='red', width=0.6)
                plt.bar(up.index, up.high - up.close, bottom=up.close, color='red', width=0.1)
                plt.bar(up.index, up.low - up.open, bottom=up.open, color='red', width=0.1)
            if not down.empty:
                plt.bar(down.index, down.open - down.close, bottom=down.close, color='green', width=0.6)
                plt.bar(down.index, down.high - down.open, bottom=down.open, color='green', width=0.1)
                plt.bar(down.index, down.low - down.close, bottom=down.close, color='green', width=0.1)
        else:
            # 均线图（与训练时 create_chart 一致）
            for ma_num in [4, 8, 12, 16, 20, 47]:
                ma_name = f'MA{ma_num}'
                if ma_name in window_df.columns:
                    plt.plot(range(len(window_df)), window_df[ma_name], color=MA_COLORS[ma_name], linewidth=1.5)

        plt.axis('off')
        plt.gca().set_position([0, 0, 1, 1])
        buf = io.BytesIO()
        plt.savefig(buf, format='jpg', facecolor='white', pad_inches=0)
        plt.close()
        buf.seek(0)
        img = Image.open(buf).convert('RGB')
        return self.transform(img).unsqueeze(0).to(self.device)

    def extract_feature(self, window_df, ma_list):
        input_tensor = self.prepare_tensor(window_df, ma_list)
        with torch.no_grad():
            feat = self.model(input_tensor)
            return feat.squeeze(0).cpu().numpy()

    def get_custom_prototype(self, mode_index):
        path = os.path.join("custom_modes", f"{mode_index}.npy")
        if os.path.exists(path):
            return np.load(path)
        return None

    def get_analysis_mode(self, mode_index):
        """从模型元数据或 modeListSelf.json 读取分析模式"""
        import json
        # 优先从模型图片目录的 meta.json 读取
        meta_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "few_shot_learning", "version525", "data", "Images", mode_index, "meta.json"
        )
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get('analysisMode', 'MA')
            except Exception:
                pass
        # 兜底从 modeListSelf.json 读取
        try:
            from json_config import read_json_data
            modes = read_json_data()
            for m in modes:
                if m.get('index') == mode_index or m.get('name') == mode_index:
                    return m.get('analysis_mode', 'MA')
        except Exception:
            pass
        return 'MA'

    def get_score(self, window_df, ma_list, target_idx, mode_index):
        """
        【2-Way 原型分类概率计算】
        """
        analysis_mode = self.get_analysis_mode(mode_index)
        input_tensor = self.prepare_tensor(window_df, ma_list, analysis_mode)

        # 1. 动态加载该自定义模型的专属特征重心 (.npy)
        pos_proto = self.get_custom_prototype(mode_index)
        if pos_proto is None:
            return 0.0

        # 2. 加载模型专属背景重心（优先），兜底用共享背景
        bg_proto = self.get_custom_prototype(f"{mode_index}_bg")
        if bg_proto is None:
            bg_proto = self.get_custom_prototype("background_class")
        if bg_proto is None:
            bg_proto = np.zeros_like(pos_proto)

        # 3. 动态加载该自定义模型微调后的专属权重网络 (.pth)
        custom_adapter = os.path.join("custom_modes", f"{mode_index}_adapter.pth")
        load_path = custom_adapter if os.path.exists(custom_adapter) else self.base_model_path

        try:
            self.model.adapter.load_state_dict(torch.load(load_path, map_location=self.device))
            self.model.eval()
        except Exception as e:
            print(f"警告: 加载适配器权重失败 {e}，将使用基础权重。")

        with torch.no_grad():
            # 4. 提取当前窗口的高维特征向量
            query_feat = self.model(input_tensor).flatten().cpu().numpy()

            # 5. 计算到两个特征中心的欧氏距离
            dist_pos = np.linalg.norm(query_feat - pos_proto)
            dist_bg = np.linalg.norm(query_feat - bg_proto)

            # 6. 距离差（margin），越大越像正样本
            margin = float(dist_bg - dist_pos)

            # 7. 使用 margin-based sigmoid 打分
            # temperature=10：陡峭度高，只有margin很大的才得高分，避免不相似的也得0.96
            probability = 1.0 / (1.0 + np.exp(-margin * 10.0))

            return float(probability)


_instance = None


def get_ai_engine():
    global _instance
    if _instance is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "kline_adapter.pth")
        _instance = KLineAIEngine(model_path=model_path)
    return _instance