"""Stage 2: full rule-filtered multi-MA DTW baseline."""
import json
import os
import time

import pandas as pd

from test_pipeline_common import (
    MA_LIST,
    OUTPUT_DIR,
    STEP,
    WINDOW_SIZE,
    get_w_bottom_target,
    load_evaluation_labels,
    load_stock_cache,
    metric_row,
    multi_ma_dtw_similarity,
    w_bottom_rule_filter,
    write_csv,
)


def main():
    print('加载测试股票和评估标注...')
    stock_cache = load_stock_cache()
    labels = load_evaluation_labels(stock_cache)
    rule_filter = w_bottom_rule_filter
    target = get_w_bottom_target()
    detections = {}
    detail_rows = []
    windows_total = rule_passes = 0
    started = time.perf_counter()

    for number, (code, df) in enumerate(stock_cache.items(), start=1):
        candidates = []
        for start in range(0, len(df) - WINDOW_SIZE + 1, STEP):
            window = df.iloc[start:start + WINDOW_SIZE]
            windows_total += 1
            try:
                if not rule_filter(window):
                    continue
            except Exception:
                continue
            rule_passes += 1
            score = multi_ma_dtw_similarity(target, window, MA_LIST)
            candidate = {
                'start_date': window.iloc[0].trade_date.strftime('%Y-%m-%d'),
                'end_date': window.iloc[-1].trade_date.strftime('%Y-%m-%d'),
                'score': round(float(score), 6),
            }
            candidates.append(candidate)
            detail_rows.append({'code': code, **candidate})
        detections[code] = candidates
        if number % 50 == 0:
            print(f'  DTW扫描: {number}/{len(stock_cache)}，窗口{windows_total}，规则通过{rule_passes}')

    elapsed = time.perf_counter() - started
    prune_rate = 100 * (1 - rule_passes / max(windows_total, 1))
    results = [
        metric_row(labels, detections, threshold, 'score', 'DTW阈值', elapsed, len(stock_cache), {
            '规则剪枝率': round(prune_rate, 1),
        })
        for threshold in (0.4, 0.5, 0.6)
    ]
    write_csv(pd.DataFrame(results), 'dtw_test.csv')
    write_csv(pd.DataFrame(detail_rows), 'dtw_windows.csv')
    manifest = {
        'window_size': WINDOW_SIZE, 'step': STEP, 'stock_count': len(stock_cache),
        'windows_total': windows_total, 'rule_passes': rule_passes,
        'prune_rate': round(prune_rate, 3), 'elapsed_seconds': round(elapsed, 3),
    }
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, 'dtw_manifest.json'), 'w', encoding='utf-8') as output:
        json.dump(manifest, output, ensure_ascii=False, indent=2)
    print(f'DTW基线完成: {windows_total} 个窗口，剪枝{prune_rate:.1f}%，{elapsed:.1f}s')


if __name__ == '__main__':
    main()
