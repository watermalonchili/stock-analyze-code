"""YOLO W底检测结果可视化 → HTML网页"""
import json
import os
import sys
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(os.path.dirname(PROJECT_DIR), 'test_output', 'yolo_vis')
os.makedirs(OUTPUT_DIR, exist_ok=True)

from few_shot_learning.yolo0623.chart_renderer import render_kline_image
from test_pipeline_common import load_stock_cache, load_evaluation_labels, check_hit_overlap, LABELS_DIR, TEST_DATA_DIR

MIN_CONF = 0.3

def draw_bbox(img, start_idx, end_idx, conf, img_size=416):
    """在K线图上画检测框"""
    overlay = img.copy()
    draw = ImageDraw.Draw(overlay)
    n_days = 225  # 每张图固定225天
    x_step = img_size / n_days
    x1 = max(0, round(start_idx * x_step))
    x2 = min(img_size - 1, round(end_idx * x_step))
    # 画半透明红色矩形框
    draw.rectangle([x1, 2, x2, img_size - 3], outline=(255, 0, 0, 200), width=2)
    # 顶部标置信度
    label = f'{conf:.2f}'
    draw.rectangle([x1, 0, x1 + 40, 14], fill=(255, 0, 0))
    draw.text((x1 + 2, 1), label, fill=(255, 255, 255))
    # 50%透明度混合
    return Image.blend(img, overlay, 0.5) if conf < 0.7 else overlay

def generate():
    print("加载数据...")
    with open(os.path.join(os.path.dirname(PROJECT_DIR), 'test_output', 'yolo_detections.json'), encoding='utf-8') as f:
        cache = json.load(f)

    stock_cache = load_stock_cache()
    labels = load_evaluation_labels(stock_cache)
    gt_pos = labels[labels.label == 1]

    # 收集所有 detections 并去重 (同code+同start_idx)
    all_dets = []
    seen = set()
    for code, dets in cache['detections'].items():
        for d in dets:
            if d['confidence'] < MIN_CONF:
                continue
            key = (code, d['start_idx'])
            if key in seen:
                continue
            seen.add(key)
            all_dets.append((code, d))

    # 按置信度降序排列
    all_dets.sort(key=lambda x: x[1]['confidence'], reverse=True)
    print(f"检测结果(conf≥{MIN_CONF}): {len(all_dets)} 个 (去重后)")

    # 生成图片
    groups = {}  # code -> [(det, is_tp, img_path)]
    tp_count = fp_count = 0

    for i, (code, det) in enumerate(all_dets):
        df = stock_cache.get(str(code).zfill(6))
        if df is None:
            continue
        start_idx = det['start_idx']
        end_idx = det['end_idx']
        # 取从 start_idx 往前到 225 天的那段数据
        img_start = max(0, end_idx - 225)  # 以检测框尾部为基准倒推
        if img_start + 225 > len(df):
            img_start = max(0, len(df) - 225)
        if start_idx < img_start or end_idx >= img_start + 225:
            # 调整：以 start_idx 为中心
            center = (start_idx + end_idx) // 2
            img_start = max(0, min(center - 112, len(df) - 225))
        window = df.iloc[img_start:img_start + 225].reset_index(drop=True)
        if len(window) < 50:
            continue

        img = render_kline_image(window, img_size=416)
        relative_start = start_idx - img_start
        relative_end = end_idx - img_start
        img = draw_bbox(img, relative_start, relative_end, det['confidence'])

        # 判断TP/FP
        det_info = {
            'start_date': window.iloc[max(0, relative_start)]['trade_date'].strftime('%Y-%m-%d') if 0 <= relative_start < len(window) else '',
            'end_date': window.iloc[min(relative_end, len(window)-1)]['trade_date'].strftime('%Y-%m-%d') if 0 <= relative_end < len(window) else '',
        }
        is_tp = False
        for _, row in gt_pos.iterrows():
            if str(row['code']).zfill(6) == str(code).zfill(6):
                if check_hit_overlap([det_info], row['low1_date'], row['low2_date']):
                    is_tp = True
                    break
        if is_tp:
            tp_count += 1
            tag = 'TP'
        else:
            fp_count += 1
            tag = 'FP'

        fname = f"{i+1:04d}_{code}_{tag}_{det['confidence']:.3f}.png"
        img.save(os.path.join(OUTPUT_DIR, fname))
        groups.setdefault(code, []).append((det, is_tp, fname))

        if (i + 1) % 50 == 0:
            print(f"  生成图片: {i+1}/{len(all_dets)}")

    print(f"完成: TP={tp_count} FP={fp_count}, 图片保存到 {OUTPUT_DIR}")

    # 生成HTML
    html_parts = [f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YOLO W底检测可视化</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; }}
.header {{ background: linear-gradient(135deg, #16213e, #0f3460); padding: 20px 30px; position: sticky; top: 0; z-index: 100; }}
.header h1 {{ font-size: 1.5em; }}
.stats {{ display: flex; gap: 20px; margin-top: 10px; }}
.stat {{ background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 8px; }}
.stat .val {{ font-size: 1.3em; font-weight: bold; }}
.tp {{ color: #00e676; }}
.fp {{ color: #ff5252; }}
.controls {{ padding: 15px 30px; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }}
.controls button, .controls select {{ padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; }}
.btn-tp {{ background: #00e676; color: #000; }}
.btn-fp {{ background: #ff5252; color: #fff; }}
.btn-all {{ background: #448aff; color: #fff; }}
.gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 15px; padding: 15px 30px; }}
.card {{ background: #16213e; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
.card.tp-card {{ border-left: 4px solid #00e676; }}
.card.fp-card {{ border-left: 4px solid #ff5252; }}
.card img {{ width: 100%; display: block; }}
.card .info {{ padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; font-size: 0.85em; }}
.card .code {{ font-weight: bold; }}
.card .conf {{ padding: 3px 10px; border-radius: 4px; }}
.conf-high {{ background: #00e67633; color: #00e676; }}
.conf-mid {{ background: #ffab4033; color: #ffab40; }}
.card .tp-badge, .card .fp-badge {{ padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
.tp-badge {{ background: #00e67633; color: #00e676; }}
.fp-badge {{ background: #ff525233; color: #ff5252; }}
.no-results {{ text-align: center; padding: 50px; color: #666; }}
</style>
</head>
<body>
<div class="header">
<h1>YOLO W底检测结果可视化</h1>
<div class="stats">
<div class="stat"><div class="val">{len(all_dets)}</div>总检测</div>
<div class="stat"><div class="val tp">{tp_count}</div>命中(TP)</div>
<div class="stat"><div class="val fp">{fp_count}</div>误报(FP)</div>
<div class="stat"><div class="val">{MIN_CONF}</div>最低置信度</div>
</div>
</div>
<div class="controls">
<button class="btn-all" onclick="filter('all')">全部</button>
<button class="btn-tp" onclick="filter('tp')">命中 TP</button>
<button class="btn-fp" onclick="filter('fp')">误报 FP</button>
<select id="codeSelect" onchange="filterCode(this.value)">
<option value="">所有股票</option>
</select>
<select id="sortSelect" onchange="sortBy(this.value)">
<option value="conf">按置信度排序</option>
<option value="code">按股票代码排序</option>
</select>
</div>
<div class="gallery" id="gallery">
''']

    # 生成卡片
    cards = []
    for code, dets in groups.items():
        for det, is_tp, fname in dets:
            conf = det['confidence']
            conf_cls = 'conf-high' if conf >= 0.7 else 'conf-mid'
            card_cls = 'tp-card' if is_tp else 'fp-card'
            badge_html = '<span class="tp-badge">TP</span>' if is_tp else '<span class="fp-badge">FP</span>'
            cards.append({
                'html': f'''<div class="card {card_cls}" data-tp="{str(is_tp).lower()}" data-code="{code}" data-conf="{conf}">
<img src="{fname}" alt="{code}" loading="lazy">
<div class="info">
<span class="code">{code} {badge_html}</span>
<span>{det.get('start_date','')} ~ {det.get('end_date','')}</span>
<span class="conf {conf_cls}">conf={conf:.3f}</span>
</div>
</div>''',
                'code': code,
                'conf': conf,
            })

    html_parts.append('\n'.join(c['html'] for c in cards))

    # 股票下拉选项
    all_codes = sorted(set(c['code'] for c in cards))

    html_parts.append('''</div>
<div class="no-results" id="noResults" style="display:none">没有匹配结果</div>
<script>
function filter(type) {
document.querySelectorAll('.card').forEach(c => {
if (type === 'all') c.style.display = '';
else c.style.display = c.dataset.tp === type ? '' : 'none';
});
checkEmpty();
}
function filterCode(code) {
document.querySelectorAll('.card').forEach(c => {
c.style.display = !code || c.dataset.code === code ? '' : 'none';
});
}
function sortBy(mode) {
const gallery = document.getElementById('gallery');
const cards = [...gallery.children].filter(c => c.classList.contains('card'));
cards.sort((a, b) => mode === 'code' ? a.dataset.code.localeCompare(b.dataset.code) : parseFloat(b.dataset.conf) - parseFloat(a.dataset.conf));
cards.forEach(c => gallery.appendChild(c));
}
function checkEmpty() {
const visible = [...document.querySelectorAll('.card')].filter(c => c.style.display !== 'none').length;
document.getElementById('noResults').style.display = visible ? 'none' : '';
}
// 初始化下拉框
const codes = ''' + json.dumps(all_codes, ensure_ascii=False) + ''';
const sel = document.getElementById('codeSelect');
codes.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; sel.appendChild(o); });
</script>
</body></html>''')

    html_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(''.join(html_parts))
    print(f"HTML已生成: {html_path}")
    print(f"浏览器打开: file:///{html_path.replace(os.sep, '/')}")

if __name__ == '__main__':
    generate()
