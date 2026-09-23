"""
YOLO 形态检测训练管线 (yolo0623)
- 弱监督标注：用 Prototypical Network 自动标注训练数据
- YOLOv8-nano 微调：单类检测（目标形态）
- 每只股票一张大图 → 一次前向传播检测所有形态位置
"""
import os
import sys
import numpy as np
import pandas as pd
import torch

# 确保能导入项目根目录的模块
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from utils import get_stock_data, calculate_ma
from deal_sim_time_range import resample_ohlcv
from few_shot_utils import get_ai_engine
from few_shot_learning.yolo0623.chart_renderer import render_kline_image, render_ma_image

IMAGE_SIZE = 416
DAYS_PER_IMAGE = 150
INFERENCE_DAYS_PER_IMAGE = 60
INFERENCE_OVERLAP_DAYS = 30
WINDOW_SIZE = 20
DATA_FOLDER = os.getenv('DATA_FOLDER', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'kline-data'))


def generate_training_chart(df, ma_list=None, img_size=IMAGE_SIZE, analysis_mode='KLINE'):
    """按分析模式生成 img_size×img_size 白底无坐标轴图（K线蜡烛图 / MA 均线图）"""
    if str(analysis_mode).upper() == 'MA':
        return render_ma_image(df, img_size)
    return render_kline_image(df, img_size)


def auto_label_stock(df, ma_list, ai_engine, target_idx, mode_index, threshold=0.4):
    """弱监督标注：用 Prototypical Network 扫描找高分区域"""
    hits = []
    for i in range(0, len(df) - WINDOW_SIZE + 1, 5):
        window = df.iloc[i: i + WINDOW_SIZE]
        try:
            score = ai_engine.get_score(window, ma_list, target_idx, mode_index)
        except Exception:
            score = 0.0
        if score >= threshold:
            hits.append((i, i + WINDOW_SIZE - 1, score))
    if not hits:
        return []
    hits.sort(key=lambda x: x[0])
    merged = [hits[0]]
    for s, e, sc in hits[1:]:
        ps, pe, psc = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(e, pe), max(sc, psc))
        else:
            merged.append((s, e, sc))
    return merged


def region_to_yolo_bbox(start, end, df, img_w, img_h):
    """DataFrame 索引区间 → YOLO 归一化 bbox"""
    n = len(df)
    x1, x2 = start / n, (end + 1) / n
    region = df.iloc[start: end + 1]
    vals = []
    for col in region.columns:
        if col.startswith('MA') or col == 'close':
            v = region[col].dropna().values
            if len(v) > 0:
                vals.extend(v.tolist())
    if not vals:
        return None
    y_min, y_max = min(vals), max(vals)
    full_min = df['close'].min()
    full_max = df['close'].max()
    pr = full_max - full_min if full_max > full_min else 1.0
    y1 = max(0, min(1, 1.0 - (y_max - full_min) / pr))
    y2 = max(0, min(1, 1.0 - (y_min - full_min) / pr))
    h = max(y2 - y1, 0.15)
    return ((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, h)


def build_dataset(mode_index, stock_pool, ma_list, output_dir, threshold=0.4):
    """构建完整 YOLO 训练数据集"""
    ai_engine = get_ai_engine()
    AI_CLASS_MAP = {"BA": 1, "BeA": 0}
    target_idx = AI_CLASS_MAP.get(mode_index)

    img_dir = os.path.join(output_dir, 'images')
    lbl_dir = os.path.join(output_dir, 'labels')
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)

    pos_count, neg_count = 0, 0
    for idx, code in enumerate(stock_pool):
        ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
        print(f"  [标注 {idx+1}/{len(stock_pool)}] {ts_code}", end='\r')
        try:
            df = get_stock_data(ts_code, None, None, data_folder=DATA_FOLDER)
            if df is None or df.empty or len(df) < 30:
                continue
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date').reset_index(drop=True)
            df = calculate_ma(df, ma_list)
            if df.empty:
                continue
        except Exception:
            continue

        regions = auto_label_stock(df, ma_list, ai_engine, target_idx, mode_index, threshold)
        for chunk_start in range(0, len(df), DAYS_PER_IMAGE):
            chunk_end = min(chunk_start + DAYS_PER_IMAGE, len(df))
            chunk = df.iloc[chunk_start: chunk_end].reset_index(drop=True)
            if len(chunk) < 30:
                continue
            chunk_regions = []
            for rs, re_, sc in regions:
                ls, le = rs - chunk_start, re_ - chunk_start
                if le < 0 or ls >= len(chunk):
                    continue
                ls, le = max(0, ls), min(len(chunk) - 1, le)
                chunk_regions.append((ls, le))
            img = generate_training_chart(chunk, ma_list)
            name = f"{code}_{chunk_start}_{chunk_end}"
            if chunk_regions:
                img.save(os.path.join(img_dir, f"{name}.png"))
                with open(os.path.join(lbl_dir, f"{name}.txt"), 'w') as f:
                    for rs, re_ in chunk_regions:
                        bbox = region_to_yolo_bbox(rs, re_, chunk, IMAGE_SIZE, IMAGE_SIZE)
                        if bbox:
                            f.write(f"0 {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")
                pos_count += 1
                # 数据增强：水平翻转
                img_flip = img.transpose(Image.FLIP_LEFT_RIGHT)
                img_flip.save(os.path.join(img_dir, f"{name}_flip.png"))
                with open(os.path.join(lbl_dir, f"{name}_flip.txt"), 'w') as f:
                    for rs, re_ in chunk_regions:
                        bbox = region_to_yolo_bbox(rs, re_, chunk, IMAGE_SIZE, IMAGE_SIZE)
                        if bbox:
                            f.write(f"0 {1.0-bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")
                pos_count += 1
            elif neg_count < pos_count * 3:
                img.save(os.path.join(img_dir, f"neg_{name}.png"))
                open(os.path.join(lbl_dir, f"neg_{name}.txt"), 'w').close()
                neg_count += 1

    print(f"\n  数据集完成: 正样本 {pos_count}, 负样本 {neg_count}")
    yaml_path = os.path.join(output_dir, 'dataset.yaml')
    with open(yaml_path, 'w') as f:
        f.write(f"path: {os.path.abspath(output_dir)}\ntrain: images\nval: images\nnames:\n  0: target_pattern\n")
    return yaml_path, pos_count, neg_count


def build_dataset_from_samples(segments, negative_segments, ma_list, output_dir, analysis_mode='KLINE'):
    """
    直接用用户提供的正负样本构建 YOLO 数据集（含数据增强）
    每个正样本 → 嵌入150天上下文大图 + 标注bbox + 5种增强变体
    """
    import io
    from PIL import Image, ImageEnhance

    img_dir = os.path.join(output_dir, 'images')
    lbl_dir = os.path.join(output_dir, 'labels')
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)

    pos_count = 0
    neg_count = 0

    def make_chart_with_bbox(df_segment, save_prefix, label_bbox=True):
        """生成大图+bbox标注，含数据增强"""
        nonlocal pos_count, neg_count
        n = len(df_segment)

        # 原始大图
        img = generate_training_chart(df_segment, ma_list, IMAGE_SIZE, analysis_mode)
        if label_bbox:
            # 样本在中间20天位置 → 计算bbox
            seg_len = min(20, n)
            seg_start = max(0, (n - seg_len) // 2)
            x_center = (seg_start + seg_len / 2) / n
            w = seg_len / n
            # y范围用价格范围
            vals = []
            for col in df_segment.columns:
                if col.startswith('MA') or col == 'close':
                    v = df_segment.iloc[seg_start:seg_start+seg_len][col].dropna().values
                    if len(v) > 0:
                        vals.extend(v.tolist())
            if not vals:
                return
            y_min, y_max = min(vals), max(vals)
            full_min = df_segment['close'].min()
            full_max = df_segment['close'].max()
            pr = full_max - full_min if full_max > full_min else 1.0
            y1 = max(0, min(1, 1.0 - (y_max - full_min) / pr))
            y2 = max(0, min(1, 1.0 - (y_min - full_min) / pr))
            h = max(y2 - y1, 0.15)
            y_center = (y1 + y2) / 2

        # 保存原始
        img.save(os.path.join(img_dir, f"{save_prefix}.png"))
        if label_bbox:
            with open(os.path.join(lbl_dir, f"{save_prefix}.txt"), 'w') as f:
                f.write(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
            pos_count += 1
        else:
            open(os.path.join(lbl_dir, f"{save_prefix}.txt"), 'w').close()
            neg_count += 1

        if not label_bbox:
            return

        # 数据增强：5个变体
        # 1. 水平翻转
        img_flip = img.transpose(Image.FLIP_LEFT_RIGHT)
        img_flip.save(os.path.join(img_dir, f"{save_prefix}_flip.png"))
        with open(os.path.join(lbl_dir, f"{save_prefix}_flip.txt"), 'w') as f:
            f.write(f"0 {1.0-x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
        pos_count += 1

        # 2-3. 亮度变化
        for bi, factor in enumerate([0.8, 1.2]):
            enh = ImageEnhance.Brightness(img)
            img_b = enh.enhance(factor)
            img_b.save(os.path.join(img_dir, f"{save_prefix}_b{bi}.png"))
            with open(os.path.join(lbl_dir, f"{save_prefix}_b{bi}.txt"), 'w') as f:
                f.write(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
            pos_count += 1

        # 4. 对比度变化
        enh = ImageEnhance.Contrast(img)
        img_c = enh.enhance(1.3)
        img_c.save(os.path.join(img_dir, f"{save_prefix}_c.png"))
        with open(os.path.join(lbl_dir, f"{save_prefix}_c.txt"), 'w') as f:
            f.write(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
        pos_count += 1

    def _stretch_segment(df_orig, scale):
        """时间拉伸/压缩：插值OHLC到 scale × 原长度"""
        n_orig = len(df_orig)
        n_new = max(5, int(n_orig * scale))
        indices = np.linspace(0, n_orig - 1, n_new)
        stretched = pd.DataFrame()
        for col in df_orig.columns:
            if col in ('open', 'close', 'high', 'low') or str(col).startswith('MA'):
                vals = pd.to_numeric(df_orig[col], errors='coerce').fillna(method='ffill').fillna(method='bfill').values
                stretched[col] = np.interp(indices, np.arange(n_orig), vals)
            elif col == 'trade_date':
                stretched[col] = [f'day_{j}' for j in range(n_new)]
            else:
                stretched[col] = df_orig[col].iloc[0]
        return stretched

    # 正样本
    for i, seg in enumerate(segments):
        try:
            df = pd.DataFrame(seg)
            if len(df) < 5:
                continue
            # 原始 + 5种增强
            make_chart_with_bbox(df, f"pos_{i}", label_bbox=True)
            # 时间尺度增强：拉伸/压缩，让YOLO学会检测不同长度的形态
            for scale in [0.8, 1.2, 1.4]:
                df_stretched = _stretch_segment(df, scale)
                make_chart_with_bbox(df_stretched, f"pos_{i}_s{scale}", label_bbox=True)
        except Exception as e:
            print(f"  正样本{i}处理失败: {e}")

    # 负样本
    for i, seg in enumerate(negative_segments):
        try:
            df = pd.DataFrame(seg)
            if len(df) < 5:
                continue
            make_chart_with_bbox(df, f"neg_{i}", label_bbox=False)
        except Exception as e:
            print(f"  负样本{i}处理失败: {e}")

    print(f"  数据集构建: 正样本(含增强) {pos_count} 张, 负样本 {neg_count} 张")

    yaml_path = os.path.join(output_dir, 'dataset.yaml')
    with open(yaml_path, 'w') as f:
        f.write(f"path: {os.path.abspath(output_dir)}\ntrain: images\nval: images\nnames:\n  0: target_pattern\n")
    return yaml_path, pos_count, neg_count


def build_dataset_from_contexts(positive_contexts, negative_contexts, output_dir):
    """Build a YOLO dataset from chart contexts with explicit target indexes."""
    from PIL import Image, ImageEnhance

    img_dir = os.path.join(output_dir, 'images')
    lbl_dir = os.path.join(output_dir, 'labels')
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)
    positive_count = negative_count = 0

    def save_positive(context, name):
        nonlocal positive_count
        df = context['df'].reset_index(drop=True)
        start, end = context['start_idx'], context['end_idx']
        bbox = region_to_yolo_bbox(start, end, df, IMAGE_SIZE, IMAGE_SIZE)
        if bbox is None:
            return False
        image = generate_training_chart(df, img_size=IMAGE_SIZE)

        def write_label(label_name, label_bbox):
            with open(os.path.join(lbl_dir, f'{label_name}.txt'), 'w') as label_file:
                label_file.write(f'0 {label_bbox[0]:.6f} {label_bbox[1]:.6f} {label_bbox[2]:.6f} {label_bbox[3]:.6f}\n')

        image.save(os.path.join(img_dir, f'{name}.png'))
        write_label(name, bbox)
        positive_count += 1

        flipped = image.transpose(Image.FLIP_LEFT_RIGHT)
        flipped.save(os.path.join(img_dir, f'{name}_flip.png'))
        write_label(f'{name}_flip', (1 - bbox[0], bbox[1], bbox[2], bbox[3]))
        positive_count += 1

        for suffix, transformed in (
            ('_b0', ImageEnhance.Brightness(image).enhance(0.8)),
            ('_b1', ImageEnhance.Brightness(image).enhance(1.2)),
            ('_c', ImageEnhance.Contrast(image).enhance(1.3)),
        ):
            transformed.save(os.path.join(img_dir, f'{name}{suffix}.png'))
            write_label(f'{name}{suffix}', bbox)
            positive_count += 1
        return True

    for index, context in enumerate(positive_contexts):
        save_positive(context, f'pos_{index:03d}')

    for index, context in enumerate(negative_contexts):
        df = context.reset_index(drop=True)
        image = generate_training_chart(df, img_size=IMAGE_SIZE)
        name = f'neg_{index:03d}'
        image.save(os.path.join(img_dir, f'{name}.png'))
        open(os.path.join(lbl_dir, f'{name}.txt'), 'w').close()
        negative_count += 1

    yaml_path = os.path.join(output_dir, 'dataset.yaml')
    with open(yaml_path, 'w') as yaml_file:
        yaml_file.write(f'path: {os.path.abspath(output_dir)}\ntrain: images\nval: images\nnames:\n  0: target_pattern\n')
    return yaml_path, positive_count, negative_count


def train_yolo(dataset_yaml, mode_index, epochs=80, imgsz=416):
    """训练 YOLOv8-nano"""
    from ultralytics import YOLO
    import shutil
    import re

    print(f"[YOLO训练] epochs={epochs}, imgsz={imgsz}")
    model = YOLO('yolov8n.pt')
    use_cuda = torch.cuda.is_available()

    # 每次训练使用与 mode_index 绑定的专属独立目录，避免共享 'train' 目录导致文件锁冲突
    safe_mode = re.sub(r'[\\/:*?"<>|]', '_', str(mode_index))
    train_project = os.path.join(PROJECT_ROOT, 'runs', 'detect')
    train_name = f"train_{safe_mode}"
    train_dir = os.path.join(train_project, train_name)

    # 清理同名旧文件夹，避免 Windows 同名文件句柄占用/覆盖锁冲突
    if os.path.exists(train_dir):
        shutil.rmtree(train_dir, ignore_errors=True)
        print(f"[YOLO训练] 已清理旧训练目录: {train_dir}")

    model.train(
        data=dataset_yaml, epochs=epochs, imgsz=imgsz,
        batch=16 if use_cuda else 16,
        device='cuda' if use_cuda else 'cpu',
        workers=0,
        amp=True,
        verbose=True, exist_ok=True,
        project=train_project,
        name=train_name,
    )
    save_path = os.path.join(PROJECT_ROOT, 'custom_modes', f'{mode_index}_yolo.pt')
    best = os.path.join(train_dir, 'weights', 'best.pt')
    if os.path.exists(best):
        shutil.copy2(best, save_path)
    print(f"[YOLO训练] 模型保存至: {save_path}")
    return save_path


# ======================== YOLO 推理检测 ========================

_yolo_models = {}


def load_yolo_model(mode_index):
    """加载并缓存 YOLO 模型"""
    if mode_index not in _yolo_models:
        from ultralytics import YOLO
        model_path = os.path.join(PROJECT_ROOT, 'custom_modes', f'{mode_index}_yolo.pt')
        if not os.path.exists(model_path):
            return None
        _yolo_models[mode_index] = YOLO(model_path)
    return _yolo_models[mode_index]


def _window_starts(length, days_per_image):
    overlap = min(INFERENCE_OVERLAP_DAYS, max(days_per_image - 1, 0))
    step = max(days_per_image - overlap, 1)
    starts = list(range(0, max(length - 29, 1), step))
    last_start = max(length - days_per_image, 0)
    if last_start not in starts:
        starts.append(last_start)
    return sorted(set(starts))


def iter_yolo_windows(stock_frames, ma_list, img_size=IMAGE_SIZE,
                      days_per_image=INFERENCE_DAYS_PER_IMAGE, analysis_mode='KLINE'):
    """Yield rendered YOLO windows with their stock-local metadata."""
    for stock_code, source_df in stock_frames.items():
        df = source_df.copy().reset_index(drop=True)
        if len(df) < 30:
            continue
        for chunk_start in _window_starts(len(df), days_per_image):
            chunk_end = min(chunk_start + days_per_image, len(df))
            chunk_df = df.iloc[chunk_start:chunk_end].reset_index(drop=True)
            if len(chunk_df) < 30:
                continue
            yield {
                'stock_code': str(stock_code),
                'df': df,
                'chunk_start': chunk_start,
                'length': len(chunk_df),
                'image': generate_training_chart(chunk_df, ma_list, img_size, analysis_mode),
            }


def _run_yolo_batch(model, windows, conf_threshold, batch_size):
    """Run one batch, reducing its size only when CUDA memory is exhausted."""
    pending = list(windows)
    predictions = []
    current_batch_size = min(batch_size, len(pending))
    while pending:
        batch = pending[:current_batch_size]
        try:
            batch_predictions = model(
                [item['image'] for item in batch], conf=conf_threshold, verbose=False,
            )
            predictions.extend(zip(batch, batch_predictions))
            pending = pending[current_batch_size:]
        except RuntimeError as exc:
            if 'out of memory' not in str(exc).lower() or current_batch_size == 1:
                raise
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            current_batch_size = max(1, current_batch_size // 2)
    return predictions


def _dedupe_detections(detections):
    detections.sort(key=lambda item: item['confidence'], reverse=True)
    kept = []
    for detection in detections:
        if not any(
            abs(detection['start_idx'] - existing['start_idx']) < 10
            and abs(detection['end_idx'] - existing['end_idx']) < 10
            for existing in kept
        ):
            kept.append(detection)
    return kept


def detect_pattern_yolo_batch(stock_frames, ma_list, mode_index, img_size=IMAGE_SIZE,
                              conf_threshold=0.3,
                              days_per_image=INFERENCE_DAYS_PER_IMAGE,
                              batch_size=4, analysis_mode='KLINE'):
    """Detect patterns from mixed-stock batches and return detections by stock code."""
    model = load_yolo_model(mode_index)
    results = {str(stock_code): [] for stock_code in stock_frames}
    if model is None:
        return results

    batch_size = max(1, int(batch_size))
    batch = []
    for window in iter_yolo_windows(stock_frames, ma_list, img_size, days_per_image, analysis_mode):
        batch.append(window)
        if len(batch) < batch_size:
            continue
        _collect_yolo_predictions(results, _run_yolo_batch(model, batch, conf_threshold, batch_size), img_size)
        batch = []
    if batch:
        _collect_yolo_predictions(results, _run_yolo_batch(model, batch, conf_threshold, batch_size), img_size)

    return {stock_code: _dedupe_detections(detections) for stock_code, detections in results.items()}


def _collect_yolo_predictions(results, predictions, img_size):
    for window, prediction in predictions:
        if prediction.boxes is None:
            continue
        df = window['df']
        chunk_start = window['chunk_start']
        length = window['length']
        for box in prediction.boxes:
            xyxy = box.xyxy[0].cpu().numpy()
            idx_start = max(0, min(int(xyxy[0] / img_size * length), length - 1))
            idx_end = max(idx_start + 5, min(int(xyxy[2] / img_size * length), length - 1))
            global_start = chunk_start + idx_start
            global_end = min(chunk_start + idx_end, len(df) - 1)
            if global_start > global_end:
                continue
            segment = df.iloc[global_start:global_end + 1]
            if segment.empty:
                continue
            results[window['stock_code']].append({
                'start_date': str(segment.iloc[0]['trade_date'])[:10],
                'end_date': str(segment.iloc[-1]['trade_date'])[:10],
                'confidence': round(float(box.conf[0].cpu()), 4),
                'start_idx': global_start,
                'end_idx': global_end,
                'segment_df': segment.copy(),
            })


def detect_pattern_yolo(df, ma_list, mode_index, img_size=IMAGE_SIZE,
                        conf_threshold=0.3, days_per_image=INFERENCE_DAYS_PER_IMAGE,
                        batch_size=4, prefetch_batches=2, analysis_mode='KLINE'):
    """Compatibility wrapper for callers that detect a single stock."""
    del prefetch_batches
    return detect_pattern_yolo_batch(
        {'single_stock': df}, ma_list, mode_index, img_size, conf_threshold,
        days_per_image, batch_size, analysis_mode,
    )['single_stock']
