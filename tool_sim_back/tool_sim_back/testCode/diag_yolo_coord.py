"""YOLO 坐标映射诊断脚本 —— 追踪像素bbox→索引→日期 转换链"""
import json
import os
import sys
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_DIR = os.path.join(os.path.dirname(PROJECT_DIR), 'test_data')
OUTPUT_DIR = os.path.join(os.path.dirname(PROJECT_DIR), 'test_output', 'yolo_vis')

from few_shot_learning.yolo0623.chart_renderer import render_kline_image
from few_shot_learning.yolo0623.main import load_yolo_model, generate_training_chart, INFERENCE_DAYS_PER_IMAGE, INFERENCE_OVERLAP_DAYS
from test_pipeline_common import load_stock, MA_LIST, check_hit_overlap, LABELS_DIR

MODE_NAME = 'wbtest_kline_20260723'
IMG_SIZE = 416

def diagnose():
    # 加载标注数据
    labels = pd.read_csv(os.path.join(LABELS_DIR, 'all_labeled.csv'))
    positives = labels[labels.label == 1]

    # 加载已有YOLO缓存，找哪些正样本被检测到了，哪些没检测到
    with open(os.path.join(os.path.dirname(PROJECT_DIR), 'test_output', 'yolo_detections.json'), encoding='utf-8') as f:
        cache = json.load(f)

    # 统计每个正样本是否被YOLO检出
    yolo_dets = cache['detections']
    hit_codes = set()
    missed = []
    for _, row in positives.iterrows():
        code = str(row['code']).zfill(6)
        dets = yolo_dets.get(code, [])
        hit = check_hit_overlap(dets, row['low1_date'], row['low2_date'])
        if hit:
            hit_codes.add(code)
        else:
            missed.append(row)

    total_pos = len(positives)
    hit_count = sum(1 for _, row in positives.iterrows() if check_hit_overlap(
        yolo_dets.get(str(row['code']).zfill(6), []), row['low1_date'], row['low2_date']))
    print(f"YOLO检出: {hit_count}/{total_pos} ({100*hit_count/total_pos:.1f}%)")
    print(f"未检出: {len(missed)}")

    # 选5个未检出的样本做深度诊断
    np.random.seed(123)
    indices = np.random.choice(len(missed), min(5, len(missed)), replace=False)
    samples = [missed[i] for i in indices]

    model = load_yolo_model(MODE_NAME)
    if model is None:
        print("无法加载YOLO模型!")
        return

    os.makedirs(os.path.join(OUTPUT_DIR, 'diag'), exist_ok=True)

    for idx, row in enumerate(samples):
        code = str(row['code']).zfill(6)
        low1_date = str(row['low1_date'])[:10]
        low2_date = str(row['low2_date'])[:10]
        print(f"\n{'='*60}")
        print(f"样本 {idx+1}: {code}  GT: {low1_date} ~ {low2_date}")
        print(f"{'='*60}")

        df = load_stock(code)
        if df is None:
            print("  股票数据加载失败")
            continue

        # 找到GT low1/low2在df中的索引
        low1_idx = df[df['trade_date'] == pd.Timestamp(low1_date)].index
        low2_idx = df[df['trade_date'] == pd.Timestamp(low2_date)].index
        if len(low1_idx) == 0 or len(low2_idx) == 0:
            print(f"  GT日期不在数据中! low1_idx={len(low1_idx)}, low2_idx={len(low2_idx)}")
            continue
        low1_idx = low1_idx[0]
        low2_idx = low2_idx[0]
        print(f"  GT索引: low1={low1_idx}, low2={low2_idx}, 跨度={low2_idx-low1_idx}天")

        # 找哪个150天chunk包含了这个W底
        # 推理用的INFERENCE_DAYS_PER_IMAGE=225, but we used 150
        days_per_image = cache.get('days_per_image', 150)
        overlap = cache.get('overlap_days', 50)
        step = max(days_per_image - overlap, 1)

        # 计算chunks
        wb_center = (low1_idx + low2_idx) // 2
        best_chunk_start = max(0, wb_center - days_per_image // 2)
        best_chunk_start = min(best_chunk_start, max(0, len(df) - days_per_image))

        print(f"  W底中心索引: {wb_center}")
        print(f"  最佳chunk_start: {best_chunk_start}")

        # 用最佳chunk渲染图像并用YOLO检测
        chunk_df = df.iloc[best_chunk_start:best_chunk_start + days_per_image].reset_index(drop=True)
        print(f"  Chunk实际行数: {len(chunk_df)}")

        img = generate_training_chart(chunk_df, img_size=IMG_SIZE)

        # YOLO检测
        results = model([img], conf=0.15, verbose=False)
        pred = results[0]

        if pred.boxes is None:
            print("  YOLO: 未检出任何目标!")
            # 也画图看看
            img.save(os.path.join(OUTPUT_DIR, 'diag', f'diag_{idx+1}_{code}_nodet.png'))
            print(f"  已保存无检测图: yolo_vis/diag/diag_{idx+1}_{code}_nodet.png")
            continue

        boxes = pred.boxes
        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        print(f"  YOLO检出: {len(boxes)} 个框")

        # 在图上画出GT区域和YOLO检出框
        draw_img = img.copy()
        draw = ImageDraw.Draw(draw_img)

        n_bars = len(chunk_df)
        x_step = IMG_SIZE / n_bars

        # 画GT区域（绿色）
        gt_rel_start = low1_idx - best_chunk_start
        gt_rel_end = low2_idx - best_chunk_start
        gt_x1 = int(gt_rel_start * x_step)
        gt_x2 = int((gt_rel_end + 1) * x_step)
        draw.rectangle([gt_x1, 5, gt_x2, IMG_SIZE - 5], outline=(0, 255, 0), width=2)
        draw.text((gt_x1, 0), f'GT {low1_date}', fill=(0, 255, 0))

        for bi, (box_xyxy, conf) in enumerate(zip(xyxy, confs)):
            x1, y1, x2, y2 = box_xyxy

            # 像素→索引转换（和_collect_yolo_predictions完全一致）
            length = n_bars
            idx_start = max(0, min(int(x1 / IMG_SIZE * length), length - 1))
            idx_end = max(idx_start + 5, min(int(x2 / IMG_SIZE * length), length - 1))

            global_start = best_chunk_start + idx_start
            global_end = best_chunk_start + idx_end

            det_start_date = str(df.iloc[global_start]['trade_date'])[:10]
            det_end_date = str(df.iloc[global_end]['trade_date'])[:10]

            # 检查overlap
            hit = check_hit_overlap(
                [{'start_date': det_start_date, 'end_date': det_end_date}],
                low1_date, low2_date
            )

            print(f"  框{bi+1}: 像素[{x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}] conf={conf:.4f}")
            print(f"         索引[{idx_start},{idx_end}] 全局[{global_start},{global_end}]")
            print(f"         日期[{det_start_date}~{det_end_date}] {'✓ 命中' if hit else '✗ 未命中'}")
            print(f"         GT [{low1_date}~{low2_date}] (索引{low1_idx}~{low2_idx})")

            # 画YOLO框（红色=未命中，蓝色=命中）
            color = (0, 0, 255) if hit else (255, 0, 0)
            draw.rectangle([int(x1), int(y1), int(x2), int(y2)], outline=color, width=2)
            label = f'{conf:.2f} {"HIT" if hit else "MISS"}'
            draw.text((int(x1), max(int(y1)-15, 0)), label, fill=color)

        fname = f'diag_{idx+1}_{code}.png'
        draw_img.save(os.path.join(OUTPUT_DIR, 'diag', fname))
        print(f"  已保存诊断图: yolo_vis/diag/{fname}")

if __name__ == '__main__':
    diagnose()
