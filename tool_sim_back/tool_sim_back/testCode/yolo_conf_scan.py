"""YOLO 视觉模型 conf 阈值扫描（0.1~0.6），复用 test_runner 的评估集与命中判定。"""
import sys, os, time, json
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'few_shot_learning', 'yolo0623'))

from utils import calculate_ma
from main import detect_pattern_yolo
from testCode.test_runner import (
    load_stock, check_hit_overlap, generate_negatives,
    MA_LIST, TEST_DATA_DIR, LABELS_DIR, OUTPUT_DIR,
)

MODE_INDEX = 'wbtest_kline'
CONF_SCAN = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
SCAN_CONF = 0.1  # 检测时最低置信度，保存所有 >=0.1 的候选


def main():
    gt_all_labeled = pd.read_csv(os.path.join(LABELS_DIR, 'all_labeled.csv'))
    gt_pos_all = gt_all_labeled[gt_all_labeled.label == 1].copy()
    gt_neg_labeled = gt_all_labeled[gt_all_labeled.label == 0].copy()
    print(f"标注数据集: {len(gt_all_labeled)} 条 (正{len(gt_pos_all)} 负{len(gt_neg_labeled)})")

    test_codes = []
    for fn in os.listdir(TEST_DATA_DIR):
        if fn.lower().endswith('.csv'):
            code = os.path.splitext(fn)[0].split('.')[0]
            if code.isdigit():
                test_codes.append(code.zfill(6))
    all_stocks = sorted(set(test_codes))
    print(f"股票池: {len(all_stocks)} 只")

    stock_cache = {}
    for code in all_stocks:
        df = load_stock(code)
        if df is not None:
            stock_cache[code] = calculate_ma(df, MA_LIST)
    print(f"加载股票: {len(stock_cache)} 只")

    negs_new = generate_negatives(gt_pos_all, stock_cache, n=50)
    gt_neg_all = pd.concat([gt_neg_labeled, pd.DataFrame(negs_new)], ignore_index=True)
    gt_all = pd.concat([gt_pos_all, gt_neg_all], ignore_index=True)
    print(f"评估集: {len(gt_all)} 条 (正{len(gt_pos_all)} 负{len(gt_neg_all)})")

    # YOLO 检测（conf>=0.1 全量候选）
    yolo_detections = {}
    t0 = time.time()
    for idx, code in enumerate(sorted(stock_cache.keys())):
        try:
            hits = detect_pattern_yolo(stock_cache[code], MA_LIST, MODE_INDEX,
                                       conf_threshold=SCAN_CONF, img_size=416)
            yolo_detections[code] = hits
        except Exception as e:
            yolo_detections[code] = []
        if (idx + 1) % 50 == 0:
            print(f"  YOLO检测: {idx+1}/{len(stock_cache)}")
    yolo_time = time.time() - t0
    total_cand = sum(len(v) for v in yolo_detections.values())
    print(f"YOLO检测完成: 总耗时 {yolo_time:.1f}s, 候选数 {total_cand}")

    # 保存原始检测结果（剔除不可序列化的 segment_df 字段）
    serializable = {
        code: [{k: v for k, v in d.items() if k != 'segment_df'} for d in dets]
        for code, dets in yolo_detections.items()
    }
    out_json = os.path.join(OUTPUT_DIR, 'yolo_detections_20260914.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'mode': MODE_INDEX, 'scan_confidence': SCAN_CONF,
                   'detections': serializable}, f, ensure_ascii=False)
    print(f"已保存检测结果 → {out_json}")

    # 逐阈值算指标
    rows = []
    print("\n conf    TP    FP    FN    TN    P%     R%     F1%    漏检%  误报%")
    for conf in CONF_SCAN:
        tp = fp = fn = tn = 0
        for _, row in gt_all.iterrows():
            code = str(row['code']).zfill(6)
            dets = [d for d in yolo_detections.get(code, []) if d.get('confidence', 0) >= conf]
            hit = check_hit_overlap(dets, row['low1_date'], row['low2_date'])
            if row['label'] == 1 and hit:
                tp += 1
            elif row['label'] == 1 and not hit:
                fn += 1
            elif row['label'] == 0 and hit:
                fp += 1
            else:
                tn += 1
        p = tp / (tp + fp) * 100 if (tp + fp) else 0
        r = tp / (tp + fn) * 100 if (tp + fn) else 0
        f1 = 2 * p * r / (p + r) if (p + r) else 0
        miss = 100 - r
        fpr = fp / (fp + tn) * 100 if (fp + tn) else 0
        rows.append({'置信度阈值': conf, 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
                     'Precision': round(p, 1), 'Recall': round(r, 1), 'F1': round(f1, 1),
                     '漏检率': round(miss, 1), '误报率': round(fpr, 1)})
        print(f" {conf:.1f}   {tp:5d} {fp:5d} {fn:5d} {tn:5d}  {p:5.1f} {r:5.1f} {f1:5.1f}  {miss:5.1f} {fpr:5.1f}")

    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_DIR, 'yolo_conf_scan.csv'), index=False, encoding='utf-8-sig')
    print(f"\n结果已保存 → {os.path.join(OUTPUT_DIR, 'yolo_conf_scan.csv')}")


if __name__ == '__main__':
    main()
