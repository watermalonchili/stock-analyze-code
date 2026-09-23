import tushare as ts
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
from PIL import Image
import torch
from ultralytics import YOLO
import os
from pathlib import Path
import numpy as np
import math

app = Flask(__name__)
CORS(app, resources={r"/detect_bullish_arrangement": {
    "origins": ["http://localhost:8080"],
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

# 配置参数
ts.set_token('025198f4736f5b8f90f99903c08840a57f974daf1b1f78fe135f652e')  # 替换为你的Tushare Token
pro = ts.pro_api()

MODEL_PATH = "D:/self/code/vuecode/tool_ma_front/src/models/weights/best.pt"  # 训练好的YOLO模型路径
OUTPUT_DIR = "D:/self/code/vuecode/tool_ma_front/src/models/yolo_results"  # 检测结果保存目录

plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False

# 初始化YOLO模型（全局加载一次）
model = None
if os.path.exists(MODEL_PATH):
    model = YOLO(MODEL_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        print("YOLO模型已加载到GPU")
    else:
        print("YOLO模型将在CPU上运行")
else:
    print(f"错误：未找到模型文件 {MODEL_PATH}")

def get_stock_data(ts_code, start_date, end_date):
    """获取股票日线数据"""
    start = datetime.strptime(start_date, '%Y%m%d').strftime('%Y%m%d')
    end = datetime.strptime(end_date, '%Y%m%d').strftime('%Y%m%d')
    try:
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
        return df.sort_values('trade_date').reset_index(drop=True) if not df.empty else pd.DataFrame()
    except Exception as e:
        print(f"数据获取失败: {ts_code}, {e}")
        return pd.DataFrame()

def calculate_ma(data, ma_list):
    """计算均线数据"""
    for ma in ma_list:
        data[f'MA{ma}'] = data['close'].rolling(window=ma).mean()
    return data.dropna()

def generate_enhanced_long_chart(stock_code, ma_data, ma_list, window_size=21, stride=2, max_width=65536, max_height=65536, min_window_width=4, min_window_height=3, safety_margin=100, enhance_detection=True):
    """生成增强版的长图片，优化检测效果"""
    # 计算需要多少个窗口
    num_windows = math.ceil((len(ma_data) - window_size) / stride) + 1
    
    # 原始窗口尺寸（英寸）
    original_window_width = 12
    original_window_height = 8
    
    # 计算原始长图片尺寸（英寸）
    original_long_width = original_window_width * num_windows
    original_long_height = original_window_height
    
    # 计算最大允许的宽度（考虑安全余量）
    max_allowed_width = max_width - safety_margin
    
    # 计算缩放因子
    width_scale = min(1.0, max_allowed_width / (original_long_width * 300))  # 300是默认DPI
    height_scale = min(1.0, max_height / (original_long_height * 300))
    scale_factor = min(width_scale, height_scale)
    
    # 确保窗口不会太小
    scaled_window_width = original_window_width * scale_factor
    scaled_window_height = original_window_height * scale_factor
    
    # 如果窗口太小，进一步调整缩放因子
    if scaled_window_width < min_window_width:
        scale_factor = min_window_width / original_window_width
    if scaled_window_height < min_window_height:
        scale_factor = min_window_height / original_window_height
    
    # 重新计算缩放后的尺寸
    scaled_window_width = original_window_width * scale_factor
    scaled_window_height = original_window_height * scale_factor
    scaled_long_width = scaled_window_width * num_windows
    scaled_long_height = scaled_window_height
    
    # 调整DPI以控制最终像素尺寸
    # 使用严格向下取整的方式，确保最终宽度不超过限制
    adjusted_dpi = int(min(300, max_allowed_width / scaled_long_width))
    
    # 再次计算最终尺寸，确保不超过限制
    final_long_width = scaled_long_width
    final_long_height = scaled_long_height
    
    # 创建长图片画布
    fig = plt.figure(figsize=(final_long_width, final_long_height), dpi=adjusted_dpi)
    
    # 为每个窗口创建子图
    window_positions = []
    for i in range(num_windows):
        start_idx = i * stride
        end_idx = start_idx + window_size
        
        # 确保不超出数据范围
        if end_idx > len(ma_data):
            end_idx = len(ma_data)
            start_idx = end_idx - window_size
        
        if start_idx < 0:
            start_idx = 0
        
        window_data = ma_data.iloc[start_idx:end_idx]
        
        # 计算子图在长图片中的位置
        subplot_left = i * scaled_window_width / final_long_width
        subplot_bottom = 0
        subplot_width = scaled_window_width / final_long_width
        subplot_height = 1
        
        # 创建子图
        ax = fig.add_axes([subplot_left, subplot_bottom, subplot_width, subplot_height])
        
        # 增强检测效果：使用更粗的线条和更高的对比度
        line_width = max(1.5, 2 * scale_factor) if enhance_detection else 1.0
        
        # 绘制均线
        for ma in ma_list:
            ax.plot(window_data['trade_date'], window_data[f'MA{ma}'], label=f'{ma}日均线', linewidth=line_width)
        
        # 设置子图属性
        if enhance_detection:
            # 检测模式下，移除标题和网格以减少干扰
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
        else:
            # 正常模式下保留原始设置
            ax.set_title(f'{stock_code} 窗口 {i+1}', fontsize=max(6, 10 * scale_factor))
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_xticks([])
        
        # 保存窗口在长图片中的位置信息
        window_positions.append({
            'index': i,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'left': subplot_left,
            'bottom': subplot_bottom,
            'width': subplot_width,
            'height': subplot_height
        })
    
    # 添加图例
    if enhance_detection:
        # 检测模式下，图例放在单独的图片中
        fig_legend = plt.figure(figsize=(10, 2), dpi=adjusted_dpi)
        ax_legend = fig_legend.add_subplot(111)
        ax_legend.axis('off')
        handles, labels = ax.get_legend_handles_labels()
        ax_legend.legend(handles, labels, loc='center', ncol=len(ma_list), fontsize=10)
        
        # 保存图例图片
        legend_dir = os.path.join(OUTPUT_DIR, "legends")
        os.makedirs(legend_dir, exist_ok=True)
        legend_path = os.path.join(legend_dir, f"{stock_code}_legend.png")
        fig_legend.savefig(legend_path, dpi=adjusted_dpi, bbox_inches='tight')
        plt.close(fig_legend)
    else:
        # 正常模式下，图例放在图片中
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=len(ma_list), fontsize=max(6, 10 * scale_factor))
    
    # 保存长图片
    chart_type = "enhanced" if enhance_detection else "normal"
    long_chart_dir = os.path.join(OUTPUT_DIR, f"{chart_type}_long_charts")
    os.makedirs(long_chart_dir, exist_ok=True)
    date_range = f"{ma_data['trade_date'].iloc[0]}_to_{ma_data['trade_date'].iloc[-1]}"
    long_chart_path = os.path.join(long_chart_dir, f"{stock_code}_{date_range}_{chart_type}_ma.png")
    
    # 计算最终图片尺寸（像素）
    final_width_pixels = final_long_width * adjusted_dpi
    final_height_pixels = final_long_height * adjusted_dpi
    
    print(f"图片尺寸计算结果: {final_width_pixels}x{final_height_pixels} 像素")
    
    # 验证尺寸是否在限制范围内
    if final_width_pixels >= max_width or final_height_pixels >= max_height:
        raise ValueError(f"图片尺寸 {final_width_pixels}x{final_height_pixels} 仍然超出限制 {max_width}x{max_height}")
    
    plt.savefig(long_chart_path, dpi=adjusted_dpi, bbox_inches='tight')
    plt.close()
    
    return long_chart_path, window_positions, (final_long_width, final_long_height), adjusted_dpi

def detect_with_yolo(image_path, nms_threshold=0.3, conf_threshold=0.15):
    """使用YOLO模型检测图像，优化检测参数"""
    if not model:
        print("错误：未加载YOLO模型")
        return None
    
    # 调整检测参数
    results = model(image_path, conf=conf_threshold, iou=nms_threshold)
    
    # 保存检测结果图像
    save_dir = "D:/self/code/vuecode/tool_ma_front/public/detect_result"
    os.makedirs(save_dir, exist_ok=True)
    img_name = os.path.basename(image_path)
    save_path = os.path.join(save_dir, img_name)
    
    # 仅在检测到目标时保存结果图像
    has_detections = len(results[0].boxes) > 0 if hasattr(results[0], 'boxes') else False
    
    if has_detections:
        print(f"检测到 {len(results[0].boxes)} 个多头排列模式")
        results[0].save(save_path)
    
    return has_detections, save_path, results

def apply_nms(results, iou_threshold=0.3):
    """非极大值抑制 - 调整阈值以保留更多检测框"""
    for result in results:
        if hasattr(result, 'boxes') and result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()
            keep_indices = non_max_suppression(boxes, scores, iou_threshold)
            result.boxes = result.boxes[keep_indices]
    return results

def non_max_suppression(boxes, scores, iou_threshold=0.3):
    """NMS算法实现 - 调整阈值以保留更多检测框"""
    if len(boxes) == 0:
        return []
    
    boxes = np.array(boxes)
    scores = np.array(scores)
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= iou_threshold)[0]
        order = order[inds + 1]
    return keep

def check_ma_order(ma_data, ma_list):
    """检查均线是否满足多头排列条件"""
    ma_columns = [f'MA{ma}' for ma in ma_list]
    # 检查均线是否按从短期到长期的顺序排列
    ordered = True
    for i in range(len(ma_columns)-1):
        if not (ma_data[ma_columns[i]] > ma_data[ma_columns[i+1]]).all():
            ordered = False
            break
    
    # 检查均线是否呈上升趋势
    rising = True
    for ma in ma_columns:
        if not (ma_data[ma].iloc[-1] > ma_data[ma].iloc[0]):
            rising = False
            break
    
    return ordered and rising

def process_enhanced_image_detection(long_chart_path, window_positions, image_size_inches, dpi, ma_data, ma_list, conf_threshold=0.15):
    """处理增强版长图片上的检测结果，优化映射逻辑"""
    # 读取图像尺寸（像素）
    img_width_pixels = image_size_inches[0] * dpi
    img_height_pixels = image_size_inches[1] * dpi
    
    # 执行YOLO检测
    has_detections, detection_path, yolo_results = detect_with_yolo(long_chart_path)
    
    if not has_detections or not yolo_results[0].boxes:
        print(f"未检测到多头排列模式: {long_chart_path}")
        return []
    
    # 获取检测框
    boxes = yolo_results[0].boxes.xyxy.cpu().numpy()
    confidences = yolo_results[0].boxes.conf.cpu().numpy()
    
    # 存储多头排列的时间区间
    bullish_intervals = []
    
    # 遍历每个检测框
    for i, box in enumerate(boxes):
        confidence = float(confidences[i])
        if confidence < conf_threshold:  # 忽略低置信度检测
            continue
        
        # 获取检测框坐标（归一化到图像尺寸）
        x1, y1, x2, y2 = box
        x1_normalized = x1 / img_width_pixels
        x2_normalized = x2 / img_width_pixels
        
        # 找到检测框覆盖的窗口
        overlapping_windows = []
        for window in window_positions:
            window_left = window['left']
            window_right = window['left'] + window['width']
            
            # 检查窗口与检测框是否重叠
            if x1_normalized < window_right and x2_normalized > window_left:
                overlapping_windows.append(window)
        
        if not overlapping_windows:
            continue
        
        # 确定多头排列的起始和结束索引
        start_idx = min(window['start_idx'] for window in overlapping_windows)
        end_idx = max(window['end_idx'] for window in overlapping_windows)
        
        # 获取对应的日期范围
        start_date = ma_data['trade_date'].iloc[start_idx]
        end_date = ma_data['trade_date'].iloc[end_idx-1]
        
        # 检查均线数据是否也满足多头排列条件
        window_data = ma_data.iloc[start_idx:end_idx]
        is_bullish_by_data = check_ma_order(window_data, ma_list)
        
        print(f"检测到多头排列: {start_date} 至 {end_date}, 置信度: {confidence:.2f}, 窗口数: {len(overlapping_windows)}")
        
        bullish_intervals.append({
            "start": start_date,
            "end": end_date,
            "chart_path": detection_path,
            "confidence": confidence,
            "window_indices": [window['index'] for window in overlapping_windows],
            "is_bullish_by_data": is_bullish_by_data
        })
    
    # 按置信度排序
    bullish_intervals.sort(key=lambda x: x['confidence'], reverse=True)
    
    return bullish_intervals

@app.route('/detect_bullish_arrangement', methods=['POST'])
def detect_bullish_arrangement():
    data = request.get_json()
    stock_pool = data.get('pool', [])
    start_date = data['start_date'].replace('-', '')
    end_date = data['end_date'].replace('-', '')
    ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])
    window_size = data.get('window_size', 21)  # 窗口大小
    stride = data.get('stride', 2)  # 滑动步长
    
    # 缩放参数
    max_width = data.get('max_width', 65536)  # PIL限制
    max_height = data.get('max_height', 65536)  # PIL限制
    min_window_width = data.get('min_window_width', 4)  # 窗口最小宽度(英寸)
    min_window_height = data.get('min_window_height', 3)  # 窗口最小高度(英寸)
    safety_margin = data.get('safety_margin', 200)  # 安全余量(像素)
    
    # 检测参数
    enhance_detection = data.get('enhance_detection', True)  # 是否启用增强检测模式
    nms_threshold = data.get('nms_threshold', 0.3)  # 非极大值抑制阈值
    conf_threshold = data.get('conf_threshold', 0.15)  # 置信度阈值
    
    result = {}
    for stock in stock_pool:
        ts_code = f"{stock['code']}.SH" if stock['code'].startswith('6') else f"{stock['code']}.SZ"
        print(f"正在处理股票: {ts_code}")
        
        # 获取股票数据
        df = get_stock_data(ts_code, start_date, end_date) 
        if df.empty:
            print(f"未获取到股票数据: {ts_code}")
            continue
        
        df = calculate_ma(df, ma_list)
        if df.empty:
            print(f"计算均线后数据为空: {ts_code}")
            continue
        
        # 生成增强版的长图片
        stock_code = stock['code']
        try:
            long_chart_path, window_positions, image_size_inches, dpi = generate_enhanced_long_chart(
                stock_code, df, ma_list, window_size, stride, max_width, max_height, min_window_width, min_window_height, safety_margin, enhance_detection)
            
            # 处理增强版长图片上的检测结果
            bullish_intervals = process_enhanced_image_detection(
                long_chart_path, window_positions, image_size_inches, dpi, df, ma_list, conf_threshold)
            
            if bullish_intervals:
                print(f"检测到 {len(bullish_intervals)} 个多头排列模式: {ts_code}")
                result[ts_code] = bullish_intervals
            else:
                print(f"未检测到多头排列模式: {ts_code}")
        except Exception as e:
            print(f"处理股票时出错: {ts_code}, 错误: {e}")
    
    print(f"检测完成，共处理 {len(stock_pool)} 只股票，发现 {len(result)} 只有多头排列的股票")
    return jsonify({"bullish_arrangements": result})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    