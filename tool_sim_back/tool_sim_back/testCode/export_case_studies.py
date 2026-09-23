"""Export 5 case-study K-line charts with YOLO bbox + DTW score annotation."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

from test_pipeline_common import OUTPUT_DIR, load_evaluation_labels, load_stock_cache, check_hit_overlap

CASE_COUNT = 5
CONTEXT_DAYS = 60
BOX_COLOR = '#FF0000'


def draw_case_chart(df, bbox_start, bbox_end, code, confidence, dtw_score, out_path):
    """Draw K-line chart with YOLO red bbox overlay and annotation header."""
    n = len(df)
    dpi = 150
    fig_w = CONTEXT_DAYS * 0.15
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * 0.75), dpi=dpi)

    x_arr = np.arange(n)
    up = df[df.close >= df.open]
    down = df[df.close < df.open]
    body_w = 0.65
    wick_w = 0.12

    if not up.empty:
        ax.bar(up.index, up.close.values - up.open.values,
               bottom=up.open.values, color='red', width=body_w)
        ax.bar(up.index, up.high.values - up.close.values,
               bottom=up.close.values, color='red', width=wick_w)
        ax.bar(up.index, up.low.values - up.open.values,
               bottom=up.open.values, color='red', width=wick_w)
    if not down.empty:
        ax.bar(down.index, down.open.values - down.close.values,
               bottom=down.close.values, color='green', width=body_w)
        ax.bar(down.index, down.high.values - down.open.values,
               bottom=down.open.values, color='green', width=wick_w)
        ax.bar(down.index, down.low.values - down.close.values,
               bottom=down.close.values, color='green', width=wick_w)

    y_min, y_max = df.low.min(), df.high.max()
    y_range = y_max - y_min
    ax.set_ylim(y_min - y_range * 0.15, y_max + y_range * 0.1)
    ax.set_xlim(-0.5, n - 0.5)

    rect = patches.Rectangle(
        (bbox_start - 0.5, y_min - y_range * 0.05),
        bbox_end - bbox_start + 1, y_range * 1.1,
        linewidth=2, edgecolor=BOX_COLOR, facecolor='none', linestyle='-', zorder=10
    )
    ax.add_patch(rect)

    title = f'Code: {code} | Confidence: {confidence:.2f} | DTW Score: {dtw_score:.4f}'
    ax.set_title(title, fontsize=10, fontweight='bold', pad=8, color='#333333')

    ax.axis('off')
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor='white', pad_inches=0.1)
    plt.close(fig)
    return out_path


def main():
    detections_path = os.path.join(OUTPUT_DIR, 'fusion_detections.csv')
    df_dets = pd.read_csv(detections_path)
    print(f'fusion_detections: {len(df_dets)} entries')

    stock_cache = load_stock_cache()
    labels = load_evaluation_labels(stock_cache)

    # Find true positives: detections that overlap with a labeled W-bottom
    tp_list = []
    for _, det_row in df_dets.iterrows():
        code = str(int(det_row['code'])).zfill(6)
        if code not in stock_cache:
            continue
        start_date = str(det_row['start_date'])[:10]
        end_date = str(det_row['end_date'])[:10]
        stock_labels = labels[(labels.code.astype(str).str.zfill(6) == code) & (labels.label == 1)]
        for _, lbl in stock_labels.iterrows():
            hit = check_hit_overlap([{'start_date': start_date, 'end_date': end_date}],
                                     lbl.low1_date, lbl.low2_date)
            if hit:
                tp_list.append({
                    'code': code,
                    'confidence': det_row['confidence'],
                    'dtw_score': det_row['dtw_score'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'start_idx': int(det_row['start_idx']),
                    'end_idx': int(det_row['end_idx']),
                    'label_low1': str(lbl.low1_date)[:10],
                    'label_low2': str(lbl.low2_date)[:10],
                })
                break

    print(f'TP detections found: {len(tp_list)} (from {len(stock_cache)} valid stocks)')

    tp_sorted = sorted(tp_list, key=lambda x: x['confidence'], reverse=True)
    if len(tp_sorted) > CASE_COUNT:
        indices = np.linspace(0, len(tp_sorted) - 1, CASE_COUNT, dtype=int)
        selected = [tp_sorted[i] for i in indices]
    else:
        selected = tp_sorted[:CASE_COUNT]

    case_dir = os.path.join(OUTPUT_DIR, 'case_studies')
    for i, item in enumerate(selected):
        code = item['code']
        df = stock_cache.get(code)
        if df is None:
            print(f'  skip {code}: not in cache')
            continue

        g_start = item['start_idx']
        g_end = item['end_idx']
        center = (g_start + g_end) // 2
        ctx_start = max(0, min(center - CONTEXT_DAYS // 2, len(df) - CONTEXT_DAYS))
        ctx_end = ctx_start + CONTEXT_DAYS
        if ctx_end > len(df):
            ctx_start = len(df) - CONTEXT_DAYS
            ctx_end = len(df)
        ctx = df.iloc[ctx_start:ctx_end].copy().reset_index(drop=True)

        rel_start = g_start - ctx_start
        rel_end = g_end - ctx_start
        rel_start = max(0, min(rel_start, CONTEXT_DAYS - 1))
        rel_end = max(rel_start + 3, min(rel_end, CONTEXT_DAYS - 1))

        out_name = f'case_{i+1:02d}_{code}_conf{item["confidence"]:.2f}.png'
        out_path = os.path.join(case_dir, out_name)
        draw_case_chart(ctx, rel_start, rel_end, code, item['confidence'], item['dtw_score'], out_path)
        print(f'  [{i+1}/{CASE_COUNT}] {out_name}  conf={item["confidence"]:.2f}  dtw={item["dtw_score"]:.4f}')

    print(f'Case studies saved to: {case_dir}')


if __name__ == '__main__':
    main()
