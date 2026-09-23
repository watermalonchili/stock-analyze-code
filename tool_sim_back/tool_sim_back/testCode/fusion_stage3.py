"""Stage 3: DTW fine ranking of cached YOLO candidates only, with DTW grid search."""
import json
import os
import time

import pandas as pd

from test_pipeline_common import (
    MA_LIST,
    OUTPUT_DIR,
    WINDOW_SIZE,
    check_hit_overlap,
    get_w_bottom_target,
    load_evaluation_labels,
    load_stock_cache,
    multi_ma_dtw_similarity,
    write_csv,
)

YOLO_CONFIDENCE = 0.10
DTW_THRESHOLDS = [0.38]
EXPECTED_WINDOW_DAYS = 60
EXPECTED_OVERLAP_DAYS = 30
PADDING_DAYS = 5


def pad_detections(detections, days):
    padded = []
    for d in detections:
        try:
            p = {**d}
            p['start_date'] = str(pd.Timestamp(str(d['start_date'])[:10]) - pd.Timedelta(days=days))[:10]
            p['end_date'] = str(pd.Timestamp(str(d['end_date'])[:10]) + pd.Timedelta(days=days))[:10]
            padded.append(p)
        except (KeyError, TypeError, ValueError):
            padded.append(d)
    return padded


def run_fusion(dtw_threshold):
    cache_path = os.path.join(OUTPUT_DIR, 'yolo_detections.json')
    with open(cache_path, encoding='utf-8') as cache_file:
        cache = json.load(cache_file)
    if cache.get('days_per_image') != EXPECTED_WINDOW_DAYS or cache.get('overlap_days') != EXPECTED_OVERLAP_DAYS:
        raise ValueError('YOLO缓存窗口配置不匹配')
    if not cache.get('model', {}).get('sha256'):
        raise ValueError('YOLO缓存缺少模型标识')

    stock_cache = load_stock_cache()
    labels = load_evaluation_labels(stock_cache)
    target = get_w_bottom_target()
    yolo_detections = cache['detections']
    fine_detections = {}
    detail_rows = []
    yolo_candidates = dtw_attempts = 0
    started = time.perf_counter()

    for code, detections in yolo_detections.items():
        df = stock_cache.get(str(code).zfill(6))
        ranked = []
        if df is not None:
            for detection in detections:
                if detection.get('confidence', 0) < YOLO_CONFIDENCE:
                    continue
                yolo_candidates += 1
                start = int(detection.get('start_idx', 0))
                window = df.iloc[start:start + WINDOW_SIZE]
                if len(window) < 10:
                    continue
                dtw_attempts += 1
                score = multi_ma_dtw_similarity(target, window, MA_LIST)
                if score >= dtw_threshold:
                    ranked_detection = {**detection, 'dtw_score': round(float(score), 6)}
                    ranked.append(ranked_detection)
                    detail_rows.append({'code': code, **ranked_detection})
        fine_detections[str(code).zfill(6)] = ranked

    elapsed = time.perf_counter() - started
    tp = fp = fn = tn = 0
    for _, label in labels.iterrows():
        raw_dets = fine_detections.get(str(label.code).zfill(6), [])
        padded_dets = pad_detections(raw_dets, PADDING_DAYS)
        hit = check_hit_overlap(padded_dets, label.low1_date, label.low2_date)
        if label.label == 1:
            tp += int(hit)
            fn += int(not hit)
        else:
            fp += int(hit)
            tn += int(not hit)
    precision = tp / (tp + fp) * 100 if tp + fp else 0
    recall = tp / (tp + fn) * 100 if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    final_count = sum(map(len, fine_detections.values()))
    return {
        'threshold': dtw_threshold,
        'yolo_candidates': yolo_candidates,
        'dtw_attempts': dtw_attempts,
        'final_count': final_count,
        'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
        'Precision': round(precision, 1),
        'Recall': round(recall, 1),
        'F1': round(f1, 1),
        'elapsed': round(elapsed, 3),
        'time_per_stock': round(elapsed / max(len(stock_cache), 1), 3),
    }


def main():
    cache_path = os.path.join(OUTPUT_DIR, 'yolo_detections.json')
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f'缺少阶段一缓存: {cache_path}；请先运行 yolo_stage1.py')

    stock_cache = load_stock_cache()
    results = []
    for dtw_th in DTW_THRESHOLDS:
        result = run_fusion(dtw_th)
        results.append(result)
        print(f'DTW={dtw_th}: TP={result["TP"]}, FP={result["FP"]}, FN={result["FN"]}, '
              f'P={result["Precision"]}%, R={result["Recall"]}%, F1={result["F1"]}%, '
              f'候选={result["yolo_candidates"]}→{result["final_count"]}, 耗时={result["elapsed"]}s')

    write_csv(pd.DataFrame(results), 'fusion_test.csv')
    print(f'\n融合网格搜索完成，结果写入 fusion_test.csv')


if __name__ == '__main__':
    main()
