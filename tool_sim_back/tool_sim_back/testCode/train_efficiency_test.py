"""Training efficiency test: 10/20/30 positive samples x 80 epochs.
Based on retrain_yolo_20260723.py pipeline — measures prep time, per-epoch time,
total training time, GPU peak memory, and validation mAP50."""

import hashlib
import os
import sys
import time

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from few_shot_learning.yolo0623.chart_renderer import RENDERER_VERSION
from few_shot_learning.yolo0623.main import build_dataset_from_contexts, train_yolo
from test_pipeline_common import LABELS_DIR, MA_LIST, PROJECT_DIR, load_stock

CONTEXT_DAYS = 60
NEGATIVE_COUNT = 80
SEED = 42
EPOCHS = 80
IMAGE_SIZE = 416
SAMPLE_SIZES = [10, 20, 30]


def index_for_date(df, value, prefer_end=False):
    target = pd.Timestamp(str(value)[:10])
    matches = df.index[df.trade_date == target].tolist()
    if matches:
        return matches[-1] if prefer_end else matches[0]
    return int((df.trade_date - target).abs().idxmin())


def context_slice(df, start_idx, end_idx):
    target_center = (start_idx + end_idx) // 2
    context_start = max(0, target_center - CONTEXT_DAYS // 2)
    context_start = min(context_start, max(0, len(df) - CONTEXT_DAYS))
    context = df.iloc[context_start:context_start + CONTEXT_DAYS].copy().reset_index(drop=True)
    return context, start_idx - context_start, end_idx - context_start


def load_positive_contexts(labels):
    contexts = []
    pool = labels[labels.label == 1].sample(frac=1, random_state=SEED)
    for _, row in pool.iterrows():
        code = str(row.code).zfill(6)
        df = load_stock(code)
        if df is None or len(df) < CONTEXT_DAYS:
            continue
        low1_idx = index_for_date(df, row.low1_date)
        low2_idx = index_for_date(df, row.low2_date, prefer_end=True)
        bbox_start = max(0, low1_idx - 3)
        bbox_end = min(len(df) - 1, low2_idx + 3)
        context, relative_start, relative_end = context_slice(df, bbox_start, bbox_end)
        if relative_start < 0 or relative_end >= len(context):
            continue
        contexts.append({
            'code': code,
            'source_start_date': str(row.low1_date)[:10],
            'source_end_date': str(row.low2_date)[:10],
            'df': context,
            'start_idx': relative_start,
            'end_idx': relative_end,
        })
    return contexts


def load_negative_contexts(all_labels, excluded_codes):
    rng = np.random.default_rng(SEED)
    codes = [str(c).zfill(6) for c in all_labels.code.unique()
             if str(c).zfill(6) not in excluded_codes]
    rng.shuffle(codes)
    contexts = []
    for code in codes:
        df = load_stock(code)
        if df is None or len(df) < CONTEXT_DAYS:
            continue
        positives = all_labels[(all_labels.label == 1) & (all_labels.code.astype(str).str.zfill(6) == code)]
        forbidden = []
        for _, row in positives.iterrows():
            try:
                forbidden.append((
                    pd.Timestamp(str(row.low1_date)[:10]) - pd.Timedelta(days=15),
                    pd.Timestamp(str(row.low2_date)[:10]) + pd.Timedelta(days=15),
                ))
            except (TypeError, ValueError):
                continue
        starts = rng.permutation(len(df) - CONTEXT_DAYS + 1)
        for start in starts:
            context = df.iloc[start:start + CONTEXT_DAYS].copy().reset_index(drop=True)
            c_start, c_end = context.iloc[0].trade_date, context.iloc[-1].trade_date
            if any(c_start <= end and c_end >= begin for begin, end in forbidden):
                continue
            contexts.append(context)
            break
        if len(contexts) == NEGATIVE_COUNT:
            return contexts
    return contexts


def read_mAP50():
    results_csv = os.path.join(PROJECT_DIR, 'runs', 'detect', 'train', 'results.csv')
    try:
        res = pd.read_csv(results_csv)
        col = 'metrics/mAP50(B)'
        if col in res.columns:
            series = res[col].dropna()
            if len(series) > 0:
                return float(series.iloc[-1]) * 100
    except Exception:
        pass
    return 0.0


def run_one(n_samples, all_labels):
    print(f'\n{"=" * 60}')
    print(f'>>> n={n_samples}  positive samples, {EPOCHS} epochs')
    print(f'{"=" * 60}')

    # Sample n positives
    pos_pool = all_labels[all_labels.label == 1].sample(n=n_samples, random_state=SEED)
    subset = pd.concat([pos_pool, all_labels[all_labels.label == 0]], ignore_index=True)

    # --- Data preparation ---
    t0 = time.perf_counter()
    positives = load_positive_contexts(subset)
    excluded = {item['code'] for item in positives}
    negatives = load_negative_contexts(all_labels, excluded)
    prep_time = time.perf_counter() - t0

    if len(positives) < 3:
        print(f'  SKIP: only {len(positives)} valid positive contexts')
        return None

    # --- Build dataset ---
    safe = hashlib.md5(f'eff{n_samples}e{EPOCHS}'.encode()).hexdigest()[:8]
    mode_name = f'yolo_eff_{safe}'
    dataset_dir = os.path.join(PROJECT_DIR, 'custom_modes', f'{mode_name}_dataset')
    yaml_path, aug_pos, neg_count = build_dataset_from_contexts(positives, negatives, dataset_dir)
    print(f'  Positives: {len(positives)} raw -> {aug_pos} augmented, Negatives: {neg_count}')

    # --- Train ---
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    t_train = time.perf_counter()
    train_yolo(yaml_path, mode_name, epochs=EPOCHS, imgsz=IMAGE_SIZE)
    train_time = time.perf_counter() - t_train
    gpu_mem = torch.cuda.max_memory_allocated() / 1024 ** 3 if torch.cuda.is_available() else 0

    mAP50 = read_mAP50()
    per_epoch = train_time / EPOCHS

    result = {
        '正样本数': n_samples,
        '增强后正样本': aug_pos,
        '负样本数': neg_count,
        '数据准备耗时(s)': round(prep_time, 1),
        '总训练耗时(s)': round(train_time, 1),
        '单Epoch耗时(s)': round(per_epoch, 1),
        'GPU峰值显存(GB)': round(gpu_mem, 3),
        '验证mAP50(%)': round(mAP50, 2),
    }
    print(f'  Prep: {prep_time:.1f}s  Train: {train_time:.1f}s ({per_epoch:.1f}s/epoch)  GPU: {gpu_mem:.3f}GB  mAP50: {mAP50:.2f}%')
    return result


def main():
    labels_path = os.path.join(LABELS_DIR, 'all_labeled.csv')
    all_labels = pd.read_csv(labels_path)
    total_pos = len(all_labels[all_labels.label == 1])
    print(f'Labels: {len(all_labels)} (pos={total_pos}, neg={len(all_labels[all_labels.label == 0])})')
    print(f'Config: CONTEXT_DAYS={CONTEXT_DAYS}, NEGATIVES={NEGATIVE_COUNT}, EPOCHS={EPOCHS}, IMGSZ={IMAGE_SIZE}, batch=16, amp=True')
    print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"}')

    results = [run_one(n, all_labels) for n in SAMPLE_SIZES]
    results = [r for r in results if r is not None]

    print(f'\n{"=" * 80}')
    print('Training Efficiency Results (80 Epochs)')
    print(f'{"=" * 80}')
    df = pd.DataFrame(results)
    print(df.to_string(index=False))

    out_path = os.path.join(os.path.dirname(PROJECT_DIR), 'test_output', 'train_efficiency.csv')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f'\nSaved: {out_path}')


if __name__ == '__main__':
    main()
