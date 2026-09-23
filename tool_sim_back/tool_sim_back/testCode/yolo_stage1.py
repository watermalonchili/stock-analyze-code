"""Stage 1: globally batched YOLO W-bottom scan."""
import argparse
import hashlib
import json
import os
import sys
import time

import torch
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from few_shot_learning.yolo0623.chart_renderer import RENDERER_VERSION
from few_shot_learning.yolo0623.main import (
    INFERENCE_DAYS_PER_IMAGE,
    INFERENCE_OVERLAP_DAYS,
    detect_pattern_yolo_batch,
)
from test_pipeline_common import (
    MA_LIST,
    OUTPUT_DIR,
    PROJECT_DIR,
    load_evaluation_labels,
    load_stock_cache,
    metric_row,
    write_csv,
)

MODE_NAME = 'wbtest_kline'
SCAN_CONFIDENCE = 0.10
SCAN_IMAGE_SIZE = 416
BATCH_SIZE = 4
SCAN_DAYS_PER_IMAGE = 60


def model_metadata(model_path):
    with open(model_path, 'rb') as model_file:
        digest = hashlib.sha256(model_file.read()).hexdigest()
    return {'path': model_path, 'sha256': digest}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default=MODE_NAME)
    parser.add_argument('--from-cache', action='store_true', help='从已有缓存重新评估，跳过YOLO扫描')
    args = parser.parse_args()
    mode_name = args.mode
    model_path = os.path.join(PROJECT_DIR, 'custom_modes', f'{mode_name}_yolo.pt')
    if not os.path.exists(model_path):
        raise FileNotFoundError(f'未找到YOLO模型: {model_path}')

    stock_cache = load_stock_cache()
    labels = load_evaluation_labels(stock_cache)
    print(f'有效股票: {len(stock_cache)}，评估标注: {len(labels)}')

    if args.from_cache:
        cache_path = os.path.join(OUTPUT_DIR, 'yolo_detections.json')
        if not os.path.exists(cache_path):
            raise FileNotFoundError(f'缓存不存在: {cache_path}')
        with open(cache_path, encoding='utf-8') as cache_file:
            cache = json.load(cache_file)
        detections = cache['detections']
        elapsed = cache['elapsed_seconds']
        print(f'从缓存加载: {sum(map(len, detections.values()))} 个候选')
    else:
        torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
        started = time.perf_counter()
        detections = detect_pattern_yolo_batch(
            stock_cache, MA_LIST, mode_name, img_size=SCAN_IMAGE_SIZE,
            conf_threshold=SCAN_CONFIDENCE, batch_size=BATCH_SIZE,
            days_per_image=SCAN_DAYS_PER_IMAGE,
        )
        elapsed = time.perf_counter() - started
    candidate_count = sum(map(len, detections.values()))
    results = [
        metric_row(labels, detections, threshold, 'confidence', '置信度阈值', elapsed, len(stock_cache))
        for threshold in (0.10, 0.15, 0.20, 0.30, 0.40)
    ]
    write_csv(pd.DataFrame(results), 'yolo_test.csv')

    manifest = {
        'model': model_metadata(model_path),
        'renderer_version': RENDERER_VERSION,
        'image_size': SCAN_IMAGE_SIZE,
        'days_per_image': SCAN_DAYS_PER_IMAGE,
        'overlap_days': INFERENCE_OVERLAP_DAYS,
        'step_days': INFERENCE_DAYS_PER_IMAGE - INFERENCE_OVERLAP_DAYS,
        'scan_confidence': SCAN_CONFIDENCE,
        'batch_size': BATCH_SIZE,
        'stock_count': len(stock_cache),
        'candidate_count': candidate_count,
        'elapsed_seconds': round(elapsed, 3),
        'gpu_peak_memory_gb': round(torch.cuda.max_memory_allocated() / 1024 ** 3, 3) if torch.cuda.is_available() else 0,
        'detections': detections,
    }
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cache_path = os.path.join(OUTPUT_DIR, 'yolo_detections.json')
    with open(cache_path, 'w', encoding='utf-8') as cache_file:
        json.dump(manifest, cache_file, ensure_ascii=False, indent=2)
    print(f'YOLO扫描完成: {candidate_count} 个候选，{elapsed:.1f}s，缓存: {cache_path}')


if __name__ == '__main__':
    main()
