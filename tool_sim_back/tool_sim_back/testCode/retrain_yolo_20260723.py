"""Train a Pillow-rendered YOLO W-bottom model — v2: 60d context, all 400+ labeled samples."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from few_shot_learning.yolo0623.chart_renderer import RENDERER_VERSION
from few_shot_learning.yolo0623.main import build_dataset_from_contexts, train_yolo
from test_pipeline_common import LABELS_DIR, MA_LIST, PROJECT_DIR, load_stock

MODE_NAME = 'wbtest_kline_v2'
NEGATIVE_COUNT = 80
CONTEXT_DAYS = 60
SEED = 42
EPOCHS = 30
IMAGE_SIZE = 416


def index_for_date(df, value, prefer_end=False):
    target = pd.Timestamp(str(value)[:10])
    matches = df.index[df.trade_date == target].tolist()
    if matches:
        return matches[-1] if prefer_end else matches[0]
    distances = (df.trade_date - target).abs()
    return int(distances.idxmin())


def context_slice(df, start_idx, end_idx):
    target_center = (start_idx + end_idx) // 2
    context_start = max(0, target_center - CONTEXT_DAYS // 2)
    context_start = min(context_start, max(0, len(df) - CONTEXT_DAYS))
    context = df.iloc[context_start:context_start + CONTEXT_DAYS].copy().reset_index(drop=True)
    return context, start_idx - context_start, end_idx - context_start


def load_positive_contexts(labels):
    """从 all_labeled.csv 加载全部正样本，使用 low1_date~low2_date 作为 W 底 bbox"""
    contexts = []
    pool = labels[labels.label == 1].sample(frac=1, random_state=SEED)
    for _, row in pool.iterrows():
        code = str(row.code).zfill(6)
        df = load_stock(code)
        if df is None or len(df) < CONTEXT_DAYS:
            print(f'  跳过 {code}: 数据不足({len(df) if df is not None else 0}行)')
            continue
        low1_idx = index_for_date(df, row.low1_date)
        low2_idx = index_for_date(df, row.low2_date, prefer_end=True)
        # 以 low1-low2 为 bbox，前后各扩展一点确保完整覆盖
        bbox_start = max(0, low1_idx - 3)
        bbox_end = min(len(df) - 1, low2_idx + 3)
        context, relative_start, relative_end = context_slice(df, bbox_start, bbox_end)
        if relative_start < 0 or relative_end >= len(context):
            print(f'  跳过 {code}: 窗口不完整(low1={row.low1_date} low2={row.low2_date})')
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
    codes = [str(c).zfill(6) for c in all_labels.code.unique() if str(c).zfill(6) not in excluded_codes]
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
    print(f'警告: 仅生成 {len(contexts)} 个负样本 (预期 {NEGATIVE_COUNT})')
    return contexts


def main():
    labels_path = os.path.join(LABELS_DIR, 'all_labeled.csv')
    labels = pd.read_csv(labels_path)
    print(f'标注数据: {len(labels)} 条 (正{len(labels[labels.label==1])} 负{len(labels[labels.label==0])})')

    positives = load_positive_contexts(labels)
    negatives = load_negative_contexts(labels, {item['code'] for item in positives})
    if len(positives) < 10:
        raise RuntimeError(f'正样本不足: {len(positives)}')
    if len(negatives) < 2:
        raise RuntimeError(f'负样本不足: {len(negatives)}')
    print(f'正样本: {len(positives)}, 负样本: {len(negatives)}')

    dataset_dir = os.path.join(PROJECT_DIR, 'custom_modes', f'{MODE_NAME}_dataset')
    yaml_path, augmented_positive_count, negative_count = build_dataset_from_contexts(positives, negatives, dataset_dir)
    manifest = {
        'mode_name': MODE_NAME,
        'renderer_version': RENDERER_VERSION,
        'context_days': CONTEXT_DAYS,
        'seed': SEED,
        'positive_source_count': len(positives),
        'negative_source_count': len(negatives),
        'augmented_positive_count': augmented_positive_count,
        'written_negative_count': negative_count,
        'positive_samples': [{
            'code': item['code'],
            'start_date': item['source_start_date'],
            'end_date': item['source_end_date'],
            'context_target_indexes': [item['start_idx'], item['end_idx']],
        } for item in positives],
    }
    with open(os.path.join(dataset_dir, 'training_manifest.json'), 'w', encoding='utf-8') as output:
        json.dump(manifest, output, ensure_ascii=False, indent=2)
    print(f'数据集完成: 原始正样本{len(positives)}，原始负样本{len(negatives)}，增强正样本{augmented_positive_count}')
    model_path = train_yolo(yaml_path, MODE_NAME, epochs=EPOCHS, imgsz=IMAGE_SIZE)
    print(f'训练完成: {model_path}')


if __name__ == '__main__':
    main()
