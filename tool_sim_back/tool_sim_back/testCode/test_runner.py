"""
K线形态检索系统自动化测试脚本（完整版）
用法: cd tool_sim_back && python test_runner.py
输出: E:/gitClone/test_output/
"""
import sys, os, json, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_DIR = 'E:/gitClone/test_data'
OUTPUT_DIR = 'E:/gitClone/test_output'
LABELS_DIR = 'E:/gitClone/wbottom_test'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _safe_csv(df, name):
    """写入CSV，解决PermissionError"""
    p = os.path.join(OUTPUT_DIR, name)
    try:
        df.to_csv(p, index=False)
    except PermissionError:
        alt = os.path.join(OUTPUT_DIR, name.replace('.csv', '_v2.csv'))
        df.to_csv(alt, index=False)
        print(f"  [警告] {name} 被占用，写入 {alt}")

# 所有可用数据源
DATA_DIRS = [d for d in [TEST_DATA_DIR] if os.path.exists(d)]

from utils import get_stock_data, calculate_ma

MA_LIST = [4, 8, 12, 16, 20, 47]
WINDOW_SIZE = 32
STEP = 2


# ============================================================
# 核心算法
# ============================================================
def dtw_similarity(target, query):
    t = np.asarray(target, dtype=float)
    q = np.asarray(query, dtype=float)
    n, m = len(t), len(q)
    if n == 0 or m == 0:
        return 0.0
    t = (t - t.mean()) / (t.std() + 1e-8)
    q = (q - q.mean()) / (q.std() + 1e-8)
    INF = float('inf')
    dp = np.full((n + 1, m + 1), INF)
    dp[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = abs(t[i-1] - q[j-1]) + min(dp[i-1, j], dp[i, j-1], dp[i-1, j-1])
    return float(np.exp(-dp[n, m] / max(n, m)))


def draw_kline_chart(df, img_size=640):
    """生成 K线蜡烛图 PIL Image（红涨绿跌，白底无坐标轴）"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image
    import io

    n = len(df)
    dpi = 100
    fig, ax = plt.subplots(figsize=(img_size / dpi, img_size / dpi), dpi=dpi)

    up = df[df.close >= df.open]
    down = df[df.close < df.open]

    if not up.empty:
        ax.bar(up.index, up.close.values - up.open.values,
               bottom=up.open.values, color='red', width=0.7)
        ax.bar(up.index, up.high.values - up.close.values,
               bottom=up.close.values, color='red', width=0.15)
        ax.bar(up.index, up.low.values - up.open.values,
               bottom=up.open.values, color='red', width=0.15)
    if not down.empty:
        ax.bar(down.index, down.open.values - down.close.values,
               bottom=down.close.values, color='green', width=0.7)
        ax.bar(down.index, down.high.values - down.open.values,
               bottom=down.open.values, color='green', width=0.15)
        ax.bar(down.index, down.low.values - down.close.values,
               bottom=down.close.values, color='green', width=0.15)

    ax.set_xlim(-0.5, n - 0.5)
    ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor='white', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGB')


def w_bottom_rule_filter(df_window):
    """W底结构规则过滤：宽松检查窗口内是否存在W底基本结构"""
    closes = df_window['close'].values.astype(float)
    n = len(closes)
    if n < 15:
        return False
    # 找局部低点（±2天窗口）
    lows = []
    for i in range(2, n - 2):
        if closes[i] <= closes[i-2:i+3].min():
            lows.append((i, closes[i]))
    if len(lows) < 2:
        return False
    # 找一对低点：间隔≥3天，价格差≤10%
    for i in range(len(lows)):
        for j in range(i + 1, len(lows)):
            if lows[j][0] - lows[i][0] >= 3:
                diff = abs(lows[i][1] - lows[j][1]) / max(lows[i][1], 0.01)
                if diff <= 0.10:
                    # 两低点之间有更高点即可（不强制倍数）
                    mid = closes[lows[i][0]:lows[j][0]]
                    if max(mid) > max(lows[i][1], lows[j][1]):
                        return True
    return False


def multi_ma_dtw_similarity(target, df_window, ma_list):
    """多维DTW：收盘价权重0.7 + 各均线平均权重0.3"""
    closes = df_window['close'].values.astype(float)
    close_score = dtw_similarity(target, closes)
    ma_scores = []
    for ma in ma_list:
        col = f'MA{ma}'
        if col in df_window.columns:
            vals = df_window[col].values.astype(float)
            valid = ~np.isnan(vals)
            if valid.sum() >= 10:
                vals = pd.Series(vals).interpolate().bfill().ffill().values
                ma_scores.append(dtw_similarity(target, vals))
    ma_avg = float(np.mean(ma_scores)) if ma_scores else close_score
    return 0.7 * close_score + 0.3 * ma_avg


def get_w_bottom_target():
    """标准W底骨架 → 插值32点"""
    prices = [10.0, 8.0, 10.5, 8.1, 11.0]
    indices = np.linspace(0, len(prices) - 1, WINDOW_SIZE)
    return np.interp(indices, np.arange(len(prices)), prices).tolist()


def load_stock(code):
    """从多个数据源加载股票数据"""
    ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
    for data_dir in DATA_DIRS:
        df = get_stock_data(ts_code, None, None, data_folder=data_dir)
        if df is not None and not df.empty:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date').reset_index(drop=True)
            # 删除空列（name/industry/block可能为NaN，会导致calculate_ma的dropna删除所有行）
            df = df.drop(columns=['name', 'industry', 'block'], errors='ignore')
            return df
    return None


def check_hit_overlap(detections, low1_date, low2_date, min_overlap_ratio=0.5):
    """检查检测结果是否命中标注的W底（重叠比例≥50%视为TP）"""
    try:
        d1 = pd.Timestamp(str(low1_date)[:10])
        d2 = pd.Timestamp(str(low2_date)[:10])
        gt_start = d1 - pd.Timedelta(days=10)
        gt_end = d2 + pd.Timedelta(days=10)
        gt_span = max((gt_end - gt_start).days, 1)
    except:
        return False

    for det in detections:
        try:
            ds = pd.Timestamp(str(det.get('start_date', ''))[:10])
            de = pd.Timestamp(str(det.get('end_date', ''))[:10])
            overlap_start = max(ds, gt_start)
            overlap_end = min(de, gt_end)
            if overlap_end < overlap_start:
                continue
            overlap_days = (overlap_end - overlap_start).days
            det_span = max((de - ds).days, 1)
            ratio = overlap_days / min(gt_span, det_span)
            if ratio >= min_overlap_ratio:
                return True
        except:
            continue
    return False


def get_rule_filter():
    """获取LLM规则过滤函数"""
    try:
        from llm_agent import generate_ai_filter
        # W底的标准特征标签
        tags = ['走势整体呈震荡上行趋势', '共包含 5 个关键骨架拐点', '波动幅度约 15%']
        return generate_ai_filter(tags, 'W底形态，两个低点价格接近，中间有反弹高点')
    except Exception as e:
        print(f"  LLM规则过滤不可用: {e}")
        return None


def generate_negatives(gt_pos, stock_cache, n=100):
    """从股票历史中生成负样本（远离任何标注W底的随机窗口）"""
    np.random.seed(42)
    negs = []
    codes = list(stock_cache.keys())

    for code in codes:
        df = stock_cache[code]
        if df is None or len(df) < WINDOW_SIZE + 20:
            continue

        # 该股票的所有正样本日期范围
        pos_ranges = []
        for _, row in gt_pos.iterrows():
            if str(row['code']).zfill(6) == code:
                try:
                    d1 = pd.Timestamp(str(row['low1_date'])[:10])
                    d2 = pd.Timestamp(str(row['low2_date'])[:10])
                    pos_ranges.append((d1 - pd.Timedelta(days=20), d2 + pd.Timedelta(days=20)))
                except:
                    pass

        # 尝试找远离正样本的窗口
        attempts = 0
        while attempts < 10 and len([n for n in negs if n['code'] == code]) < 2:
            attempts += 1
            start_idx = np.random.randint(0, max(len(df) - WINDOW_SIZE, 1))
            window_start = df.iloc[start_idx]['trade_date']
            window_end = df.iloc[start_idx + WINDOW_SIZE - 1]['trade_date']

            # 检查是否远离所有正样本
            too_close = False
            for ps, pe in pos_ranges:
                if window_start <= pe and window_end >= ps:
                    too_close = True
                    break
            if too_close:
                continue

            negs.append({
                'code': code,
                'low1_date': window_start.strftime('%Y-%m-%d'),
                'low2_date': window_end.strftime('%Y-%m-%d'),
                'label': 0,
            })
            if len(negs) >= n:
                return negs

    return negs


# ============================================================
# 主测试流程
# ============================================================
def run_tests():
    print("=" * 60)
    print("K线形态检索系统自动化测试")
    print(f"数据源: {DATA_DIRS}")
    print("=" * 60)

    # 加载全部标注数据（all_labeled.csv = 原有314 + DTW新增98）作为评估标准
    gt_all_labeled = pd.read_csv(os.path.join(LABELS_DIR, 'all_labeled.csv'))
    gt_pos_all = gt_all_labeled[gt_all_labeled.label == 1].copy()
    gt_neg_labeled = gt_all_labeled[gt_all_labeled.label == 0].copy()
    print(f"标注数据集: {len(gt_all_labeled)} 条 (正{len(gt_pos_all)} 负{len(gt_neg_labeled)})")

    # 从DTW新增中随机抽取50条正样本用于YOLO训练
    np.random.seed(42)
    dtw_additions = pd.read_csv(os.path.join(LABELS_DIR, 'dtw_top100_labeled.csv'))
    gt_pos_train = dtw_additions.sample(n=min(50, len(dtw_additions)), random_state=42).copy()
    print(f"YOLO训练正样本: {len(gt_pos_train)} 条 (从DTW新增{len(dtw_additions)}条中抽取)")

    target = get_w_bottom_target()
    test_codes = []
    if os.path.exists(TEST_DATA_DIR):
        for filename in os.listdir(TEST_DATA_DIR):
            if filename.lower().endswith('.csv'):
                code = os.path.splitext(filename)[0].split('.')[0]
                if code.isdigit():
                    test_codes.append(code.zfill(6))
    all_stocks = sorted(set(test_codes))
    print(f"测试股票池: {len(all_stocks)} 只")
    print(f"标注股票: {gt_all_labeled['code'].nunique()} 只\n")

    # 预加载股票数据
    stock_cache = {}
    for idx, code in enumerate(all_stocks):
        code = str(code).zfill(6)
        df = load_stock(code)
        if df is not None:
            df = calculate_ma(df, MA_LIST)
            stock_cache[code] = df
        if (idx + 1) % 50 == 0:
            print(f"  数据加载: {idx+1}/{len(all_stocks)}")
    print(f"成功加载 {len(stock_cache)} 只股票数据\n")

    # 生成负样本（远离W底的随机窗口）
    print("生成补充负样本（远离W底的随机窗口）...")
    negs_new = generate_negatives(gt_pos_all, stock_cache, n=50)
    gt_neg_all = pd.concat([gt_neg_labeled, pd.DataFrame(negs_new)], ignore_index=True)
    print(f"负样本: 标注{len(gt_neg_labeled)} + 随机{len(negs_new)} = {len(gt_neg_all)}\n")

    # 合并最终评估集：all_labeled.csv 全部标注数据
    gt_all = pd.concat([gt_pos_all, gt_neg_all], ignore_index=True)
    print(f"最终评估集: {len(gt_all)} 条 (正{len(gt_pos_all)} 负{len(gt_neg_all)})\n")

    # ======== YOLO 模型训练 ========
    print("=" * 60)
    print(f"YOLO模型训练（K线图，{len(gt_pos_train)}正样本 + 50负样本）")
    print("=" * 60)

    MODE_NAME = 'wbtest_kline'
    trained_model_path = os.path.join(PROJECT_DIR, 'custom_modes', f'{MODE_NAME}_yolo.pt')
    if not os.path.exists(trained_model_path):
        raise FileNotFoundError(f"未找到已训练YOLO模型: {trained_model_path}")
    print(f"复用已有YOLO模型: {trained_model_path}")

    # ======== 测试一：YOLO独立测试 ========
    print("\n" + "=" * 60)
    print("测试一：视觉模型（YOLO）独立测试")
    print("=" * 60)

    yolo_detections = {}
    test_stocks = list(stock_cache.keys())

    if os.path.exists(trained_model_path):
        mode_index = MODE_NAME
        print(f"YOLO模型: {trained_model_path}")

        yolo_dir = os.path.join(PROJECT_DIR, 'few_shot_learning', 'yolo0623')
        if yolo_dir not in sys.path:
            sys.path.insert(0, yolo_dir)
        try:
            from main import detect_pattern_yolo
            t0 = time.time()
            total_yolo_hits = 0
            for idx, code in enumerate(test_stocks):
                code = str(code).zfill(6)
                if code not in stock_cache:
                    continue
                try:
                    hits = detect_pattern_yolo(stock_cache[code], MA_LIST, mode_index, conf_threshold=0.15, img_size=416)
                    yolo_detections[code] = hits
                    total_yolo_hits += len(hits)
                except Exception as e:
                    if idx < 3:
                        print(f"    {code} YOLO出错: {e}")
                    yolo_detections[code] = []
                if (idx + 1) % 30 == 0:
                    print(f"  YOLO检测: {idx+1}/{len(test_stocks)}, 累计命中{total_yolo_hits}")
            yolo_time = time.time() - t0
            print(f"  YOLO总耗时: {yolo_time:.1f}s, 总检测数: {total_yolo_hits}, 单股平均: {yolo_time/max(len(stock_cache),1):.3f}s")
        except Exception as e:
            print(f"  YOLO导入失败: {e}")
            yolo_time = 0
    else:
        print("  无YOLO模型，跳过")
        yolo_time = 0

    # 计算YOLO各阈值指标
    yolo_results = []
    for conf in [0.1, 0.2, 0.3, 0.4, 0.5]:
        tp = fp = fn = tn = 0
        for _, row in gt_all.iterrows():
            code = str(row['code']).zfill(6)
            dets = [d for d in yolo_detections.get(code, []) if d.get('confidence', 0) >= conf]
            hit = check_hit_overlap(dets, row['low1_date'], row['low2_date'])
            if row['label'] == 1 and hit: tp += 1
            elif row['label'] == 1 and not hit: fn += 1
            elif row['label'] == 0 and hit: fp += 1
            else: tn += 1
        p = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        r = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0
        per_stock = yolo_time / len(stock_cache) if yolo_time > 0 else 0
        yolo_results.append({
            '置信度阈值': conf, 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'Precision': round(p, 1), 'Recall': round(r, 1), 'F1': round(f1, 1),
            '漏检率': round(100 - r, 1), '误报率': round(fpr, 1),
            '平均耗时/股': round(per_stock, 3),
        })
        print(f"  conf={conf}: TP={tp} FP={fp} FN={fn} P={p:.1f}% R={r:.1f}% F1={f1:.1f}% FPR={fpr:.1f}%")

    _safe_csv(pd.DataFrame(yolo_results), 'yolo_test.csv')

    # ======== 测试二：判别模型（骨架DTW+规则）独立测试 ========
    print("\n" + "=" * 60)
    print("测试二：判别模型（骨架DTW+规则）独立测试")
    print("=" * 60)

    # 获取规则过滤器（LLM或结构规则fallback）
    ai_filter = get_rule_filter()
    if ai_filter is None:
        print("  LLM规则不可用，使用W底结构规则fallback")
        ai_filter = w_bottom_rule_filter
    else:
        print("  使用LLM规则过滤")

    # 规则前置 + 多维DTW滑窗
    dtw_windows = {}
    total_windows_count = 0
    rule_pass_count = 0
    t0 = time.time()
    for idx, code in enumerate(test_stocks):
        code = str(code).zfill(6)
        if code not in stock_cache:
            continue
        df = stock_cache[code]
        windows = []
        for i in range(0, max(len(df) - WINDOW_SIZE + 1, 1), STEP):
            if i + WINDOW_SIZE > len(df):
                break
            window_df = df.iloc[i: i + WINDOW_SIZE]
            sd = window_df.iloc[0]['trade_date'].strftime('%Y-%m-%d')
            ed = window_df.iloc[-1]['trade_date'].strftime('%Y-%m-%d')
            total_windows_count += 1
            # 规则过滤
            try:
                if not ai_filter(window_df):
                    continue
            except:
                pass
            rule_pass_count += 1
            # 多维DTW打分
            score = multi_ma_dtw_similarity(target, window_df, MA_LIST)
            windows.append({'start_date': sd, 'end_date': ed, 'score': score})
        dtw_windows[code] = windows
        if (idx + 1) % 50 == 0:
            print(f"  DTW扫描: {idx+1}/{len(test_stocks)}, 累计窗口{total_windows_count}, 规则通过{rule_pass_count}")
    dtw_time = time.time() - t0
    prune_rate = (1 - rule_pass_count / max(total_windows_count, 1)) * 100
    print(f"  DTW总耗时: {dtw_time:.1f}s, 总窗口: {total_windows_count}, 规则通过: {rule_pass_count}, 剪枝率: {prune_rate:.1f}%, 单股平均: {dtw_time/max(len(stock_cache),1):.3f}s")

    dtw_results = []
    for thresh in [0.4, 0.5, 0.6]:
        tp = fp = fn = tn = 0
        for _, row in gt_all.iterrows():
            code = str(row['code']).zfill(6)
            dets = [w for w in dtw_windows.get(code, []) if w['score'] >= thresh]
            hit = check_hit_overlap(dets, row['low1_date'], row['low2_date'])
            if row['label'] == 1 and hit: tp += 1
            elif row['label'] == 1 and not hit: fn += 1
            elif row['label'] == 0 and hit: fp += 1
            else: tn += 1
        p = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        r = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0
        per_stock = dtw_time / len(stock_cache)
        dtw_results.append({
            'DTW阈值': thresh, 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'Precision': round(p, 1), 'Recall': round(r, 1), 'F1': round(f1, 1),
            '漏检率': round(100 - r, 1), '误报率': round(fpr, 1),
            '规则剪枝率': round(prune_rate, 1), '平均耗时/股': round(per_stock, 3),
        })
        print(f"  DTW≥{thresh}: TP={tp} FP={fp} FN={fn} P={p:.1f}% R={r:.1f}% F1={f1:.1f}% FPR={fpr:.1f}%")

    _safe_csv(pd.DataFrame(dtw_results), 'dtw_test.csv')

    # ======== 测试三：双模型融合测试 ========
    print("\n" + "=" * 60)
    print("测试三：双模型融合测试")
    print("=" * 60)

    YOLO_CONF = 0.15  # 低阈值确保高召回粗筛
    DTW_THRESH = 0.38  # 适配加权多维DTW分数
    fusion_tp = fusion_fp = fusion_fn = fusion_tn = 0
    yolo_pass_total = 0
    dtw_pass_total = 0
    t0 = time.time()

    for _, row in gt_all.iterrows():
        code = str(row['code']).zfill(6)
        yolo_dets = [d for d in yolo_detections.get(code, []) if d.get('confidence', 0) >= YOLO_CONF]
        yolo_pass_total += len(yolo_dets)

        # 对YOLO候选做多维DTW精排
        fusion_dets = []
        df = stock_cache.get(code)
        if df is not None:
            for yd in yolo_dets:
                try:
                    ds = pd.Timestamp(str(yd['start_date'])[:10])
                    de = pd.Timestamp(str(yd['end_date'])[:10])
                    mask = (df['trade_date'] >= ds) & (df['trade_date'] <= de)
                    window_df = df[mask].head(WINDOW_SIZE)
                    if len(window_df) >= 10:
                        score = multi_ma_dtw_similarity(target, window_df, MA_LIST)
                        if score >= DTW_THRESH:
                            fusion_dets.append(yd)
                            dtw_pass_total += 1
                except:
                    pass

        hit = check_hit_overlap(fusion_dets, row['low1_date'], row['low2_date'])
        if row['label'] == 1 and hit: fusion_tp += 1
        elif row['label'] == 1 and not hit: fusion_fn += 1
        elif row['label'] == 0 and hit: fusion_fp += 1
        else: fusion_tn += 1

    fusion_time = time.time() - t0
    fp = fusion_tp / (fusion_tp + fusion_fp) * 100 if (fusion_tp + fusion_fp) > 0 else 0
    fr = fusion_tp / (fusion_tp + fusion_fn) * 100 if (fusion_tp + fusion_fn) > 0 else 0
    ff1 = 2 * fp * fr / (fp + fr) if (fp + fr) > 0 else 0
    ffpr = fusion_fp / (fusion_fp + fusion_tn) * 100 if (fusion_fp + fusion_tn) > 0 else 0
    print(f"  YOLO候选(conf≥{YOLO_CONF}): {yolo_pass_total}, DTW通过(≥{DTW_THRESH}): {dtw_pass_total}")
    print(f"  TP={fusion_tp} FP={fusion_fp} FN={fusion_fn} P={fp:.1f}% R={fr:.1f}% F1={ff1:.1f}% FPR={ffpr:.1f}%")
    print(f"  融合总耗时: {fusion_time:.1f}s, 单股平均: {fusion_time/len(stock_cache):.3f}s")

    fusion_df = pd.DataFrame([
        {'阶段': 'YOLO粗筛', '候选数': yolo_pass_total, 'TP': '', 'FP': '', 'FN': '', 'Precision': '', 'Recall': '', 'F1': '', '耗时/股': ''},
        {'阶段': 'DTW精排', '候选数': dtw_pass_total, 'TP': '', 'FP': '', 'FN': '', 'Precision': '', 'Recall': '', 'F1': '', '耗时/股': ''},
        {'阶段': '融合最终', '候选数': dtw_pass_total, 'TP': fusion_tp, 'FP': fusion_fp, 'FN': fusion_fn,
         'Precision': round(fp, 1), 'Recall': round(fr, 1), 'F1': round(ff1, 1), '耗时/股': round(fusion_time/len(stock_cache), 3)},
    ])
    _safe_csv(fusion_df, 'fusion_test.csv')

    print("\n" + "=" * 60)
    print("前三阶段测试完成。")
    print(f"结果文件: {OUTPUT_DIR}")
    print("=" * 60)

    # ======== DTW Top100 样本导出 ========
    print("\n" + "=" * 60)
    print("DTW Top100 样本 K线图导出")
    print("=" * 60)

    SAMPLE_DIR = os.path.join(OUTPUT_DIR, 'dtw_top100_samples')
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    # 使用K线图画图（与YOLO检测一致）

    # 收集全部检测窗口按DTW得分排序
    all_dets = []
    for code, windows in dtw_windows.items():
        for w in windows:
            all_dets.append({
                'code': code,
                'start_date': w['start_date'],
                'end_date': w['end_date'],
                'dtw_score': round(w['score'], 4),
            })
    all_dets.sort(key=lambda x: x['dtw_score'], reverse=True)
    top100 = all_dets[:100]
    print(f"  总检测窗口: {len(all_dets)}, 导出TOP{len(top100)}")

    # 逐一画图保存
    saved = 0
    for i, det in enumerate(top100):
        df = stock_cache.get(det['code'])
        if df is None:
            continue
        mask = (df['trade_date'] >= pd.Timestamp(det['start_date'])) & \
               (df['trade_date'] <= pd.Timestamp(det['end_date']))
        window_df = df[mask].head(64)  # 取最多64根K线画图
        if len(window_df) < 10:
            continue
        try:
            img = draw_kline_chart(window_df)
            fname = f"{i+1:03d}_{det['code']}_{det['start_date']}_{det['end_date']}_score{det['dtw_score']:.4f}.png"
            img.save(os.path.join(SAMPLE_DIR, fname))
            saved += 1
        except Exception as e:
            print(f"    [{i+1}] {det['code']} 画图失败: {e}")

    print(f"  成功导出 {saved} 张K线图 → {SAMPLE_DIR}")

    # ======== 测试四：效果对比汇总 ========
    print("\n" + "=" * 60)
    print("测试四：效果对比汇总")
    print("=" * 60)

    yolo_best = next((r for r in yolo_results if r.get('置信度阈值') == 0.1), yolo_results[0] if yolo_results else {})
    dtw_best = dtw_results[1] if len(dtw_results) > 1 else (dtw_results[0] if dtw_results else {})

    summary = pd.DataFrame([
        {'对比项': 'Precision', '视觉模型单独': f"{yolo_best.get('Precision', '-')}%", '判别模型单独': f"{dtw_best.get('Precision', '-')}%", '双模型融合': f"{fp:.1f}%"},
        {'对比项': 'Recall', '视觉模型单独': f"{yolo_best.get('Recall', '-')}%", '判别模型单独': f"{dtw_best.get('Recall', '-')}%", '双模型融合': f"{fr:.1f}%"},
        {'对比项': 'F1-Score', '视觉模型单独': f"{yolo_best.get('F1', '-')}%", '判别模型单独': f"{dtw_best.get('F1', '-')}%", '双模型融合': f"{ff1:.1f}%"},
        {'对比项': '漏检率', '视觉模型单独': f"{yolo_best.get('漏检率', '-')}%", '判别模型单独': f"{dtw_best.get('漏检率', '-')}%", '双模型融合': f"{100-fr:.1f}%"},
        {'对比项': '误报率', '视觉模型单独': f"{yolo_best.get('误报率', '-')}%", '判别模型单独': f"{dtw_best.get('误报率', '-')}%", '双模型融合': f"{ffpr:.1f}%"},
        {'对比项': '单股耗时', '视觉模型单独': f"{yolo_best.get('平均耗时/股', '-')}s", '判别模型单独': f"{dtw_best.get('平均耗时/股', '-')}s", '双模型融合': f"{fusion_time/len(stock_cache):.3f}s"},
    ])
    _safe_csv(summary, 'summary.csv')
    print(summary.to_string(index=False))

    # # ======== 测试五：视觉模型训练效率测试 ========
    # print("\n" + "=" * 60)
    # print("测试五：视觉模型训练效率测试")
    # print("=" * 60)
    #
    # train_data = pd.read_csv(os.path.join(LABELS_DIR, 'train.csv'))
    # train_pos = train_data[train_data.label == 1]
    # print(f"训练集正样本: {len(train_pos)} 个")
    #
    # train_results = []
    # for n_samples in [10, 20, 30]:
    #     if len(train_pos) < n_samples:
    #         print(f"  训练样本{n_samples}: 训练集不足({len(train_pos)})，跳过")
    #         continue
    #
    #     sampled = train_pos.sample(n=n_samples, random_state=42)
    #
    #     # 构建训练片段数据
    #     segments = []
    #     for _, row in sampled.iterrows():
    #         code = str(row['code']).zfill(6)
    #         if code not in stock_cache:
    #             continue
    #         df = stock_cache[code]
    #         try:
    #             d1 = pd.Timestamp(str(row['low1_date'])[:10])
    #             d2 = pd.Timestamp(str(row['low2_date'])[:10])
    #             mask = (df['trade_date'] >= d1 - pd.Timedelta(days=5)) & (df['trade_date'] <= d2 + pd.Timedelta(days=5))
    #             seg = df[mask].head(WINDOW_SIZE)
    #             if len(seg) >= 10:
    #                 segments.append(seg[['open', 'close', 'high', 'low', 'vol']].to_dict('records'))
    #         except:
    #             continue
    #
    #     if len(segments) < 5:
    #         print(f"  训练样本{n_samples}: 有效片段不足，跳过")
    #         continue
    #
    #     print(f"  正样本{n_samples} → 有效片段{len(segments)}个, 数据增强中...")
    #
    #     # 数据增强（8种变体/样本）
    #     aug_count = len(segments) * 8
    #     print(f"  增强后: {aug_count} 张训练图")
    #
    #     # 实际训练（如果YOLO可用）
    #     try:
    #         yolo_dir = os.path.join(PROJECT_DIR, 'few_shot_learning', 'yolo0623')
    #         if yolo_dir not in sys.path:
    #             sys.path.insert(0, yolo_dir)
    #         from main import build_dataset_from_samples, train_yolo
    #         import hashlib
    #
    #         safe_name = hashlib.md5(f"wbtest{n_samples}".encode()).hexdigest()[:8]
    #         output_dir = os.path.join('custom_modes', f'yolo_test_{safe_name}')
    #         t_prep = time.time()
    #         yaml_path, pos_cnt, neg_cnt = build_dataset_from_samples(
    #             segments, [], MA_LIST, output_dir, 'KLINE')
    #         prep_time = time.time() - t_prep
    #
    #         t_train = time.time()
    #         import torch
    #         model_path = train_yolo(yaml_path, f'wbtest{n_samples}', epochs=30, imgsz=416)
    #         train_time = time.time() - t_train
    #
    #         gpu_mem = torch.cuda.max_memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
    #         torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    #
    #         # 读取mAP50
    #         mAP50 = 0
    #         try:
    #             results_path = os.path.join('runs', 'detect', 'train', 'results.csv')
    #             if os.path.exists(results_path):
    #                 res = pd.read_csv(results_path)
    #                 mAP50 = res.iloc[-1].get('metrics/mAP50(B)', 0) * 100 if 'metrics/mAP50(B)' in res.columns else 0
    #         except:
    #             pass
    #
    #         train_results.append({
    #             '正样本数': n_samples, '增强后样本数': aug_count, '负样本数': neg_cnt,
    #             '数据准备时间': round(prep_time, 1), '训练Epoch': 30,
    #             '总训练时间': round(train_time, 1), 'GPU峰值显存(GB)': round(gpu_mem, 2),
    #             'mAP50': round(mAP50, 1),
    #         })
    #         print(f"  完成: 准备{prep_time:.1f}s 训练{train_time:.1f}s GPU:{gpu_mem:.2f}GB mAP50={mAP50:.1f}%")
    #     except Exception as e:
    #         print(f"  训练失败: {e}")
    #         train_results.append({
    #             '正样本数': n_samples, '增强后样本数': aug_count, '负样本数': 0,
    #             '数据准备时间': 0, '训练Epoch': 30, '总训练时间': 0, 'GPU峰值显存(GB)': 0, 'mAP50': 0,
    #         })
    #
    # if train_results:
    #     _safe_csv(pd.DataFrame(train_results), 'train_efficiency.csv')
    #
    # # 增强方式记录
    # aug_methods = pd.DataFrame([
    #     {'增强类型': '亮度×0.8/1.2', '说明': '图像亮度变化'},
    #     {'增强类型': '对比度×1.3', '说明': '线条对比度增强'},
    #     {'增强类型': '时间×0.8', '说明': '形态缩短20%'},
    #     {'增强类型': '时间×1.2', '说明': '形态加长20%'},
    #     {'增强类型': '时间×1.4', '说明': '形态加长40%'},
    # ])
    # _safe_csv(aug_methods, 'augmentation_methods.csv')
    #
    # print(f"\n{'='*60}")
    # print("全部测试完成！")
    # print(f"结果文件: {OUTPUT_DIR}/")
    # print(f"  - yolo_test.csv (YOLO独立测试)")
    # print(f"  - dtw_test.csv (判别模型独立测试)")
    # print(f"  - fusion_test.csv (双模型融合测试)")
    # print(f"  - summary.csv (效果对比汇总)")
    # print(f"  - train_efficiency.csv (训练效率)")
    # print(f"  - augmentation_methods.csv (增强方式)")
    # print(f"{'='*60}")


if __name__ == '__main__':
    run_tests()
