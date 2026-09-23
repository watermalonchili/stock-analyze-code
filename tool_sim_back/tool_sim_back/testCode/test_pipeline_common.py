"""Shared helpers for independent W-bottom benchmark stages."""
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_stock_data, calculate_ma

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_DIR = os.path.join(os.path.dirname(PROJECT_DIR), 'test_data')
OUTPUT_DIR = os.path.join(os.path.dirname(PROJECT_DIR), 'test_output')
LABELS_DIR = os.path.join(os.path.dirname(PROJECT_DIR), 'wbottom_test')
MA_LIST = [4, 8, 12, 16, 20, 47]
WINDOW_SIZE = 32
STEP = 2


def write_csv(dataframe, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        dataframe.to_csv(path, index=False, encoding='utf-8-sig')
    except PermissionError:
        path = os.path.join(OUTPUT_DIR, filename.replace('.csv', '_v2.csv'))
        dataframe.to_csv(path, index=False, encoding='utf-8-sig')
        print(f'  [警告] 文件被占用，写入 {path}')
    return path


def stock_codes():
    if not os.path.isdir(TEST_DATA_DIR):
        return []
    return sorted(
        match.group(1)
        for filename in os.listdir(TEST_DATA_DIR)
        if (match := re.fullmatch(r'(\d{6})\.csv', filename, flags=re.IGNORECASE))
    )


def load_stock(code):
    ts_code = f'{code}.SH' if str(code).startswith('6') else f'{code}.SZ'
    df = get_stock_data(ts_code, None, None, data_folder=TEST_DATA_DIR)
    if df is None or df.empty:
        return None
    df = df.copy()
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date').reset_index(drop=True)
    df = df.drop(columns=['name', 'industry', 'block'], errors='ignore')
    return calculate_ma(df, MA_LIST)


def load_stock_cache(codes=None):
    cache = {}
    codes = stock_codes() if codes is None else codes
    for index, code in enumerate(codes, start=1):
        try:
            df = load_stock(code)
        except Exception as exc:
            print(f'  {code} 数据加载失败: {exc}')
            continue
        if df is not None and not df.empty:
            cache[str(code).zfill(6)] = df
        if index % 50 == 0:
            print(f'  数据加载: {index}/{len(codes)}')
    return cache


def load_evaluation_labels(stock_cache):
    labels = pd.read_csv(os.path.join(LABELS_DIR, 'all_labeled.csv'))
    positives = labels[labels.label == 1].copy()
    negatives = labels[labels.label == 0].copy()
    generated = generate_negatives(positives, stock_cache, n=50)
    return pd.concat([positives, negatives, pd.DataFrame(generated)], ignore_index=True)


def generate_negatives(positives, stock_cache, n=50):
    rng = np.random.default_rng(42)
    negatives = []
    for code, df in stock_cache.items():
        if len(df) < WINDOW_SIZE + 20:
            continue
        ranges = []
        for _, row in positives[positives.code.astype(str).str.zfill(6) == code].iterrows():
            try:
                ranges.append((
                    pd.Timestamp(str(row.low1_date)[:10]) - pd.Timedelta(days=20),
                    pd.Timestamp(str(row.low2_date)[:10]) + pd.Timedelta(days=20),
                ))
            except (TypeError, ValueError):
                continue
        for _ in range(10):
            if sum(item['code'] == code for item in negatives) >= 2:
                break
            start = int(rng.integers(0, len(df) - WINDOW_SIZE))
            begin = df.iloc[start].trade_date
            end = df.iloc[start + WINDOW_SIZE - 1].trade_date
            if any(begin <= range_end and end >= range_start for range_start, range_end in ranges):
                continue
            negatives.append({
                'code': code,
                'low1_date': begin.strftime('%Y-%m-%d'),
                'low2_date': end.strftime('%Y-%m-%d'),
                'label': 0,
            })
            if len(negatives) >= n:
                return negatives
    return negatives


def check_hit_overlap(detections, low1_date, low2_date, min_overlap_ratio=0.5):
    try:
        start = pd.Timestamp(str(low1_date)[:10]) - pd.Timedelta(days=10)
        end = pd.Timestamp(str(low2_date)[:10]) + pd.Timedelta(days=10)
    except (TypeError, ValueError):
        return False
    target_span = max((end - start).days, 1)
    for detection in detections:
        try:
            det_start = pd.Timestamp(str(detection['start_date'])[:10])
            det_end = pd.Timestamp(str(detection['end_date'])[:10])
        except (KeyError, TypeError, ValueError):
            continue
        overlap_start, overlap_end = max(start, det_start), min(end, det_end)
        if overlap_end < overlap_start:
            continue
        overlap = (overlap_end - overlap_start).days
        if overlap / min(target_span, max((det_end - det_start).days, 1)) >= min_overlap_ratio:
            return True
    return False


def metric_row(labels, detections, threshold, score_key, threshold_name, elapsed, stock_count, extra=None):
    tp = fp = fn = tn = 0
    for _, label in labels.iterrows():
        code = str(label.code).zfill(6)
        matches = [item for item in detections.get(code, []) if item.get(score_key, 0) >= threshold]
        hit = check_hit_overlap(matches, label.low1_date, label.low2_date)
        if label.label == 1:
            tp += int(hit)
            fn += int(not hit)
        else:
            fp += int(hit)
            tn += int(not hit)
    precision = 100 * tp / (tp + fp) if tp + fp else 0
    recall = 100 * tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    row = {
        threshold_name: threshold, 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
        'Precision': round(precision, 1), 'Recall': round(recall, 1), 'F1': round(f1, 1),
        '漏检率': round(100 - recall, 1),
        '误报率': round(100 * fp / (fp + tn), 1) if fp + tn else 0,
        '平均耗时/股': round(elapsed / max(stock_count, 1), 3),
    }
    if extra:
        row.update(extra)
    return row


def dtw_similarity(target, query):
    target = np.asarray(target, dtype=float)
    query = np.asarray(query, dtype=float)
    if not len(target) or not len(query):
        return 0.0
    target = (target - target.mean()) / (target.std() + 1e-8)
    query = (query - query.mean()) / (query.std() + 1e-8)
    dp = np.full((len(target) + 1, len(query) + 1), np.inf)
    dp[0, 0] = 0
    for i in range(1, len(target) + 1):
        for j in range(1, len(query) + 1):
            dp[i, j] = abs(target[i - 1] - query[j - 1]) + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return float(np.exp(-dp[-1, -1] / max(len(target), len(query))))


def multi_ma_dtw_similarity(target, window, ma_list=MA_LIST):
    close_score = dtw_similarity(target, window.close.to_numpy(dtype=float))
    scores = []
    for ma in ma_list:
        column = f'MA{ma}'
        if column in window:
            values = window[column].to_numpy(dtype=float)
            if np.count_nonzero(~np.isnan(values)) >= 10:
                scores.append(dtw_similarity(target, pd.Series(values).interpolate().bfill().ffill()))
    return 0.7 * close_score + 0.3 * (float(np.mean(scores)) if scores else close_score)


def get_w_bottom_target():
    points = [10.0, 8.0, 10.5, 8.1, 11.0]
    return np.interp(np.linspace(0, len(points) - 1, WINDOW_SIZE), np.arange(len(points)), points)


def w_bottom_rule_filter(window):
    closes = window.close.to_numpy(dtype=float)
    n = len(closes)
    lows = [(i, closes[i]) for i in range(2, n - 2) if closes[i] <= closes[i-2:i+3].min()]
    for pos, (i1, p1) in enumerate(lows):
        for i2, p2 in lows[pos+1:]:
            gap = i2 - i1
            if gap < 5:  # 间距至少5天
                continue
            diff = abs(p1 - p2) / max(p1, 0.01)
            if diff > 0.08:  # 两底价格差 ≤ 8%
                continue
            mid = closes[i1:i2+1]
            mid_high = max(mid)
            low_max = max(p1, p2)
            if mid_high < low_max * 1.03:  # 中间反弹至少高于低点3%
                continue
            # 右侧有反弹迹象（不低于第二底2%）
            if i2 + 3 < n:
                if max(closes[i2:]) < p2 * 1.02:
                    continue
            return True
    return False


def get_rule_filter():
    try:
        from llm_agent import generate_ai_filter
        return generate_ai_filter(
            ['走势整体呈震荡上行趋势', '共包含 5 个关键骨架拐点', '波动幅度约 15%'],
            'W底形态，两个低点价格接近，中间有反弹高点',
        )
    except Exception as exc:
        print(f'  LLM规则过滤不可用: {exc}')
        return w_bottom_rule_filter
