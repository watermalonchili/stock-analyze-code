# conditional_timegan.py
"""
条件 TimeGAN：基于骨架+特征+种子的多尺度仿真K线生成器

架构：两阶段混合
  Phase 1 — 统计引导生成器（零样本，即时可用）
  Phase 2 — 轻量条件序列 VAE-GAN（种子少样本微调）
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import hashlib

# ============================================================
# 常量
# ============================================================
SEQ_LEN = 20
INPUT_DIM = 11
LATENT_DIM = 64
COND_DIM = 64
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MA_LIST = [4, 8, 12, 16, 20, 47]


# ============================================================
# 1. 输入表示
# ============================================================
def encode_sequence(df_dict_list, ma_list=MA_LIST):
    """将 OHLCV+MA 字典列表转为 (SEQ_LEN, 11) 的归一化张量"""
    df = pd.DataFrame(df_dict_list)
    for col in ['open', 'close', 'high', 'low', 'vol']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    for m in ma_list:
        c = f'MA{m}'
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

    n = len(df)
    features = np.zeros((n, INPUT_DIM), dtype=np.float32)
    close = df['close'].values.astype(np.float64)

    for i in range(n):
        c = close[i] if close[i] != 0 else 1.0
        o = df['open'].iloc[i] if not pd.isna(df['open'].iloc[i]) else c
        h = df['high'].iloc[i] if not pd.isna(df['high'].iloc[i]) else c
        l = df['low'].iloc[i] if not pd.isna(df['low'].iloc[i]) else c
        v = df['vol'].iloc[i] if 'vol' in df.columns and not pd.isna(df['vol'].iloc[i]) else 1.0

        features[i, 0] = (c - o) / o if o != 0 else 0  # close_to_open
        features[i, 1] = max((h - c) / c, 0) if c != 0 else 0  # high_to_close
        features[i, 2] = min((l - c) / c, 0) if c != 0 else 0  # low_to_close
        features[i, 3] = (close[i] / close[i-1] - 1) if i > 0 and close[i-1] != 0 else 0  # return
        mean_vol = np.mean(np.abs(df['vol'].values.astype(float))) if 'vol' in df.columns else 1.0
        features[i, 4] = v / mean_vol if mean_vol != 0 else 1.0  # vol_ratio
        for j, m in enumerate(ma_list):
            mc = f'MA{m}'
            val = df[mc].iloc[i] if mc in df.columns and not pd.isna(df[mc].iloc[i]) else c
            features[i, 5 + j] = val / c if c != 0 else 1.0  # MA_ratio

    # 裁剪或填充到 SEQ_LEN
    if n >= SEQ_LEN:
        features = features[-SEQ_LEN:]
    else:
        pad = np.zeros((SEQ_LEN - n, INPUT_DIM), dtype=np.float32)
        features = np.concatenate([pad, features])

    return torch.FloatTensor(features), close[0] if len(close) > 0 else 1.0


def decode_to_ohlcv(raw_output, first_close, ma_list=MA_LIST):
    """将模型输出 (SEQ_LEN, 11) 解码回 OHLCV+MA 字典列表"""
    close = first_close
    records = []
    for i in range(raw_output.shape[0]):
        r = raw_output[i]
        ret = float(r[3])
        c = close * (1 + ret) if i > 0 else close
        o = c / (1 + float(r[0])) if (1 + float(r[0])) != 0 else c
        h = c * (1 + max(float(r[1]), 0))
        l = c * (1 + min(float(r[2]), 0))
        # 硬约束
        h = max(h, o, c)
        l = min(l, o, c)
        if h < l:
            h, l = max(h, l), min(h, l)
        rec = {
            'trade_date': f'day_{i}',
            'open': round(float(o), 4),
            'close': round(float(c), 4),
            'high': round(float(h), 4),
            'low': round(float(l), 4),
            'vol': round(abs(float(r[4])) * 1e6, 0)
        }
        for j, m in enumerate(ma_list):
            ma_val = c * float(r[5 + j])
            rec[f'MA{m}'] = round(float(ma_val), 4)
        records.append(rec)
        close = c
    return records


# ============================================================
# 2. 条件编码器
# ============================================================
class SkeletonEncoder(nn.Module):
    """骨架 → 32维"""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(2, 16, 3, padding=1)
        self.conv2 = nn.Conv1d(16, 32, 3, padding=1)
        self.pool = nn.AdaptiveAvgPool1d(1)

    def forward(self, x):
        # x: (B, 2, 20) — [price_norm, weight]
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = self.pool(x).flatten(1)
        return x  # (B, 32)


class FeatureEncoder(nn.Module):
    """特征文本 → 16维"""
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(8, 16)
        self.fc2 = nn.Linear(16, 16)

    def forward(self, x):
        return self.fc2(F.relu(self.fc1(x)))


def parse_features_to_vector(features):
    """将特征文本列表解析为8维向量"""
    import re
    vec = [0.5] * 8  # 默认中性
    # vec: [volatility, trend_strength, crossover, entanglement, drawdown, recovery, volume_surge, consolidation]
    for feat in features:
        if not isinstance(feat, str):
            continue
        fl = feat.lower()
        m = re.search(r'(\d+(?:\.\d+)?)\s*%', feat)
        if m:
            vec[0] = min(float(m.group(1)) / 50.0, 1.0)  # 波动率归一化
        if any(w in fl for w in ['上行', '上涨', '上升']):
            vec[1] = 0.8
        elif any(w in fl for w in ['下行', '下跌', '下降']):
            vec[1] = 0.2
        if any(w in fl for w in ['金叉', '上穿', '交叉']):
            vec[2] = 0.9
        if any(w in fl for w in ['纠缠', '密集', '缠绕']):
            vec[3] = 0.9
        if any(w in fl for w in ['回撤', '回落']):
            vec[4] = 0.8
        if any(w in fl for w in ['放量', '放大', '成交量']):
            vec[6] = 0.9
        if any(w in fl for w in ['横盘', '盘整', '震荡']):
            vec[7] = 0.8
        m2 = re.search(r'(\d+)\s*天', feat)
        if m2:
            vec[3] = min(int(m2.group(1)) / 30.0, 1.0)
    return np.array(vec, dtype=np.float32)


def extract_seed_statistics(seeds):
    """从种子提取24维统计向量"""
    all_close = []
    all_intraday = []
    all_shadow_up = []
    all_shadow_down = []
    all_returns = []

    for seed in seeds:
        df = pd.DataFrame(seed)
        for col in ['open', 'close', 'high', 'low']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        close = df['close'].dropna().values.astype(float)
        if len(close) < 2:
            continue
        all_close.extend(close.tolist())
        returns = np.diff(close) / close[:-1]
        all_returns.extend(returns.tolist())

        for i in range(len(df)):
            c = df['close'].iloc[i] if not pd.isna(df['close'].iloc[i]) else 0
            h = df['high'].iloc[i] if not pd.isna(df['high'].iloc[i]) else c
            l = df['low'].iloc[i] if not pd.isna(df['low'].iloc[i]) else c
            o = df['open'].iloc[i] if not pd.isna(df['open'].iloc[i]) else c
            if c > 0:
                all_intraday.append((h - l) / c)
                body = abs(c - o)
                total = h - l
                if total > 0:
                    all_shadow_up.append((h - max(c, o)) / total)
                    all_shadow_down.append((min(c, o) - l) / total)

    stats = np.zeros(24, dtype=np.float32)

    if all_returns:
        r = np.array(all_returns)
        stats[0] = np.mean(r)  # 均值收益率
        stats[1] = np.std(r)   # 收益率标准差
        # AR(1) 系数
        if len(r) > 2:
            stats[2] = np.corrcoef(r[:-1], r[1:])[0, 1] if np.std(r[:-1]) > 0 else 0
        else:
            stats[2] = 0

    if all_intraday:
        stats[3] = np.mean(all_intraday)  # 均值振幅
        stats[4] = np.std(all_intraday)   # 振幅标准差

    if all_shadow_up:
        stats[5] = np.mean(all_shadow_up)
    if all_shadow_down:
        stats[6] = np.mean(all_shadow_down)

    if all_returns and len(all_returns) > 1:
        stats[7] = np.mean(np.sign(all_returns) == np.sign([all_returns[0]] + list(all_returns[:-1])))  # 自相关

    # 连续涨跌统计
    if all_returns:
        signs = np.sign(all_returns)
        streak = 1
        max_streak = 1
        for i in range(1, len(signs)):
            if signs[i] == signs[i-1]:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1
        stats[8] = max_streak / 20.0

    # 最大回撤
    if len(all_close) > 1:
        cummax = np.maximum.accumulate(all_close)
        drawdowns = (np.array(all_close) - cummax) / cummax
        stats[9] = abs(np.min(drawdowns))

    # MA 比率均值 (slots 10-15)
    for seed in seeds:
        df = pd.DataFrame(seed)
        close_val = pd.to_numeric(df['close'], errors='coerce').dropna()
        if len(close_val) == 0:
            continue
        mean_c = close_val.mean()
        for j, m in enumerate(MA_LIST):
            mc = f'MA{m}'
            if mc in df.columns:
                vals = pd.to_numeric(df[mc], errors='coerce').dropna()
                if len(vals) > 0 and mean_c > 0:
                    stats[10 + j] = (stats[10 + j] + vals.mean() / mean_c) / 2

    stats[16:24] = 0.5  # 预留位
    return stats


class ConditionProjector(nn.Module):
    """72维 → 64维"""
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(72, 64)

    def forward(self, x):
        return torch.tanh(self.fc(x))


# ============================================================
# 3. VAE 编码器 / 解码器
# ============================================================
class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(input_size=INPUT_DIM + COND_DIM, hidden_size=128,
                          num_layers=2, bidirectional=True, batch_first=True)
        self.mu = nn.Linear(256, LATENT_DIM)
        self.logvar = nn.Linear(256, LATENT_DIM)

    def forward(self, x, cond):
        # x: (B, T, 11), cond: (B, 64)
        cond_exp = cond.unsqueeze(1).expand(-1, x.size(1), -1)
        xc = torch.cat([x, cond_exp], dim=-1)
        out, _ = self.gru(xc)
        h = torch.cat([out[:, -1, :128], out[:, 0, 128:]], dim=-1)
        return self.mu(h), self.logvar(h)

    def encode_per_step(self, x, cond):
        """返回每步的隐状态用于 Supervisor"""
        cond_exp = cond.unsqueeze(1).expand(-1, x.size(1), -1)
        xc = torch.cat([x, cond_exp], dim=-1)
        out, _ = self.gru(xc)
        return out  # (B, T, 256)


class Decoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.init_fc = nn.Linear(LATENT_DIM + COND_DIM, 128)
        self.gru = nn.GRU(input_size=128 + COND_DIM, hidden_size=128,
                          num_layers=2, batch_first=True)
        self.out_fc = nn.Linear(128, INPUT_DIM)

    def forward(self, z, cond):
        zc = torch.cat([z, cond], dim=-1)
        h0 = F.relu(self.init_fc(zc)).unsqueeze(0).repeat(2, 1, 1)  # (2, B, 128)
        cond_exp = cond.unsqueeze(1).expand(-1, SEQ_LEN, -1)
        init_input = h0[-1].unsqueeze(1).expand(-1, SEQ_LEN, -1)
        dec_input = torch.cat([init_input, cond_exp], dim=-1)
        out, _ = self.gru(dec_input, h0)
        raw = self.out_fc(out)  # (B, T, 11)
        # 金融约束
        result = raw.clone()
        result[:, :, 1] = F.relu(raw[:, :, 1])    # high ≥ 0
        result[:, :, 2] = -F.relu(-raw[:, :, 2])   # low ≤ 0
        return result


class Discriminator(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(input_size=INPUT_DIM + COND_DIM, hidden_size=64,
                          num_layers=2, batch_first=True)
        self.fc1 = nn.Linear(64 + COND_DIM, 64)
        self.fc2 = nn.Linear(64, 1)

    def forward(self, x, cond):
        cond_exp = cond.unsqueeze(1).expand(-1, x.size(1), -1)
        xc = torch.cat([x, cond_exp], dim=-1)
        _, h = self.gru(xc)
        h_last = h[-1]  # (B, 64)
        hc = torch.cat([h_last, cond], dim=-1)
        return self.fc2(F.leaky_relu(self.fc1(hc), 0.2))


class Supervisor(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc_in = nn.Linear(256, 64)
        self.gru = nn.GRU(input_size=64, hidden_size=64, num_layers=1, batch_first=True)
        self.fc_out = nn.Linear(64, 64)

    def forward(self, h_seq):
        # h_seq: (B, T, 256) from encoder
        z_seq = F.relu(self.fc_in(h_seq))  # (B, T, 64)
        out, _ = self.gru(z_seq[:, :-1, :])
        return self.fc_out(out), z_seq[:, 1:, :]  # pred, target


# ============================================================
# 4. 完整 ConditionalTimeGAN
# ============================================================
class ConditionalTimeGAN(nn.Module):
    def __init__(self):
        super().__init__()
        self.sk_enc = SkeletonEncoder()
        self.feat_enc = FeatureEncoder()
        self.cond_proj = ConditionProjector()
        self.encoder = Encoder()
        self.decoder = Decoder()
        self.discriminator = Discriminator()
        self.supervisor = Supervisor()

    def encode_condition(self, skeleton, features_text, seed_stats):
        """编码所有条件为 (B, 64)"""
        batch_size = 1
        # 骨架
        if skeleton and len(skeleton) >= 2:
            sk_tensor = self._skeleton_to_tensor(skeleton, batch_size).to(DEVICE)
            sk_vec = self.sk_enc(sk_tensor)
        else:
            sk_vec = torch.zeros(batch_size, 32, device=DEVICE)

        # 特征
        feat_vec_np = parse_features_to_vector(features_text)
        feat_vec = self.feat_enc(torch.FloatTensor(feat_vec_np).unsqueeze(0).to(DEVICE))

        # 种子统计
        seed_vec = torch.FloatTensor(seed_stats).unsqueeze(0).to(DEVICE)

        # 拼接 + 投影
        cond_raw = torch.cat([sk_vec, feat_vec, seed_vec], dim=-1)
        return self.cond_proj(cond_raw)

    def _skeleton_to_tensor(self, skeleton, batch_size):
        """骨架点插值到20点 → (B, 2, 20)"""
        points = sorted(skeleton, key=lambda p: p.get('date', ''))
        prices = [float(p.get('price', 0)) for p in points]
        weights = [float(p.get('weight', 1.0)) for p in points]

        p_min, p_max = min(prices), max(prices)
        p_range = p_max - p_min if p_max != p_min else 1.0
        prices_norm = [(p - p_min) / p_range for p in prices]

        # 线性插值到20点
        n = len(prices_norm)
        indices = np.linspace(0, n - 1, SEQ_LEN)
        interp_prices = np.interp(indices, np.arange(n), prices_norm)
        interp_weights = np.interp(indices, np.arange(n), weights)

        tensor = np.stack([interp_prices, interp_weights], axis=0)  # (2, 20)
        return torch.FloatTensor(tensor).unsqueeze(0).expand(batch_size, -1, -1).clone()

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def generate_from_latent(self, z, cond):
        raw = self.decoder(z, cond)
        return raw


# ============================================================
# 5. Phase 1: 统计引导生成（零样本，核心生成器）
# ============================================================
def statistical_conditional_generation(seeds, skeleton, features, ma_list=MA_LIST, num_samples=8,
                                        generation=1, good_samples=None, bad_samples=None):
    """基于种子统计 + 骨架方向 + 特征约束的零样本生成，支持递归反馈"""
    # 种子池扩充：原始种子 + 高分反馈样本
    all_seeds = list(seeds)
    if good_samples:
        all_seeds.extend(good_samples)
        print(f"[TimeGAN Gen{generation}] 种子池扩充: +{len(good_samples)} 个高分样本")

    stats = extract_seed_statistics(all_seeds)

    # 从种子提取 AR(1) 参数
    all_returns = []
    first_close = None
    for seed in all_seeds:
        df = pd.DataFrame(seed)
        close = pd.to_numeric(df['close'], errors='coerce').dropna().values.astype(float)
        if len(close) > 1:
            if first_close is None:
                first_close = close[0]
            r = np.diff(close) / close[:-1]
            all_returns.extend(r.tolist())

    if first_close is None:
        first_close = 10.0

    mean_ret = np.mean(all_returns) if all_returns else 0
    std_ret = max(np.std(all_returns), 0.005) if all_returns else 0.015
    ar1_coef = stats[2] if not np.isnan(stats[2]) else 0.0

    # 骨架目标收益率序列
    skeleton_returns = None
    if skeleton and len(skeleton) >= 2:
        pts = sorted(skeleton, key=lambda p: p.get('date', ''))
        prices = np.array([float(p.get('price', 0)) for p in pts])
        # 插值到 SEQ_LEN 点
        indices = np.linspace(0, len(prices) - 1, SEQ_LEN)
        interp = np.interp(indices, np.arange(len(prices)), prices)
        log_interp = np.log(interp)
        skeleton_returns = np.diff(log_interp)  # 目标对数收益率

    # 从特征提取波动率缩放因子
    vol_scale = 1.0
    for feat in features:
        if isinstance(feat, str):
            import re
            m = re.search(r'(\d+(?:\.\d+)?)\s*%', feat)
            if m:
                target_vol = float(m.group(1)) / 100.0
                current_vol = std_ret * np.sqrt(SEQ_LEN)
                if current_vol > 0:
                    vol_scale = target_vol / current_vol
                    vol_scale = max(0.3, min(vol_scale, 2.0))

    # 收集种子的 OHLCV 比率经验分布
    ohcv_ratios = []  # (open/close, high/close, low/close)
    for seed in all_seeds:
        df = pd.DataFrame(seed)
        for _, row in df.iterrows():
            c = float(row.get('close', 0))
            if c <= 0:
                continue
            o = float(row.get('open', c))
            h = float(row.get('high', c))
            l = float(row.get('low', c))
            ohcv_ratios.append((o / c, h / c, l / c))

    samples = []
    rng = np.random.RandomState(int(os.getpid() * 1000 + id(seeds)) % (2**31))

    # 代际收敛参数
    residual_scale = 0.9 ** (generation - 1)   # 每代残差标准差×0.9
    skeleton_weight = min(0.7, 0.4 + 0.1 * (generation - 1))  # 骨架权重递增

    # 提取坏样本的特征禁区（波动率/振幅/回撤的范围）
    bad_zones = {}
    if bad_samples:
        bad_feats = []
        for bs in bad_samples:
            df_b = pd.DataFrame(bs)
            close_b = pd.to_numeric(df_b['close'], errors='coerce').dropna().values.astype(float)
            if len(close_b) >= 2:
                rets_b = np.diff(close_b) / close_b[:-1]
                bad_feats.append({
                    'volatility': float(np.std(rets_b) * 100),
                    'amplitude': float((close_b.max() - close_b.min()) / close_b.mean() * 100) if close_b.mean() > 0 else 0,
                })
        if bad_feats:
            for key in ['volatility', 'amplitude']:
                vals_z = [f[key] for f in bad_feats if f[key] > 0]
                if vals_z:
                    bad_zones[key] = (min(vals_z) * 0.9, max(vals_z) * 1.1)
        print(f"[TimeGAN Gen{generation}] 坏样本禁区: {bad_zones}")

    for sample_idx in range(num_samples * 3):  # 多生成以便筛选
        if len(samples) >= num_samples:
            break

        # AR(1) 收益率生成（残差随代际收敛）
        returns = np.zeros(SEQ_LEN)
        returns[0] = rng.normal(mean_ret, std_ret * vol_scale * residual_scale * 0.5)
        for t in range(1, SEQ_LEN):
            returns[t] = ar1_coef * returns[t-1] + rng.normal(
                (1 - ar1_coef) * mean_ret, std_ret * vol_scale * residual_scale * 0.5
            )

        # 骨架方向引导（收益率层面，权重随代际递增）
        if skeleton_returns is not None and len(skeleton_returns) == SEQ_LEN - 1:
            ret_full = np.concatenate([[returns[0]], returns[1:]])
            ret_full[1:] = (1 - skeleton_weight) * returns[1:] + skeleton_weight * skeleton_returns

        # 重建价格
        close_prices = first_close * np.cumprod(1 + returns)

        # 坏样本禁区检查
        if bad_zones:
            gen_ret_std = float(np.std(returns) * 100)
            gen_amp = float((close_prices.max() - close_prices.min()) / close_prices.mean() * 100) if close_prices.mean() > 0 else 0
            skip = False
            for zkey, (zlo, zhi) in bad_zones.items():
                if zkey == 'volatility' and zlo <= gen_ret_std <= zhi:
                    skip = True
                    break
                if zkey == 'amplitude' and zlo <= gen_amp <= zhi:
                    skip = True
                    break
            if skip:
                continue  # 落在禁区，重新生成

        # 生成 OHLCV
        records = []
        for i in range(SEQ_LEN):
            c = close_prices[i]
            # open = 前一天收盘价（连续定价，K线颜色跟随涨跌方向）
            if i == 0:
                o = c * (1 + rng.normal(0, 0.003))
            else:
                o = close_prices[i - 1]

            # high/low 用合理的影线
            h = max(o, c) * (1 + abs(rng.normal(0, 0.008)))
            l = min(o, c) * (1 - abs(rng.normal(0, 0.008)))

            rec = {
                'trade_date': f'day_{i}',
                'open': round(float(o), 4),
                'close': round(float(c), 4),
                'high': round(float(h), 4),
                'low': round(float(l), 4),
                'vol': round(abs(rng.normal(1e6, 2e5)), 0)
            }
            records.append(rec)

        # 计算 MA
        c_arr = np.array([r['close'] for r in records])
        for m in ma_list:
            for i in range(len(records)):
                window = c_arr[:i+1]
                if len(window) >= m:
                    records[i][f'MA{m}'] = round(float(np.mean(window[-m:])), 4)
                else:
                    records[i][f'MA{m}'] = round(float(np.mean(window)), 4)

        samples.append(records)

    return samples


# ============================================================
# 6. 主入口：两阶段生成
# ============================================================
_model_cache = {}

def generate_synthetic_data(seeds, skeleton, features, ma_list=MA_LIST, num_samples=8,
                             generation=1, good_samples=None, bad_samples=None):
    """
    两阶段生成入口：
    Phase 1 — 统计引导（始终可用，即时生成）
    Phase 2 — VAE-GAN 微调（如有缓存的模型则使用，否则跳过）
    支持递归生成：generation/good_samples/bad_samples
    """
    # Phase 1: 始终执行
    phase1_samples = statistical_conditional_generation(
        seeds, skeleton, features, ma_list, num_samples,
        generation=generation, good_samples=good_samples, bad_samples=bad_samples
    )

    # Phase 2: 尝试加载或快速训练 VAE-GAN
    try:
        cond_hash = _compute_condition_hash(skeleton, features)
        model = _get_or_create_model(cond_hash)

        if not model.get('trained', False):
            # 用 Phase 1 样本 + 种子快速微调
            _quick_train(model, seeds, phase1_samples, skeleton, features, ma_list, steps=100)

        if model.get('trained', False):
            phase2_samples = _vae_generate(model['model'], seeds, skeleton, features, ma_list, num_samples)
            if phase2_samples and len(phase2_samples) == num_samples:
                return phase2_samples
    except Exception as e:
        print(f"[TimeGAN Phase2] 跳过，使用 Phase1 结果: {e}")

    return phase1_samples


def _compute_condition_hash(skeleton, features):
    """生成条件的短哈希用于模型缓存"""
    key = str(skeleton) + str(features)
    return hashlib.md5(key.encode()).hexdigest()[:8]


def _get_or_create_model(cond_hash):
    """获取或创建模型"""
    global _model_cache

    # 内存缓存
    if cond_hash in _model_cache:
        return _model_cache[cond_hash]

    # 磁盘缓存
    model_path = os.path.join('custom_modes', f'timegan_{cond_hash}.pth')
    model = ConditionalTimeGAN().to(DEVICE)

    loaded = False
    if os.path.exists(model_path):
        try:
            model.load_state_dict(torch.load(model_path, map_location=DEVICE))
            loaded = True
            print(f"[TimeGAN] 加载缓存模型: {model_path}")
        except Exception:
            pass

    entry = {'model': model, 'trained': loaded}
    _model_cache[cond_hash] = entry

    # LRU 逐出
    if len(_model_cache) > 5:
        oldest = next(iter(_model_cache))
        del _model_cache[oldest]

    return entry


def _quick_train(model_entry, seeds, aug_samples, skeleton, features, ma_list, steps=100):
    """快速少样本微调"""
    model = model_entry['model']
    model.train()

    stats = extract_seed_statistics(seeds)
    cond = model.encode_condition(skeleton, features, stats)

    # 构建训练数据：种子 + 增强样本
    all_data = []
    first_close = None
    for seed in [seeds[0]] if seeds else []:  # 用第一个种子
        tensor, fc = encode_sequence(seed, ma_list)
        all_data.append(tensor)
        if first_close is None:
            first_close = fc
    for aug in aug_samples[:4]:
        tensor, fc = encode_sequence(aug, ma_list)
        all_data.append(tensor)

    if not all_data:
        return

    batch = torch.stack(all_data).to(DEVICE)
    cond_batch = cond.expand(batch.size(0), -1)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    for step in range(steps):
        optimizer.zero_grad()

        # Encode
        mu, logvar = model.encoder(batch, cond_batch)
        z = model.reparameterize(mu, logvar)

        # Decode
        recon = model.decoder(z, cond_batch)

        # Losses
        recon_loss = F.mse_loss(recon, batch)
        kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())

        # Supervisor
        h_seq = model.encoder.encode_per_step(batch, cond_batch)
        pred, target = model.supervisor(h_seq)
        sup_loss = F.mse_loss(pred, target)

        # Discriminator
        real_score = model.discriminator(batch, cond_batch)
        fake_score = model.discriminator(recon.detach(), cond_batch)
        gan_loss = -torch.mean(torch.log(real_score.sigmoid() + 1e-8) +
                               torch.log(1 - fake_score.sigmoid() + 1e-8))

        loss = recon_loss + 0.1 * kl_loss + 0.5 * sup_loss + 0.01 * gan_loss
        loss.backward()
        optimizer.step()

    model.eval()
    model_entry['trained'] = True

    # 保存到磁盘
    cond_hash = _compute_condition_hash(skeleton, features)
    model_path = os.path.join('custom_modes', f'timegan_{cond_hash}.pth')
    torch.save(model.state_dict(), model_path)
    print(f"[TimeGAN] 微调完成并保存: {model_path} ({steps} steps)")


def _vae_generate(model, seeds, skeleton, features, ma_list, num_samples):
    """使用 VAE 解码器生成样本"""
    model.eval()
    stats = extract_seed_statistics(seeds)

    with torch.no_grad():
        cond = model.encode_condition(skeleton, features, stats)

        # 获取种子的 mu 作为采样中心
        if seeds:
            seed_tensor, first_close = encode_sequence(seeds[0], ma_list)
            seed_tensor = seed_tensor.unsqueeze(0).to(DEVICE)
            mu, logvar = model.encoder(seed_tensor, cond)
        else:
            mu = torch.zeros(1, LATENT_DIM, device=DEVICE)
            first_close = 10.0

        samples = []
        for i in range(num_samples):
            # 在 mu 周围采样，加入少量噪声
            noise = torch.randn(1, LATENT_DIM, device=DEVICE) * 0.3
            z = mu + noise

            raw = model.generate_from_latent(z, cond)
            raw_np = raw.squeeze(0).cpu().numpy()
            records = decode_to_ohlcv(raw_np, first_close, ma_list)
            samples.append(records)

    return samples
