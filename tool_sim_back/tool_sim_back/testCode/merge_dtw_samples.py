"""将DTW Top100 W底候选加入标注数据集"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_DATA = 'E:/gitClone/test_data'
LABELS_DIR = 'E:/gitClone/wbottom_test'
WINDOW = 32

# ---- W底结构提取 ----
def find_w_bottom_structure(df):
    """在窗口内找W底的两个低点和颈线"""
    closes = df['close'].values.astype(float)
    n = len(closes)
    # 找局部低点
    lows = []
    for i in range(2, n-2):
        if closes[i] <= closes[i-2:i+3].min():
            lows.append((i, closes[i]))
    if len(lows) < 2:
        return None
    # 找最佳W底对：间隔>=5天，价格接近（<10%），中间有反弹
    best = None
    best_score = 0
    for i in range(len(lows)):
        for j in range(i+1, len(lows)):
            gap = lows[j][0] - lows[i][0]
            if gap < 5:
                continue
            diff = abs(lows[i][1] - lows[j][1]) / max(lows[i][1], 0.01)
            if diff > 0.10:
                continue
            mid = closes[lows[i][0]:lows[j][0]+1]
            mid_high = max(mid)
            mid_high_idx = lows[i][0] + np.argmax(mid)
            if mid_high <= max(lows[i][1], lows[j][1]) * 1.02:
                continue
            # 计算反弹比例
            rebound = closes[lows[j][0]:]
            if len(rebound) > 0:
                rebound_ratio = (max(rebound) - lows[j][1]) / (mid_high - lows[j][1] + 0.01)
            else:
                rebound_ratio = 0
            # 综合评分
            s = (1-diff/0.10) * 0.3 + min(gap/15, 1) * 0.2 + min(rebound_ratio, 2) * 0.3 + 0.2
            if s > best_score:
                best_score = s
                best = (lows[i], lows[j], mid_high_idx, mid_high, rebound_ratio, gap, diff)
    return best


def scan_dtw_top100():
    """重新运行DTW扫描获取Top100"""
    from dtw_scan import dtw_score, TARGET, OUTPUT_DIR
    csv_files = sorted([f for f in os.listdir(TEST_DATA) if f.endswith('.csv')])
    codes = [f.replace('.csv','') for f in csv_files]

    all_dets = []
    for idx, code in enumerate(codes):
        fpath = os.path.join(TEST_DATA, f'{code}.csv')
        try:
            df = pd.read_csv(fpath)
            if len(df) < WINDOW:
                continue
            df['trade_date'] = pd.to_datetime(df['timestamps'] if 'timestamps' in df.columns else df['trade_date'])
            closes = df['close'].values.astype(np.float64)
            for i in range(0, len(closes) - WINDOW + 1, 8):
                score = dtw_score(TARGET, closes[i:i+WINDOW])
                if score >= 0.65:
                    all_dets.append({
                        'code': code,
                        'start_date': df.iloc[i]['trade_date'].strftime('%Y-%m-%d'),
                        'end_date': df.iloc[i+WINDOW-1]['trade_date'].strftime('%Y-%m-%d'),
                        'score': round(score*100, 2),
                        'start_idx': i,
                    })
        except:
            continue
        if (idx+1) % 100 == 0:
            print(f"  扫描: {idx+1}/{len(codes)}")

    all_dets.sort(key=lambda x: x['score'], reverse=True)
    return all_dets[:100]


print("重新扫描DTW Top100...")
top100 = scan_dtw_top100()
print(f"Top100获取完成")

# 加载原始数据
train = pd.read_csv(os.path.join(LABELS_DIR, 'train.csv'))
test = pd.read_csv(os.path.join(LABELS_DIR, 'test.csv'))
existing = pd.concat([train, test], ignore_index=True)
print(f"现有标注: {len(existing)} 条 (正{len(existing[existing.label==1])} 负{len(existing[existing.label==0])})")

# 为每个DTW候选找W底结构
new_rows = []
for i, det in enumerate(top100):
    code = det['code']
    fpath = os.path.join(TEST_DATA, f'{code}.csv')
    try:
        df = pd.read_csv(fpath)
        df['trade_date'] = pd.to_datetime(df['timestamps'] if 'timestamps' in df.columns else df['trade_date'])
        mask = (df['trade_date'] >= pd.Timestamp(det['start_date'])) & \
               (df['trade_date'] <= pd.Timestamp(det['end_date']))
        window = df[mask].reset_index(drop=True).head(WINDOW)
        if len(window) < 15:
            continue

        struct = find_w_bottom_structure(window)
        if struct is None:
            continue
        low1, low2, neck_idx, neck_price, reb_ratio, gap, diff = struct

        new_rows.append({
            'code': code,
            'score': det['score'],
            'start_date': det['start_date'],
            'end_date': det['end_date'],
            'low1_date': window.iloc[low1[0]]['trade_date'].strftime('%Y-%m-%d'),
            'low1_price': round(low1[1], 4),
            'low2_date': window.iloc[low2[0]]['trade_date'].strftime('%Y-%m-%d'),
            'low2_price': round(low2[1], 4),
            'neckline_date': window.iloc[neck_idx]['trade_date'].strftime('%Y-%m-%d'),
            'neckline_price': round(neck_price, 4),
            'rebound_high_date': window.iloc[min(low2[0]+5, len(window)-1)]['trade_date'].strftime('%Y-%m-%d'),
            'rebound_high_price': round(window.iloc[low2[0]:]['close'].max(), 4),
            'gap_days': gap,
            'bottom_diff_pct': round(diff*100, 3),
            'neckline_prem_pct': round((neck_price/max(low1[1], low2[1])-1)*100, 3),
            'rebound_ratio': round(reb_ratio, 3),
            'label': 1,
            'annotator': 'dtw_top100',
            'note': f'DTW={det["score"]:.1f}',
        })
    except Exception as e:
        print(f"  [{i+1}] {code} 结构提取失败: {e}")

new_df = pd.DataFrame(new_rows)
new_df = new_df[['code','score','start_date','end_date','low1_date','low1_price',
    'low2_date','low2_price','neckline_date','neckline_price','rebound_high_date',
    'rebound_high_price','gap_days','bottom_diff_pct','neckline_prem_pct',
    'rebound_ratio','label','annotator','note']]

# 合并并去重（同一股票+同low1_date视为重复）
merged = pd.concat([existing, new_df], ignore_index=True)
dup_key = merged['code'].astype(str) + '_' + merged['low1_date'].astype(str)
merged = merged[~dup_key.duplicated(keep='first')].reset_index(drop=True)

print(f"DTW候选加入: {len(new_df)} 条有效")
print(f"合并后总量: {len(merged)} 条 (正{len(merged[merged.label==1])} 负{len(merged[merged.label==0])})")

# 保存
out_path = os.path.join(LABELS_DIR, 'all_labeled.csv')
merged.to_csv(out_path, index=False)
print(f"已保存: {out_path}")

# 同时保存一份DTW新增的清单
new_out = os.path.join(LABELS_DIR, 'dtw_top100_labeled.csv')
new_df.to_csv(new_out, index=False)
print(f"DTW新增: {new_out}")
