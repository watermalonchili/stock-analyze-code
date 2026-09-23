"""DTW扫描中证500全部股票，导出Top100 W底相似K线图（快速版）"""
import sys, os, time
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_DATA = 'E:/gitClone/test_data'
OUTPUT_DIR = 'E:/gitClone/test_output/dtw_top100_samples'
os.makedirs(OUTPUT_DIR, exist_ok=True)

WINDOW = 32
STEP = 8  # 步长8天，每只股约150窗口

# ---- 标准W底骨架 32点 ----
prices = [10.0, 8.0, 10.5, 8.1, 11.0]
TARGET = np.interp(np.linspace(0, 4, WINDOW), np.arange(5), prices)
TARGET = (TARGET - TARGET.mean()) / (TARGET.std() + 1e-8)

# ---- DTW (纯numpy, 快) ----
def dtw_score(template, query):
    q = np.asarray(query, dtype=np.float64)
    q = (q - q.mean()) / (q.std() + 1e-8)
    n = len(template)
    INF = np.inf
    dp = np.full((n+1, n+1), INF)
    dp[0, 0] = 0.0
    for i in range(1, n+1):
        ti = template[i-1]
        row = dp[i]; prev = dp[i-1]
        for j in range(1, n+1):
            row[j] = abs(ti - q[j-1]) + min(prev[j], row[j-1], prev[j-1])
    return float(np.exp(-dp[n, n] / n))

# ---- K线图 ----
def draw_kline(df, img_size=640):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image; import io
    n = len(df); dpi = 100
    fig, ax = plt.subplots(figsize=(img_size/dpi, img_size/dpi), dpi=dpi)
    up = df[df.close >= df.open]
    down = df[df.close < df.open]
    if not up.empty:
        ax.bar(up.index, up.close.values-up.open.values, bottom=up.open.values, color='red', width=0.7)
        ax.bar(up.index, up.high.values-up.close.values, bottom=up.close.values, color='red', width=0.15)
        ax.bar(up.index, up.low.values-up.open.values, bottom=up.open.values, color='red', width=0.15)
    if not down.empty:
        ax.bar(down.index, down.open.values-down.close.values, bottom=down.close.values, color='green', width=0.7)
        ax.bar(down.index, down.high.values-down.open.values, bottom=down.open.values, color='green', width=0.15)
        ax.bar(down.index, down.low.values-down.close.values, bottom=down.close.values, color='green', width=0.15)
    ax.set_xlim(-0.5, n-0.5); ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    buf = io.BytesIO(); fig.savefig(buf, format='png', facecolor='white', pad_inches=0)
    plt.close(fig); buf.seek(0)
    return Image.open(buf).convert('RGB')

# ---- 主流程 ----
csv_files = sorted([f for f in os.listdir(TEST_DATA) if f.endswith('.csv')])
codes = [f.replace('.csv','') for f in csv_files]
print(f"股票池: {len(codes)} 只 | WINDOW={WINDOW} STEP={STEP} | 仅收盘价DTW")

t0 = time.time()
all_dets = []
loaded = 0

for idx, code in enumerate(codes):
    fpath = os.path.join(TEST_DATA, f'{code}.csv')
    try:
        df = pd.read_csv(fpath)
        if len(df) < WINDOW:
            continue
        df['trade_date'] = pd.to_datetime(df['timestamps'] if 'timestamps' in df.columns else df['trade_date'])
        closes = df['close'].values.astype(np.float64)
    except Exception:
        continue
    loaded += 1

    # 滑窗扫描
    for i in range(0, len(closes) - WINDOW + 1, STEP):
        score = dtw_score(TARGET, closes[i:i+WINDOW])
        if score >= 0.65:
            sd = df.iloc[i]['trade_date'].strftime('%Y-%m-%d')
            ed = df.iloc[i+WINDOW-1]['trade_date'].strftime('%Y-%m-%d')
            all_dets.append({'code': code, 'start': sd, 'end': ed, 'score': round(score, 4)})

    if (idx+1) % 50 == 0:
        print(f"  [{idx+1}/{len(codes)}] 加载{loaded}只, 高分{len(all_dets)}个, {time.time()-t0:.0f}s")

print(f"\n扫描: {loaded}只有效, 高分(≥0.65) {len(all_dets)}个, {time.time()-t0:.1f}s")

# Top100 排序
all_dets.sort(key=lambda x: x['score'], reverse=True)
print(f"Top5: {[(d['code'], d['score']) for d in all_dets[:5]]}")

# 导出K线图
top100 = all_dets[:100]
saved = 0
for i, det in enumerate(top100):
    fpath = os.path.join(TEST_DATA, f'{det["code"]}.csv')
    try:
        df = pd.read_csv(fpath)
        df['trade_date'] = pd.to_datetime(df['timestamps'] if 'timestamps' in df.columns else df['trade_date'])
        mask = (df['trade_date'] >= pd.Timestamp(det['start'])) & \
               (df['trade_date'] <= pd.Timestamp(det['end']))
        w = df[mask].reset_index(drop=True).head(64)
        if len(w) < 10:
            continue
        img = draw_kline(w)
        fname = f"{i+1:03d}_{det['code']}_{det['start']}_{det['end']}_score{det['score']:.4f}.png"
        img.save(os.path.join(OUTPUT_DIR, fname))
        saved += 1
    except Exception as e:
        print(f"  [{i+1}] {det['code']} 失败: {e}")

print(f"导出 {saved} 张K线图 → {OUTPUT_DIR}")
print(f"总耗时 {time.time()-t0:.1f}s")
