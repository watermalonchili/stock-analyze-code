import json
import shutil
from skeleton_learner import SkeletonLearner
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from json_config import move_images_to_new_folder, read_json_data, write_json_data
from utils import calculate_ma, get_stock_data
from datetime import timedelta
import os
# 首先添加必要的导入
import pandas as pd
import torch
import numpy as np
import time
from few_shot_utils import get_ai_engine
import re

# 确保在文件开头添加这个路径配置
BRUSH_HISTORY_FILE = 'brush_history.json'
app = Flask(__name__)
CORS(app)  # 这行代码开启全局跨域，彻底解决所有路由的 Network Error
# 将会话有效期延长
app.permanent_session_lifetime = timedelta(minutes=30)

# 引入 Matplotlib 并强制使用 Agg 后端，防止在 Flask 线程中画图时报错崩溃
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

# 【修复 1】：定义 GPU/CPU 设备变量，解决 DEVICE 爆红
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 均线颜色配置 (必须与 few_shot_utils.py 保持 100% 一致)
MA_COLORS = {
    'MA4': '#000000',  # 黑
    'MA8': '#FF9800',  # 橙
    'MA12': '#E91E63',  # 粉红
    'MA16': '#9C27B0',  # 紫
    'MA20': '#4CAF50',  # 绿
    'MA47': '#2196F3'  # 蓝
}

# 行情数据目录：优先读环境变量 DATA_FOLDER（Docker 容器内为 /data），本地兜底项目下 data/kline-data
DATA_FOLDER = os.getenv('DATA_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'kline-data'))
# 获取当前 app.py 所在的绝对根目录 (自动适配 D盘/E盘)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_ROOT = os.path.join(PROJECT_DIR, "few_shot_learning", "version525", "data", "Images")

def _resolve_analysis_mode(mode_index):
    """从模型元数据 meta.json / modeListSelf 读取该模式的分析模式，兜底 KLINE"""
    meta_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "few_shot_learning", "version525", "data", "Images", str(mode_index), "meta.json"
    )
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                mode = json.load(f).get('analysisMode')
                if mode:
                    return mode
        except Exception:
            pass
    try:
        for m in read_json_data():
            if m.get('index') == mode_index or m.get('name') == mode_index:
                mode = m.get('analysis_mode')
                if mode:
                    return mode
    except Exception:
        pass
    return 'KLINE'

# ================= 【修复 2】：手写均线画图方法 =================
def create_chart(df, save_path):
    """绘制 224x224 的均线图片 (无坐标轴，白底)"""
    # 提取最后20天的数据绘图
    plot_data = df.tail(20).copy()
    plt.figure(figsize=(2.24, 2.24), dpi=100)

    for ma_name, color in MA_COLORS.items():
        if ma_name in plot_data.columns:
            plt.plot(range(len(plot_data)), plot_data[ma_name], color=color, linewidth=1.5)

    plt.axis('off')
    plt.gca().set_position([0, 0, 1, 1])
    plt.savefig(save_path, pad_inches=0, facecolor='white')
    plt.close()

# ================= 【修复 3】：手写K线画图方法 =================
# app.py 内部的 K 线绘制函数
def create_kline_skeleton_chart(df, save_path):
    """
    绘制 224x224 的纯 K线 蜡烛图 (无坐标轴，白底)
    """
    # 1. 提取最后 20 天数据
    plot_data = df.tail(20).copy().reset_index(drop=True)

    # 【修复】：如果在 K 线模式下传入了均线数据，确保我们能提取出正确的开高低收价格
    if 'open' not in plot_data.columns:
        # 如果只有收盘价和均线，我们用 close 模拟开盘价，用 MA 模拟最高最低，确保绝对不画出空白图！
        plot_data['open'] = plot_data['close'].shift(1).fillna(plot_data['close'].iloc[0])
        plot_data['high'] = plot_data[['open', 'close']].max(axis=1) * 1.01
        plot_data['low'] = plot_data[['open', 'close']].min(axis=1) * 0.99

    plt.figure(figsize=(2.24, 2.24), dpi=100)

    up = plot_data[plot_data.close >= plot_data.open]
    down = plot_data[plot_data.close < plot_data.open]

    # 2. 绘制上涨：红色 (柱体和上下影线)
    if not up.empty:
        plt.bar(up.index, up.close - up.open, bottom=up.open, color='red', width=0.6)
        plt.bar(up.index, up.high - up.close, bottom=up.close, color='red', width=0.1)
        plt.bar(up.index, up.low - up.open, bottom=up.open, color='red', width=0.1)

    # 3. 绘制下跌：绿色 (柱体和上下影线)
    if not down.empty:
        plt.bar(down.index, down.open - down.close, bottom=down.close, color='green', width=0.6)
        plt.bar(down.index, down.high - down.open, bottom=down.open, color='green', width=0.1)
        plt.bar(down.index, down.low - down.close, bottom=down.close, color='green', width=0.1)

    # 4. 移除多余的坐标轴和白边
    plt.axis('off')
    plt.gca().set_position([0, 0, 1, 1])
    plt.savefig(save_path, pad_inches=0, facecolor='white')
    plt.close()


CORS(app, resources={r"/save_screenshot": {
        "origins": Config.CORS_ORIGINS,
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})
@app.route('/save_screenshot', methods=['POST'])
def save_screenshot():
    try:
        # 获取前端传入的文件夹名称，默认为 'savepng'
        folder_name = request.form.get('folder', 'savepng')
        
        # 检查文件夹名称是否合法（避免路径遍历攻击）
        if not folder_name or any(c in folder_name for c in ['/', '\\', '..']):
            return jsonify({"success": False, "msg": "文件夹名称不合法"}), 400
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"success": False, "msg": "未找到文件"}), 400
        
        file = request.files['file']
        
        # 检查文件名是否存在
        if file.filename == '':
            return jsonify({"success": False, "msg": "文件名不能为空"}), 400
        
        # 定义保存路径（public/[folder_name]文件夹）
        save_dir = os.path.join(os.getcwd(), 'public', folder_name)
        # 确保文件夹存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存文件
        save_path = os.path.join(save_dir, file.filename)
        file.save(save_path)
        
        print(f"截图保存成功: {save_path}")
        return jsonify({
            "success": True, 
            "msg": "截图保存成功", 
            "path": save_path,
            "filename": file.filename,
            "folder": folder_name
        })
    
    except Exception as e:
        print(f"截图保存失败: {str(e)}")
        return jsonify({"success": False, "msg": f"服务器错误: {str(e)}"}), 500

# 完善CORS配置，添加图片访问路由的跨域支持
CORS(app, resources={
    r"/get_all_screenshots": {
        "origins": Config.CORS_ORIGINS,
        "methods": ['GET', "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True
    },
    r"/get_screenshot/<path:filename>": {  # 新增图片访问路由的CORS配置
        "origins": Config.CORS_ORIGINS,
        "methods": ['GET', "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

@app.route('/get_all_screenshots', methods=['GET'])
def get_all_screenshots():
    try:
        # 获取前端传入的文件夹名称，默认为 'savepng'
        folder_name = request.args.get('folder', 'savepng')
        
        # 检查文件夹名称是否合法
        if not folder_name or any(c in folder_name for c in ['/', '\\', '..']):
            return jsonify({"success": False, "msg": "文件夹名称不合法"}), 400
        
        # 构建图片目录路径
        save_dir = os.path.join(os.getcwd(), 'public', folder_name)
        
        if not os.path.exists(save_dir):
            return jsonify({"success": False, "msg": "图片目录不存在"}), 404
        
        if not os.path.isdir(save_dir):
            return jsonify({"success": False, "msg": "无效的图片目录路径"}), 400
        
        all_files = os.listdir(save_dir)
        
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        image_files = [
            file for file in all_files
            if os.path.isfile(os.path.join(save_dir, file)) and
            os.path.splitext(file)[1].lower() in image_extensions
        ]
        
        image_list = [
            {
                "filename": folder_name + '\\' + file,
                "url": f"/get_screenshot/{folder_name}/{file}", 
                "timestamp": os.path.getmtime(os.path.join(save_dir, file))
            }
            for file in image_files
        ]

        print(image_list)
        
        image_list.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return jsonify({
            "success": True,
            "count": len(image_list),
            "images": image_list,
            "folder": folder_name
        })
    
    except Exception as e:
        print(f"获取图片列表失败: {str(e)}")
        return jsonify({"success": False, "msg": f"服务器错误: {str(e)}"}), 500

# 新增图片访问路由，处理实际的图片文件请求
@app.route('/get_screenshot/<filename>', methods=['GET'])
def get_screenshot(filename):
    print("filename:" , filename)
    try:
        # 图片存储路径（与列表接口保持一致）
        save_dir = os.path.join(os.getcwd(), 'public')
        file_path = os.path.join(save_dir, filename)

        # 添加路径打印
        print(f"尝试访问的图片路径: {file_path}")  # 检查这个路径是否真实存在
        
        # 检查文件是否存在
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"success": False, "msg": "图片不存在"}), 404
        
        # 根据文件扩展名设置正确的MIME类型
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # 读取图片文件并返回
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        # 返回图片数据，设置正确的Content-Type
        from flask import Response
        return Response(image_data, mimetype=mime_type)
    
    except Exception as e:
        print(f"获取图片失败: {str(e)}")
        return jsonify({"success": False, "msg": f"服务器错误: {str(e)}"}), 500

# 添加删除文件接口的CORS配置
CORS(app, resources={r"/delete-files": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})
@app.route('/delete-files', methods=['POST'])
def delete_folder_contents():
    try:
        data = request.get_json()
        folder_path = data.get('folderPath')
        
        if not folder_path:
            return jsonify({"success": False, "msg": "缺少文件夹路径参数"}), 400
        
        #拼接实际路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = base_dir + folder_path
        
        print(f"尝试删除内容的文件夹路径: {full_path}")
        
        #安全校验：限制只能操作public目录下的文件夹
        full_path = os.path.abspath(full_path)
        base_dir_abs = os.path.abspath(base_dir)
        
        if not full_path.startswith(base_dir_abs):
            return jsonify({"success": False, "msg": "路径不合法"}), 403
        
        #检查路径是否存在且是文件夹
        if not os.path.exists(full_path):
            return jsonify({"success": False, "msg": "文件夹不存在"}), 404
        
        if not os.path.isdir(full_path):
            return jsonify({"success": False, "msg": "指定路径不是文件夹"}), 400
        
        #清空文件夹内容（保留文件夹本身）
        #遍历文件夹内所有内容
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            try:
                #如果是文件或链接，直接删除
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                #如果是子文件夹，递归删除
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"删除{item_path}失败: {str(e)}")
                return jsonify({"success": False, "msg": f"删除{item}时出错: {str(e)}"}), 500
        
        return jsonify({"success": True, "msg": "文件夹内容已全部清空"})
            
    except Exception as e:
        print(f"清空文件夹操作失败: {str(e)}")
        return jsonify({"success": False, "msg": f"服务器错误: {str(e)}"}), 500

CORS(app, resources={r"/get_modeListSelf_new": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})
@app.route('/get_modeListSelf_new', methods=['GET'])
def get_mode_list():
    """获取所有模式列表"""
    data = read_json_data()
    return jsonify({
        'success': True,
        'data': data
    })

CORS(app, resources={r"/detect_logic_pattern": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Type"],
    "supports_credentials": True
}})
# 小样本学习的检测模式（多尺度融合）
@app.route('/detect_logic_pattern', methods=['POST'])
def detect_logic_pattern():
    start_time_all = time.time()
    data = request.get_json(force=True)
    mode_index = data.get('mode_index', '')
    stock_pool = data.get('stock_pool', [])
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    ma_list = data.get('ma_list', [])
    w_d = float(data.get('w_d', 0.5))
    w_w = float(data.get('w_w', 0.3))
    w_m = float(data.get('w_m', 0.2))
    window_size = 20

    print(f"\n🚀 [AI多尺度融合扫描启动] 模式: {mode_index}, 权重: 日线={w_d}, 周线={w_w}, 月线={w_m}")

    AI_CLASS_MAP = {"BA": 1, "BeA": 0}
    target_idx = AI_CLASS_MAP.get(mode_index)
    from few_shot_utils import get_ai_engine
    ai_engine = get_ai_engine()

    clean_start = start_date.split('T')[0] if 'T' in start_date else start_date
    clean_end = end_date.split('T')[0] if 'T' in end_date else end_date
    search_start_dt = pd.to_datetime(clean_start)
    search_end_dt = pd.to_datetime(clean_end)
    print(f"   - 搜索日期: {clean_start} ~ {clean_end}")

    from deal_sim_time_range import resample_ohlcv

    data_folder = DATA_FOLDER
    results = []

    for index, stock in enumerate(stock_pool):
        code = stock['code'] if isinstance(stock, dict) else stock
        ts_code = f"{code}.SH" if code.startswith('6') else f"{code}.SZ"
        print(f"[{index + 1}/{len(stock_pool)}] 融合扫描: {ts_code}...", end='\r')

        # --- 1. 获取日线数据 ---
        df_raw = get_stock_data(ts_code, clean_start, clean_end, data_folder=data_folder)
        if df_raw is None or df_raw.empty:
            continue

        df_raw['trade_date'] = pd.to_datetime(df_raw['trade_date'])
        df_raw = df_raw[(df_raw['trade_date'] >= search_start_dt) & (df_raw['trade_date'] <= search_end_dt)]

        df_daily = calculate_ma(df_raw.copy(), ma_list)
        if len(df_daily) < window_size:
            continue

        # --- 2. 重采样周线/月线并预计算所有窗口得分 ---
        # 需要向前扩展数据范围：max(ma_list) + window_size 个周期的历史
        max_ma = max(ma_list) if ma_list else 20
        tf_scores = {}  # {tf_name: [(end_date, score), ...]}
        for tf_name in ['weekly', 'monthly']:
            tf_label = '周线' if tf_name == 'weekly' else '月线'
            tf_scores[tf_name] = []
            try:
                # 向前扩展：周线需要额外 max_ma 周 ≈ max_ma*7 天，月线需要额外 max_ma 月 ≈ max_ma*31 天
                extend_days = max_ma * (7 if tf_name == 'weekly' else 31) + 365
                extended_start = (search_start_dt - pd.Timedelta(days=extend_days)).strftime('%Y-%m-%d')
                df_tf_raw = get_stock_data(ts_code, extended_start, clean_end, data_folder=data_folder)
                if df_tf_raw is None or df_tf_raw.empty:
                    continue

                df_tf_raw['trade_date'] = pd.to_datetime(df_tf_raw['trade_date'])
                df_tf_raw = df_tf_raw[(df_tf_raw['trade_date'] >= pd.to_datetime(extended_start)) &
                                      (df_tf_raw['trade_date'] <= search_end_dt)]

                df_tf = resample_ohlcv(df_tf_raw.copy(), tf_name)
                if df_tf.empty or len(df_tf) < window_size:
                    continue
                df_tf = calculate_ma(df_tf, ma_list)
                if df_tf.empty or len(df_tf) < window_size:
                    continue

                step = 2 if tf_name == 'weekly' else 1
                skipped = 0
                scored = 0
                for i in range(0, len(df_tf) - window_size + 1, step):
                    window = df_tf.iloc[i: i + window_size]
                    # 只保留结束日期在用户搜索范围内的窗口（用于后续与日线对齐）
                    end_dt = window.iloc[-1]['trade_date']
                    if end_dt < search_start_dt:
                        skipped += 1
                        continue
                    score = ai_engine.get_score(window, ma_list, target_idx, mode_index)
                    tf_scores[tf_name].append((end_dt, score))
                    scored += 1

                print(f"  {tf_label}: 总窗口={len(df_tf) - window_size + 1}, 跳过={skipped}(早于搜索起始), 评分={scored}")
            except Exception as e:
                print(f"  {tf_label} 预计算出错: {str(e)}")

        # --- 3. 构建周线/月线得分的按日期排序列表（用于二分查找） ---
        import bisect
        weekly_dates = [s[0] for s in tf_scores['weekly']]
        weekly_score_map = [s[1] for s in tf_scores['weekly']]
        monthly_dates = [s[0] for s in tf_scores['monthly']]
        monthly_score_map = [s[1] for s in tf_scores['monthly']]

        # --- 4. 日线滑动扫描 + 融合评分 ---
        max_fusion = 0.0
        best_info = None
        total_daily_windows = len(df_daily) - window_size + 1

        for i in range(0, total_daily_windows, 5):
            daily_window = df_daily.iloc[i: i + window_size]
            score_daily = ai_engine.get_score(daily_window, ma_list, target_idx, mode_index)

            end_dt = daily_window.iloc[-1]['trade_date']
            start_dt = daily_window.iloc[0]['trade_date']

            # 二分查找：找到 end_dt 对应的周线得分
            score_weekly = 0.0
            if weekly_dates:
                idx = bisect.bisect_right(weekly_dates, end_dt)
                if idx > 0:
                    score_weekly = weekly_score_map[idx - 1]

            # 二分查找：找到 end_dt 对应的月线得分
            score_monthly = 0.0
            if monthly_dates:
                idx = bisect.bisect_right(monthly_dates, end_dt)
                if idx > 0:
                    score_monthly = monthly_score_map[idx - 1]

            fusion_score = w_d * score_daily + w_w * score_weekly + w_m * score_monthly

            # 逐窗口日志：每10个窗口打印一次，或分数较高时打印
            if i % 50 == 0 or fusion_score >= 0.2:
                print(f"    窗口[{i}/{total_daily_windows}] {start_dt.strftime('%Y-%m-%d')}~{end_dt.strftime('%Y-%m-%d')} | 日={score_daily:.3f} 周={score_weekly:.3f} 月={score_monthly:.3f} | 融合={fusion_score:.3f}")

            if fusion_score > max_fusion:
                max_fusion = fusion_score
                best_info = {
                    'daily_window': daily_window.copy(),
                    'score_daily': round(score_daily, 4),
                    'score_weekly': round(score_weekly, 4),
                    'score_monthly': round(score_monthly, 4),
                    'fusion_score': round(fusion_score, 4),
                }

        print(f"分析完毕: {ts_code} | 融合相似度: {max_fusion:.4f}")

        if best_info is not None and max_fusion >= 0.3:
            raw_name = stock['name'] if isinstance(stock, dict) and 'name' in stock else "匹配股票"
            best_window = best_info['daily_window']
            best_window['trade_date'] = best_window['trade_date'].dt.strftime('%Y-%m-%d')
            record_data = best_window.to_dict('records')
            results.append({
                "stock_code": code,
                "stock_name": raw_name,
                "similarity": best_info['fusion_score'],
                "score_daily": best_info['score_daily'],
                "score_weekly": best_info['score_weekly'],
                "score_monthly": best_info['score_monthly'],
                "fusion_score": best_info['fusion_score'],
                "recent_data": record_data,
                "recent_data_raw": record_data
            })

    results.sort(key=lambda x: x['fusion_score'], reverse=True)
    elapsed = time.time() - start_time_all
    print(f"\n✨ [多尺度融合扫描完成] 共 {len(results)} 个结果, 耗时: {elapsed:.2f}s")

    return jsonify({
        "result": results,
        "base_ma_periods": ma_list,
        "count": len(results),
        "weights": {"w_d": w_d, "w_w": w_w, "w_m": w_m}
    })


# ======================== 实时查找（双阶段 + 三尺度） ========================
CORS(app, resources={r"/api/realtime_scan": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

def get_5min_data(ts_code, start_date, end_date):
    """5分钟线数据获取（占位，待数据接入后实现）"""
    return None


def _skeleton_to_target(skeleton_points, window_size):
    """将用户骨架点插值为 window_size 长度的平滑目标序列"""
    pts = sorted(skeleton_points, key=lambda p: p.get('date', ''))
    prices = [float(p['price']) for p in pts]
    n = len(prices)
    if n < 2:
        return None
    indices = np.linspace(0, n - 1, window_size)
    interp = np.interp(indices, np.arange(n), prices)
    return interp.tolist()


def _dtw_similarity(target, query):
    """DTW 动态时间弯曲相似度 (0~1)，值越大越相似"""
    t = np.asarray(target, dtype=float)
    q = np.asarray(query, dtype=float)
    n, m = len(t), len(q)
    if n == 0 or m == 0:
        return 0.0
    # Z-score 归一化消除绝对价格差异
    t = (t - t.mean()) / (t.std() + 1e-8)
    q = (q - q.mean()) / (q.std() + 1e-8)
    # DTW 动态规划
    INF = float('inf')
    dp = np.full((n + 1, m + 1), INF)
    dp[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(t[i-1] - q[j-1])
            dp[i, j] = cost + min(dp[i-1, j], dp[i, j-1], dp[i-1, j-1])
    dist = dp[n, m] / max(n, m)
    return float(np.exp(-dist))


@app.route('/api/realtime_scan', methods=['POST'])
def realtime_scan():
    """
    实时查找：只扫每只股票最近 N 天（N = 用户框选区间的实际交易日数）
    双阶段：视觉粗筛(get_score) → 规则精排(ai_filter)
    三尺度：5分钟/日线/周线（5分钟暂占位）
    """
    start_time = time.time()
    data = request.get_json(force=True)
    mode_index = data.get('mode_index', '')
    stock_pool = data.get('stock_pool', [])
    ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])
    rule_tags = data.get('rule_tags', [])
    rule_prompt = data.get('rule_prompt', '')
    brush_start = data.get('brush_start', '')
    brush_end = data.get('brush_end', '')

    # 根据用户框选区间计算实际交易日数作为窗口大小
    window_size = 20  # 默认值
    if brush_start and brush_end:
        try:
            # 用基准股票的数据计算实际交易日数
            first_code = stock_pool[0]['code'] if stock_pool and isinstance(stock_pool[0], dict) else stock_pool[0] if stock_pool else None
            if first_code:
                ts = f"{first_code}.SH" if str(first_code).startswith('6') else f"{first_code}.SZ"
                ref_df = get_stock_data(ts, str(brush_start)[:10], str(brush_end)[:10], data_folder=DATA_FOLDER)
                if ref_df is not None and not ref_df.empty:
                    window_size = len(ref_df)
                    print(f"   用户框选 {brush_start} ~ {brush_end} → 实际 {window_size} 个交易日")
        except Exception as e:
            print(f"   计算窗口大小失败，用默认20: {e}")

    # 限制窗口范围：最少10天，最多120天
    window_size = max(10, min(120, window_size))

    print(f"\n🚀 [实时查找启动] 模式: {mode_index}, 股票池: {len(stock_pool)} 只, 窗口: {window_size}天")

    AI_CLASS_MAP = {"BA": 1, "BeA": 0}
    target_idx = AI_CLASS_MAP.get(mode_index)
    from few_shot_utils import get_ai_engine
    ai_engine = get_ai_engine()

    # 生成规则过滤函数
    ai_filter_func = None
    if rule_tags or rule_prompt:
        from llm_agent import generate_ai_filter
        ai_filter_func = generate_ai_filter(rule_tags, rule_prompt)
        print(f"   - 规则精排: 已启用 ({len(rule_tags)} 个标签)")

    # 加载目标序列（优先用骨架插值，兜底用收盘价）
    target_close = None
    try:
        import json as _json
        image_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'version525', 'data', 'Images')
        meta_path = os.path.join(image_root, mode_index, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = _json.load(f)
            # 优先用骨架插值
            custom_skeleton = meta.get('custom_skeleton', [])
            if custom_skeleton and len(custom_skeleton) >= 2:
                target_close = _skeleton_to_target(custom_skeleton, window_size)
                print(f"   - 骨架插值目标: {len(custom_skeleton)}个拐点 → {window_size}点")
            else:
                seg_data = meta.get('segmentData', [])
                if seg_data and len(seg_data) > 0:
                    first_seg = seg_data[0]
                    target_close = [float(d.get('close', 0)) for d in first_seg if float(d.get('close', 0)) > 0]
                    print(f"   - 完整收盘价目标: {len(target_close)} 个点")
    except Exception as e:
        print(f"   - DTW目标加载失败: {e}")

    from deal_sim_time_range import resample_ohlcv
    import bisect

    data_folder = DATA_FOLDER
    results = []
    stats = {"total": 0, "pass_visual": 0, "pass_rule": 0}
    _rule_blocked = []  # 被规则拒绝的候选，用于自动放宽回退

    max_ma = max(ma_list) if ma_list else 20
    # 周线需要额外历史：max_ma 周 + window_size 周 ≈ (max_ma + window_size) * 7 天
    weekly_extend_days = (max_ma + window_size) * 7 + 30

    for index, stock in enumerate(stock_pool):
        code = stock['code'] if isinstance(stock, dict) else stock
        raw_name = stock['name'] if isinstance(stock, dict) and 'name' in stock else code
        ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
        print(f"[{index + 1}/{len(stock_pool)}] 实时扫描: {ts_code}...", end='\r')
        stats["total"] += 1

        try:
            # --- 日线：取最近 window_size 天 ---
            df_raw = get_stock_data(ts_code, None, None, data_folder=data_folder)
            if df_raw is None or df_raw.empty or len(df_raw) < window_size:
                continue
            df_raw['trade_date'] = pd.to_datetime(df_raw['trade_date'])
            df_raw = df_raw.sort_values('trade_date').reset_index(drop=True)
            df_raw = calculate_ma(df_raw, ma_list)
            if df_raw.empty:
                continue

            daily_window = df_raw.tail(window_size).copy().reset_index(drop=True)
            daily_window['trade_date'] = daily_window['trade_date'].dt.strftime('%Y-%m-%d')
            end_dt = pd.to_datetime(daily_window.iloc[-1]['trade_date'])

            # --- 周线：取与日线 end_date 对齐的窗口 ---
            weekly_window = None
            weekly_start = (end_dt - pd.Timedelta(days=weekly_extend_days)).strftime('%Y-%m-%d')
            df_w_raw = get_stock_data(ts_code, weekly_start, end_dt.strftime('%Y-%m-%d'), data_folder=data_folder)
            if df_w_raw is not None and not df_w_raw.empty:
                df_w_raw['trade_date'] = pd.to_datetime(df_w_raw['trade_date'])
                df_w_raw = df_w_raw.sort_values('trade_date').reset_index(drop=True)
                df_w = resample_ohlcv(df_w_raw, 'weekly')
                if df_w is not None and not df_w.empty and len(df_w) >= window_size:
                    df_w = calculate_ma(df_w, ma_list)
                    if not df_w.empty:
                        weekly_window = df_w.tail(window_size).copy().reset_index(drop=True)
                        weekly_window['trade_date'] = weekly_window['trade_date'].dt.strftime('%Y-%m-%d')

            # --- 5分钟线（占位） ---
            min5_window = None

            # === Stage 0: YOLO 初筛（仅 YOLO 模型）===
            yolo_model_path = os.path.join('custom_modes', f'{mode_index}_yolo.pt')
            is_yolo_model = os.path.exists(yolo_model_path)
            yolo_confidence = None

            if is_yolo_model:
                # 取最近150天画大图 → YOLO 检测
                context_days = min(150, len(df_raw))
                context_df = df_raw.tail(context_days).copy()
                try:
                    import sys as _sys
                    _yolo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'yolo0623')
                    if _yolo_dir not in _sys.path:
                        _sys.path.insert(0, _yolo_dir)
                    from main import detect_pattern_yolo as _detect_yolo
                    yolo_hits = _detect_yolo(context_df, ma_list, mode_index, conf_threshold=0.15, img_size=416,
                                             analysis_mode=_resolve_analysis_mode(mode_index))
                except Exception as e:
                    print(f"    YOLO检测出错: {e}")
                    yolo_hits = []

                if not yolo_hits:
                    continue  # YOLO 没检测到形态 → 跳过
                yolo_confidence = yolo_hits[0]['confidence']

            # === 阶段1：视觉粗筛 ===
            score_daily = ai_engine.get_score(daily_window, ma_list, target_idx, mode_index)
            score_weekly = 0.0
            if weekly_window is not None:
                score_weekly = ai_engine.get_score(weekly_window, ma_list, target_idx, mode_index)
            score_min5 = None  # 5分钟线暂无

            # === 阶段1.5：数值相似度（DTW）===
            dtw_daily = 0.0
            dtw_weekly = 0.0
            if target_close and len(target_close) >= 2:
                dtw_daily = _dtw_similarity(target_close, daily_window['close'].values)
                if weekly_window is not None:
                    dtw_weekly = _dtw_similarity(target_close, weekly_window['close'].values)

            yolo_str = f" YOLO={yolo_confidence:.2f}" if yolo_confidence else ""
            print(f"    {ts_code} |  DTW日={dtw_daily:.4f} 周={dtw_weekly:.4f}{yolo_str}")

            # YOLO模型已通过Stage 0初筛，跳过视觉阈值；非YOLO模型用视觉阈值
            if not is_yolo_model:
                if score_daily < 0.2 and score_weekly < 0.2:
                    continue
            stats["pass_visual"] += 1

            # 构建候选结果
            candidate = {
                "stock_code": code,
                "stock_name": raw_name,
                "score_daily": round(score_daily, 4),
                "score_weekly": round(score_weekly, 4),
                "score_min5": score_min5,
                "dtw_daily": round(dtw_daily, 4),
                "dtw_weekly": round(dtw_weekly, 4),
                "yolo_confidence": yolo_confidence,
                "recent_data_daily": daily_window.to_dict('records'),
                "recent_data_weekly": weekly_window.to_dict('records') if weekly_window is not None else [],
                "recent_data_min5": min5_window,
            }

            # === 阶段2：规则精排（拒绝的候选暂存，用于自动放宽回退） ===
            if ai_filter_func is not None:
                try:
                    if not ai_filter_func(daily_window):
                        _rule_blocked.append(candidate)
                        continue
                except Exception:
                    pass  # 规则报错则放行
            stats["pass_rule"] += 1
            results.append(candidate)

        except Exception as e:
            print(f"\n  ⚠ {ts_code} 扫描出错: {e}")
            continue

    # 如果LLM规则过滤过严（通过率0%），自动放宽回退
    if ai_filter_func is not None and stats['pass_rule'] == 0 and _rule_blocked:
        print(f"⚠️ [自动放宽] LLM规则过滤过严（通过率0%），跳过规则过滤，返回全部{len(_rule_blocked)}个候选")
        results = _rule_blocked
        stats['pass_rule'] = len(results)

    # 默认按 DTW 日线相似度排序
    results.sort(key=lambda x: x.get('dtw_daily', 0), reverse=True)

    elapsed = time.time() - start_time
    print(f"\n✨ [实时查找完成] 总计{stats['total']}只, 视觉通过{stats['pass_visual']}, 规则通过{stats['pass_rule']}, 耗时{elapsed:.1f}s")

    return jsonify({
        "success": True,
        "result": results[:100],
        "count": len(results),
        "stats": stats,
    })


# ======================== 个股历史形态回测引擎 ========================
CORS(app, resources={r"/api/analyze_stock_history": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

@app.route('/api/analyze_stock_history', methods=['POST'])
def analyze_stock_history():
    """
    对单只股票进行全历史滑窗回测：
    1. 滑窗 DTW 匹配历史相似片段
    2. 截取命中后 N 天的未来走势
    3. 统计胜率、平均涨幅、最大回撤
    """
    try:
        data = request.get_json(force=True)
        code = data.get('stock_code', '')
        mode_index = data.get('mode_index', '')
        ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])
        future_days = int(data.get('future_days', 10))
        dtw_threshold = float(data.get('dtw_threshold', 0.5))

        ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
        print(f"\n📊 [历史回测] {ts_code}, 未来{future_days}天, DTW阈值={dtw_threshold}")

        # 1. 加载目标序列（优先用骨架插值）
        import json as _json
        target_close = None
        image_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'version525', 'data', 'Images')
        meta_path = os.path.join(image_root, mode_index, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = _json.load(f)
            custom_skeleton = meta.get('custom_skeleton', [])
            if custom_skeleton and len(custom_skeleton) >= 2:
                # window_size 由骨架决定
                window_size = len(meta.get('segmentData', [[]])[0]) if meta.get('segmentData') else 20
                target_close = _skeleton_to_target(custom_skeleton, max(window_size, 10))
                print(f"   骨架插值目标: {len(custom_skeleton)}个拐点 → {len(target_close)}点")
            else:
                seg_data = meta.get('segmentData', [])
                if seg_data and len(seg_data) > 0:
                    target_close = [float(d.get('close', 0)) for d in seg_data[0] if float(d.get('close', 0)) > 0]

        if not target_close or len(target_close) < 2:
            return jsonify({"success": False, "msg": "无法加载目标序列"}), 400

        window_size = len(target_close)

        # 2. 加载全历史数据
        data_folder = DATA_FOLDER
        df = get_stock_data(ts_code, None, None, data_folder=data_folder)
        if df is None or df.empty or len(df) < window_size + future_days:
            return jsonify({"success": False, "msg": "历史数据不足"}), 400

        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date').reset_index(drop=True)
        df = calculate_ma(df, ma_list)
        closes = df['close'].values.astype(float)

        # 3. 三阶段检索：YOLO粗筛 → 规则过滤 → DTW精排
        matches = []

        # --- Stage 1: YOLO 视觉粗筛（有模型时用，无模型降级 DTW 全扫）---
        candidate_ranges = []  # [(start_idx, end_idx), ...]
        yolo_model_path = os.path.join('custom_modes', f'{mode_index}_yolo.pt')
        yolo_all_hits = []  # 全部 YOLO 原始检测（供开发者全景图）

        if os.path.exists(yolo_model_path):
            print(f"   Stage 1: YOLO 粗筛...")
            import sys as _sys
            _yolo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'yolo0623')
            if _yolo_dir not in _sys.path:
                _sys.path.insert(0, _yolo_dir)
            from main import detect_pattern_yolo

            yolo_hits = detect_pattern_yolo(df, ma_list, mode_index, conf_threshold=0.15, img_size=416,
                                            analysis_mode=_resolve_analysis_mode(mode_index))
            for hit in yolo_hits:
                candidate_ranges.append((hit['start_idx'], hit['end_idx']))
                yolo_all_hits.append({
                    'start_idx': hit['start_idx'],
                    'end_idx': hit['end_idx'],
                    'start_date': hit['start_date'],
                    'end_date': hit['end_date'],
                    'confidence': hit['confidence'],
                })
            print(f"   YOLO 命中 {len(candidate_ranges)} 个候选区间")
        else:
            print(f"   Stage 1: 无YOLO模型，降级为DTW全量扫描...")
            step = 3
            total_windows = len(df) - window_size - future_days
            for i in range(0, max(total_windows, 1), step):
                candidate_ranges.append((i, i + window_size - 1))

        # --- Stage 2+3: 对每个候选区间做规则过滤 + DTW 精排 ---
        # 规则过滤函数（复用 LLM 生成的 ai_filter）
        ai_filter_func = None
        rule_tags = data.get('rule_tags', [])
        rule_prompt = data.get('rule_prompt', '')
        if rule_tags or rule_prompt:
            from llm_agent import generate_ai_filter
            ai_filter_func = generate_ai_filter(rule_tags, rule_prompt)

        # 第一轮：收集所有通过规则的候选 + DTW 分数
        scored_candidates = []
        for (i_start, i_end) in candidate_ranges:
            i = i_start
            window_close = closes[i: i + window_size]
            if len(window_close) < window_size:
                continue

            # Stage 2: 规则过滤
            if ai_filter_func is not None:
                try:
                    window_df = df.iloc[i: i + window_size]
                    if not ai_filter_func(window_df):
                        continue
                except Exception:
                    pass

            # Stage 3: DTW 精排（先打分，后面再筛）
            dtw_score = _dtw_similarity(target_close, window_close)
            scored_candidates.append((i, dtw_score))

        # 动态阈值：取所有候选中 DTW 分数 top 30%（至少5个，最多30个）
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        keep_count = min(max(int(len(scored_candidates) * 0.3), 5), 30)
        top_candidates = scored_candidates[:keep_count]
        print(f"   候选{len(scored_candidates)}个, 保留{len(top_candidates)}个 (top {keep_count})")

        # 固定截取20天未来数据，前端按选择天数切片
        max_future = 20
        ma_cols = [f"MA{m}" for m in ma_list] if ma_list else []
        target_cols = ['trade_date', 'open', 'close', 'high', 'low'] + [c for c in ma_cols if c in df.columns]
        matches = []
        for (i, dtw_score) in top_candidates:

            # 截取未来 max_future 天走势
            future_start = i + window_size
            future_end = min(future_start + max_future, len(closes))
            future_prices = closes[future_start: future_end]
            if len(future_prices) < 3:
                continue

            match_close = closes[i + window_size - 1]  # Day 0 = 匹配窗口最后一天的收盘价
            # 归一化路径（全部max_future天，前端按选择天数切片）
            norm_path_full = ((future_prices - match_close) / match_close * 100).tolist()

            start_date = str(df.iloc[i]['trade_date'])[:10]
            end_date = str(df.iloc[i + window_size - 1]['trade_date'])[:10]

            # 提取匹配窗口和未来窗口的完整数据
            match_records = df.iloc[i: i + window_size][target_cols].copy()
            match_records['trade_date'] = match_records['trade_date'].dt.strftime('%Y-%m-%d')
            match_data = match_records.to_dict('records')

            future_records = df.iloc[future_start: future_end][target_cols].copy()
            future_records['trade_date'] = future_records['trade_date'].dt.strftime('%Y-%m-%d')
            future_data = future_records.to_dict('records')

            matches.append({
                'start_date': start_date,
                'end_date': end_date,
                'dtw_score': round(dtw_score, 4),
                'match_data': match_data,
                'future_data': future_data,
                'future_dates': [r['trade_date'] for r in future_data],
                'norm_path_full': [round(v, 2) for v in norm_path_full],
            })

            print(f"    ✅ 命中: {start_date}~{end_date} | DTW={dtw_score:.3f}")

        # 4. NMS 去重：合并重叠的命中窗口（保留 DTW 最高的）
        if len(matches) > 1:
            matches.sort(key=lambda m: m['dtw_score'], reverse=True)
            kept = []
            for m in matches:
                overlap = False
                for k in kept:
                    # 如果两个命中的日期范围有重叠（超过一半），跳过
                    s1, e1 = m['start_date'], m['end_date']
                    s2, e2 = k['start_date'], k['end_date']
                    if s1 <= e2 and s2 <= e1:
                        overlap = True
                        break
                if not overlap:
                    kept.append(m)
            matches = kept[:30]  # 最多保留30个

        # 按日期倒序排列（最新的在前）
        matches.sort(key=lambda m: m['start_date'], reverse=True)

        print(f"📊 [回测完成] {ts_code}: 共{len(matches)}次命中")

        # 全历史K线（供开发者全景图；含均线列，MA 模式下渲染均线全景）
        ma_cols = [f"MA{m}" for m in ma_list] if ma_list else []
        full_history_cols = ['trade_date', 'open', 'close', 'high', 'low'] + [c for c in ma_cols if c in df.columns]
        full_history = df[full_history_cols].copy()
        full_history['trade_date'] = full_history['trade_date'].dt.strftime('%Y-%m-%d')

        return jsonify({
            "success": True,
            "stock_code": code,
            "max_future": max_future,
            "matches": matches,
            "yolo_all_hits": yolo_all_hits,
            "full_history": full_history.to_dict('records'),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "msg": str(e)}), 500


# ======================== YOLO 自定义形态检测 ========================
CORS(app, resources={r"/api/train_yolo": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

@app.route('/api/train_yolo', methods=['POST'])
def train_yolo_endpoint():
    """训练 YOLO 检测器：直接用用户正负样本 + 数据增强"""
    try:
        data = request.get_json(force=True)
        mode_index = data.get('mode_index', '')
        segments = data.get('segments', [])
        negative_segments = data.get('negative_segments', [])
        ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])
        epochs = int(data.get('epochs', 80))
        analysis_mode = data.get('analysis_mode', data.get('analysisMode', 'KLINE'))

        if not mode_index or not segments:
            return jsonify({"success": False, "msg": "缺少 mode_index 或正样本"}), 400

        print(f"\n🚀 [YOLO训练启动] 模式: {mode_index}, 正样本: {len(segments)}, 负样本: {len(negative_segments)}")

        import sys as _sys
        _yolo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'yolo0623')
        if _yolo_dir not in _sys.path:
            _sys.path.insert(0, _yolo_dir)
        from main import build_dataset_from_samples, train_yolo as train_yolo_detector

        # 用 hash 避免中文路径问题
        import hashlib
        safe_name = hashlib.md5(mode_index.encode('utf-8')).hexdigest()[:8]
        output_dir = os.path.join('custom_modes', f'yolo_dataset_{safe_name}')
        yaml_path, pos_count, neg_count = build_dataset_from_samples(
            segments, negative_segments, ma_list, output_dir, analysis_mode
        )

        if pos_count < 5:
            return jsonify({"success": False, "msg": f"正样本不足({pos_count}张)"}), 400

        model_path = train_yolo_detector(yaml_path, mode_index, epochs=epochs)

        # 保存 meta.json（供 DTW 目标序列和模型预览使用）
        import json as _json
        image_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'version525', 'data', 'Images')
        model_image_dir = os.path.join(image_root, mode_index)
        os.makedirs(model_image_dir, exist_ok=True)
        meta_data = {
            'analysisMode': analysis_mode,
            'custom_skeleton': data.get('custom_skeleton', []),
            'segmentData': segments[:5] if isinstance(segments, list) else [],
        }
        meta_path = os.path.join(model_image_dir, "meta.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            _json.dump(meta_data, f, ensure_ascii=False, indent=2)
        print(f"💾 YOLO模型元数据已保存: {meta_path}")

        # 注册到 modeListSelf.json，标记 is_yolo
        formatted_lines = ["MA4", "MA8", "MA12", "MA16", "MA20", "MA47"]
        new_mode_entry = {
            "index": mode_index,
            "name": mode_index,
            "lines": formatted_lines,
            "is_custom": True,
            "is_yolo": True,
            "analysis_mode": analysis_mode,
            "modeDescription": f"YOLO 检测模型，基于 {len(segments)} 个样本+数据增强训练"
        }
        current_modes = read_json_data()
        current_modes = [m for m in current_modes if m['name'] != mode_index]
        current_modes.append(new_mode_entry)
        write_json_data(current_modes)

        print(f"✅ [YOLO训练完成] 模型: {model_path}, 正样本(含增强): {pos_count}, 负样本: {neg_count}")
        return jsonify({
            "success": True,
            "model_path": model_path,
            "pos_count": pos_count,
            "neg_count": neg_count,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "msg": f"训练失败: {str(e)}"}), 500


CORS(app, resources={r"/api/detect_yolo_pattern": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

@app.route('/api/detect_yolo_pattern', methods=['POST'])
def detect_yolo_pattern_endpoint():
    """YOLO 快速扫描：每只股票一张图 → 一次前向传播"""
    try:
        start_time = time.time()
        data = request.get_json(force=True)
        mode_index = data.get('mode_index', '')
        stock_pool = data.get('stock_pool', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])
        conf_threshold = float(data.get('conf_threshold', 0.3))

        if not mode_index or not stock_pool:
            return jsonify({"success": False, "msg": "缺少参数"}), 400

        model_path = os.path.join('custom_modes', f'{mode_index}_yolo.pt')
        if not os.path.exists(model_path):
            return jsonify({"success": False, "msg": f"YOLO 模型未训练，请先训练"}), 400

        print(f"\n🚀 [YOLO快速扫描] 模式: {mode_index}, 股票池: {len(stock_pool)} 只")

        import sys as _sys
        _yolo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'yolo0623')
        if _yolo_dir not in _sys.path:
            _sys.path.insert(0, _yolo_dir)
        from main import detect_pattern_yolo
        from utils import get_stock_data, calculate_ma

        clean_start = start_date.split('T')[0] if 'T' in str(start_date) else str(start_date)
        clean_end = end_date.split('T')[0] if 'T' in str(end_date) else str(end_date)
        search_start_dt = pd.to_datetime(clean_start) if clean_start else None
        search_end_dt = pd.to_datetime(clean_end) if clean_end else None

        data_folder = DATA_FOLDER
        results = []

        for index, stock in enumerate(stock_pool):
            code = stock['code'] if isinstance(stock, dict) else stock
            raw_name = stock['name'] if isinstance(stock, dict) and 'name' in stock else code
            ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
            print(f"[{index+1}/{len(stock_pool)}] YOLO扫描: {ts_code}...", end='\r')

            try:
                df = get_stock_data(ts_code, clean_start, clean_end, data_folder=data_folder)
                if df is None or df.empty or len(df) < 30:
                    continue
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date').reset_index(drop=True)
                df = calculate_ma(df, ma_list)
                if df.empty:
                    continue
            except Exception:
                continue

            detections = detect_pattern_yolo(df, ma_list, mode_index,
                                             conf_threshold=conf_threshold,
                                             analysis_mode=_resolve_analysis_mode(mode_index))
            for det in detections:
                seg_df = det['segment_df'].copy()
                seg_df['trade_date'] = seg_df['trade_date'].dt.strftime('%Y-%m-%d')
                results.append({
                    "stock_code": code,
                    "stock_name": raw_name,
                    "similarity": det['confidence'],
                    "start_date": det['start_date'],
                    "end_date": det['end_date'],
                    "recent_data": seg_df.to_dict('records'),
                    "recent_data_raw": seg_df.to_dict('records'),
                })

        results.sort(key=lambda x: x['similarity'], reverse=True)
        elapsed = time.time() - start_time
        print(f"\n✨ [YOLO扫描完成] 共 {len(results)} 个结果, 耗时: {elapsed:.2f}s")

        return jsonify({
            "success": True,
            "result": results,
            "base_ma_periods": ma_list,
            "count": len(results),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "msg": f"扫描失败: {str(e)}"}), 500


# 用户反馈：将低分/高分样本自动纳入正负样本集
CORS(app, resources={r"/submit_feedback": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Type"],
    "supports_credentials": True
}})
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    mode_index = data.get('mode_index')
    feedback_type = data.get('feedback_type')
    recent_data = data.get('recent_data')
    ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])

    if not recent_data or not mode_index:
        return jsonify({"success": False, "msg": "param missing"}), 400

    try:
        engine = get_ai_engine()

        df = pd.DataFrame(recent_data)
        for col in ['open', 'close', 'high', 'low', 'vol']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        for ma_num in ma_list:
            ma_col = f'MA{ma_num}'
            if ma_col in df.columns:
                df[ma_col] = pd.to_numeric(df[ma_col], errors='coerce')

        custom_adapter = os.path.join("custom_modes", f"{mode_index}_adapter.pth")
        if os.path.exists(custom_adapter):
            try:
                engine.model.adapter.load_state_dict(
                    torch.load(custom_adapter, map_location=engine.device)
                )
                engine.model.eval()
            except Exception as e:
                print(f"Warning: adapter load failed {e}")

        feat = engine.extract_feature(df, ma_list)

        sub_folder = "positive" if feedback_type == 'like' else "negative"
        save_path = os.path.join("custom_modes", "feedback", str(mode_index), sub_folder)
        os.makedirs(save_path, exist_ok=True)

        filename = f"{feedback_type}_{int(time.time() * 1000)}.npy"
        np.save(os.path.join(save_path, filename), feat)

        count = len([f for f in os.listdir(save_path) if f.endswith('.npy')])
        label = "positive" if feedback_type == 'like' else "negative"
        msg = f"saved to {label} pool (total {count})"
        print(f"[feedback] {mode_index}/{sub_folder}: {filename} (total {count})")
        return jsonify({"success": True, "msg": msg, "total_count": count})
    except Exception as e:
        print(f"[feedback] failed: {str(e)}")
        return jsonify({"success": False, "msg": str(e)}), 500

CORS(app, resources={r"/train_custom_model": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})
import few_shot_learning.version525.main as meta_main

# ================= 动态背景参照类生成器 (解决冷启动) =================
# app.py 中的 ensure_background_class
def ensure_background_class(data_folder, num_samples=15, analysis_mode='MA', stock_pool_codes=None, model_bg_dir=None):
    """
    生成背景参照类。
    model_bg_dir: 如果指定，背景图片保存到模型专属目录；否则用共享的 background_class
    优先从真实股票池随机抽样非匹配片段；若无股票池则用随机游走兜底。
    """
    bg_dir = model_bg_dir if model_bg_dir else os.path.join(data_folder, "background_class")
    if os.path.exists(bg_dir) and len(os.listdir(bg_dir)) >= num_samples:
        return bg_dir

    print("💡 [系统检测] 未找到预设图片，正在生成背景参照类数据...")
    os.makedirs(bg_dir, exist_ok=True)

    # ---- 优先方案：从真实股票池抽样 ----
    real_count = 0
    if stock_pool_codes:
        np.random.shuffle(stock_pool_codes)
        for code in stock_pool_codes:
            if real_count >= num_samples:
                break
            ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
            try:
                df = get_stock_data(ts_code, None, None, data_folder=DATA_FOLDER)
                if df is None or df.empty or len(df) < 67:
                    continue
                df = calculate_ma(df, [4, 8, 12, 16, 20, 47])
                if df.empty:
                    continue
                # 随机取一段20天窗口
                max_start = len(df) - 20
                if max_start <= 0:
                    continue
                start = np.random.randint(0, max_start)
                segment = df.iloc[start: start + 20].copy()
                save_path = os.path.join(bg_dir, f"bg_real_{real_count}.jpg")
                if analysis_mode == 'MA':
                    create_chart(segment, save_path)
                else:
                    create_kline_skeleton_chart(segment, save_path)
                real_count += 1
            except Exception:
                continue

    print(f"   真实股票背景: {real_count} 张")

    # ---- 兜底方案：随机游走补足 ----
    remaining = num_samples - real_count
    if remaining > 0:
        print(f"   真实样本不足，用随机游走补充 {remaining} 张")
        for i in range(remaining):
            prices = [100.0]
            for _ in range(120):
                change = np.random.normal(0, 1.5)
                prices.append(max(10.0, prices[-1] + change))
            df = pd.DataFrame({'close': prices})
            df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
            df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 1.0, size=len(df))
            df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 1.0, size=len(df))
            df['low'] = df['low'].clip(lower=1.0)
            save_path = os.path.join(bg_dir, f"bg_rand_{i}.jpg")
            if analysis_mode == 'MA':
                for p in [4, 8, 12, 16, 20, 47]:
                    df[f'MA{p}'] = df['close'].rolling(window=p, min_periods=1).mean()
                create_chart(df, save_path)
            else:
                create_kline_skeleton_chart(df, save_path)

    return bg_dir

# ================= AI 语义特征解析接口 =================
import re
CORS(app, resources={r"/api/parse_custom_prompt": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})
@app.route('/api/parse_custom_prompt', methods=['POST'])
def parse_custom_prompt():
    """
    调用 DeepSeek 大模型，将用户手写的形态描述文本拆解为结构化量化特征标签。
    返回 JSON 数组，每项包含 desc / hasValue / value / unit 字段。
    """
    data = request.get_json()
    user_text = data.get('text', '').strip()
    if not user_text:
        return jsonify({"success": False, "msg": "text is empty"}), 400

    from llm_agent import client

    system_prompt = (
        "You are a stock quantitative feature extraction engine. "
        "Read the user's free-text description of a stock pattern and extract AT MOST 3 concise, "
        "machine-executable quantitative indicator labels. Each label must be under 15 Chinese characters.\n"
        "IMPORTANT: You must also detect whether the feature contains a concrete numeric threshold "
        "(such as '20%', '15 days', 'deviation > 5'). If so, extract the numeric value and its unit.\n"
        "Return ONLY a valid JSON array (no markdown, no explanation) with this exact structure:\n"
        '[{"desc": "...", "hasValue": true/false, "value": number or omitted, "unit": "..." or omitted}]\n'
        "Example input: 'MA4金叉上穿后暴涨20%，均线前期高度纠缠超过15天，成交量突破时放大'\n"
        'Example output: [{"desc":"MA4金叉上穿后暴涨","hasValue":true,"value":20,"unit":"%"},'
        '{"desc":"均线前期高度纠缠持续","hasValue":true,"value":15,"unit":"天"},'
        '{"desc":"成交量突破时放大","hasValue":false}]'
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0,
            max_tokens=512
        )

        raw = response.choices[0].message.content.strip()
        # 清理 markdown 标记
        raw = re.sub(r'^```json\n|^```\n|```$', '', raw, flags=re.MULTILINE).strip()

        import json
        features = json.loads(raw)

        # 验证结构
        if not isinstance(features, list):
            raise ValueError("not a list")
        for f in features:
            if 'desc' not in f or 'hasValue' not in f:
                raise ValueError("missing required field")
            if f['hasValue']:
                f.setdefault('value', 0)
                f.setdefault('unit', '')

        usage = response.usage
        print(f"[AI特征解析] tokens: {usage.prompt_tokens}+{usage.completion_tokens}={usage.total_tokens}")

        return jsonify({"success": True, "features": features})

    except Exception as e:
        print(f"[AI特征解析] 失败: {e}")
        return jsonify({"success": False, "msg": str(e)}), 500

# ================= 生成式数据增强：虚拟样本生成 =================
CORS(app, resources={r"/api/generate_synthetic_samples": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})
@app.route('/api/generate_synthetic_samples', methods=['POST'])
def generate_synthetic_samples():
    """
    条件 TimeGAN 生成式数据增强：
    Phase 1 — 统计引导生成器（AR(1) + 骨架收益率层面混合 + 种子经验分布）
    Phase 2 — 轻量条件 VAE-GAN（少样本快速微调，可选）
    支持递归生成：feedback_data/good_samples/bad_samples/generation
    """
    data = request.get_json()
    seeds = data.get('seeds', [])
    skeleton = data.get('condition_skeleton', [])
    features = data.get('condition_features', [])
    analysis_mode = data.get('analysis_mode', 'KLINE')
    ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])
    num_samples = data.get('num_samples', 8)
    # 递归生成参数
    good_samples = data.get('good_samples', [])
    bad_samples = data.get('bad_samples', [])
    generation = data.get('generation', 1)

    if not seeds or len(seeds) == 0:
        return jsonify({"success": False, "msg": "no seed data"}), 400

    try:
        from conditional_timegan import generate_synthetic_data
        t0 = time.time()
        samples = generate_synthetic_data(
            seeds, skeleton, features, ma_list, num_samples,
            generation=generation, good_samples=good_samples, bad_samples=bad_samples
        )
        elapsed = time.time() - t0

        synthetic_results = []
        for i, sample in enumerate(samples):
            synthetic_results.append({
                'sample_id': f'GEN{generation}_SYNTH_{i + 1:03d}',
                'generation': generation,
                'recent_data_raw': sample
            })

        print(f"[TimeGAN] 第{generation}代生成 {len(synthetic_results)} 个样本, 耗时 {elapsed:.2f}s")
        return jsonify({"success": True, "synthetic_results": synthetic_results})

    except Exception as e:
        print(f"[TimeGAN] 失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "msg": str(e)}), 500


# ======================== 正态分布特征校准 ========================
CORS(app, resources={r"/api/calibrate_features": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

def _compute_segment_features(raw_data):
    """从 OHLCV+MA 数据计算量化特征值"""
    if not raw_data or len(raw_data) < 2:
        return {}
    closes = [float(d.get('close', 0) or 0) for d in raw_data]
    highs = [float(d.get('high', 0) or 0) for d in raw_data]
    lows = [float(d.get('low', 0) or 0) for d in raw_data]
    closes = [c for c in closes if c > 0]
    highs = [h for h in highs if h > 0]
    lows = [l for l in lows if l > 0]
    if len(closes) < 2:
        return {}

    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    mean_r = sum(returns) / len(returns)
    std_r = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5

    avg_close = sum(closes) / len(closes)
    amplitude = ((max(highs) - min(lows)) / avg_close * 100) if highs and lows else 0

    peak = closes[0]
    max_dd = 0.0
    for c in closes:
        if c > peak:
            peak = c
        dd = (peak - c) / peak
        if dd > max_dd:
            max_dd = dd

    trend = ((closes[-1] / closes[0]) - 1) * 100

    # MA entanglement
    ma_keys = ['MA4', 'MA8', 'MA12', 'MA16', 'MA20', 'MA47']
    ent_sum = 0.0
    ent_count = 0
    for d in raw_data:
        vals = [float(d.get(k, 0) or 0) for k in ma_keys]
        vals = [v for v in vals if v > 0]
        if len(vals) >= 2:
            m = sum(vals) / len(vals)
            s = (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5
            ent_sum += s / m
            ent_count += 1
    entanglement = (ent_sum / ent_count * 100) if ent_count > 0 else 0

    return {
        'volatility': std_r * 100,
        'trend': trend,
        'amplitude': amplitude,
        'maxDrawdown': max_dd * 100,
        'entanglement': entanglement,
    }


@app.route('/api/calibrate_features', methods=['POST'])
def calibrate_features():
    """正态分布特征范围校准：μ ± 1.96σ (95% CI) + 负样本截断"""
    try:
        data = request.get_json(force=True)
        ratings = data.get('ratings', [])
        current_features = data.get('current_features', [])

        # 1. 计算每个评分片段的特征值
        seg_features = []
        for item in ratings:
            feats = _compute_segment_features(item.get('recent_data_raw', []))
            if feats:
                seg_features.append({**feats, '_rating': item.get('rating', 0)})

        # 2. 分离正负样本
        pos_vals = [s for s in seg_features if s['_rating'] >= 4]
        neg_vals = [s for s in seg_features if s['_rating'] <= 2]

        # 特征 key → desc 映射
        feat_key_map = {
            '波动': 'volatility', '振幅': 'amplitude', '回撤': 'maxDrawdown',
            '趋势': 'trend', '纠缠': 'entanglement', '密集': 'entanglement',
        }

        updated = []
        for feat in current_features:
            desc = feat.get('desc', '')
            # 匹配特征 key
            feat_key = None
            for kw, key in feat_key_map.items():
                if kw in desc:
                    feat_key = key
                    break
            if not feat_key:
                updated.append(feat)
                continue

            vals = [s[feat_key] for s in pos_vals if feat_key in s]

            if len(vals) >= 3:
                mu = float(np.mean(vals))
                sigma = float(np.std(vals))
                feat['center'] = round(mu, 2)
                feat['min'] = round(mu - 1.96 * sigma, 2)
                feat['max'] = round(mu + 1.96 * sigma, 2)
            elif len(vals) > 0:
                prior = feat.get('initial', feat.get('center', 0))
                mu = 0.5 * prior + 0.5 * float(np.mean(vals))
                feat['center'] = round(mu, 2)
                feat['min'] = round(mu * 0.8, 2)
                feat['max'] = round(mu * 1.2, 2)

            # 负样本边界截断
            for neg_s in neg_vals:
                if feat_key in neg_s:
                    v = neg_s[feat_key]
                    if feat['min'] < v < feat['max']:
                        if v > feat['center']:
                            feat['max'] = round(min(feat['max'], v - 0.5), 2)
                        else:
                            feat['min'] = round(max(feat['min'], v + 0.5), 2)

            updated.append(feat)

        # 3. 静默更新 brush_history.json
        try:
            mode_index = data.get('mode_index', '')
            if mode_index and os.path.exists(BRUSH_HISTORY_FILE):
                with open(BRUSH_HISTORY_FILE, 'r') as f:
                    history = json.load(f)
                for ts, rec in history.items():
                    pass  # 静默更新，不强制
        except Exception:
            pass

        print(f"[特征校准] 正样本{len(pos_vals)}个, 负样本{len(neg_vals)}个, 更新{len(updated)}个特征")
        return jsonify({"success": True, "updated_features": updated})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "msg": str(e)}), 500


# app.py 中的 train_custom_model 接口
@app.route('/train_custom_model', methods=['POST'])
def train_custom_model():
    print(f"\n{'=' * 40}")
    print("🧠 [开始自定义模型训练流程]")

    data = request.get_json()
    model_name = data.get('name')
    segments = data.get('segments')  # 前端传来的三维数据

    # 1. 基础校验
    if not segments or len(segments) == 0:
        print("❌ 错误: 未接收到任何训练样本数据")
        return jsonify({"success": False, "msg": "未选中任何片段"}), 400

    try:

        # 2. 【核心智能决策】：根据第一只股票的第一个数据点，自适应判断当前是 K线 还是 均线 模式！
        first_segment = segments[0]
        first_row = first_segment[0] if isinstance(first_segment, list) else first_segment.iloc[0].to_dict()

        analysis_mode = data.get('analysisMode')
        negative_segments = data.get('negative_segments', [])
        print(f"📊 [调试信息] 正样本{len(segments)}个, 负样本{len(negative_segments)}个, 模式={analysis_mode}")

        if analysis_mode == 'KLINE':
            print("📈 [模式决策] 前端明确指定为: K线形态训练模式")
        else:
            print("📊 [模式决策] 前端明确指定为: 均线形态训练模式")

        # 3. 创建专属图像数据集目录 (存入你指定的 Images 下)
        image_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'version525', 'data', 'Images')
        save_dir = os.path.join(image_root, model_name)
        os.makedirs(save_dir, exist_ok=True)

        # 3.1 模型专属背景目录
        model_bg_dir = os.path.join(save_dir, "background")
        os.makedirs(model_bg_dir, exist_ok=True)

        # 4. 自动绘制训练图片
        print(f"🖼️ 正在自动生成训练图片: {len(segments)} 张")
        for i, seg in enumerate(segments):
            df = pd.DataFrame(seg)
            save_path = os.path.join(save_dir, f"sample_{i}.jpg")

            if analysis_mode == 'MA':
                # 均线模式：只画均线
                create_chart(df, save_path)
            else:
                # K线模式：只画标准 K 线蜡烛图
                create_kline_skeleton_chart(df, save_path)

        # 5. 准备背景参照类图片
        # 优先用用户提供的负样本，不足再用真实股票/随机游走补充
        user_bg_count = 0
        if negative_segments and len(negative_segments) > 0:
            print(f"🖼️ 用户提供了 {len(negative_segments)} 个负样本，生成背景图片...")
            for i, seg in enumerate(negative_segments):
                try:
                    df_neg = pd.DataFrame(seg)
                    bg_save_path = os.path.join(model_bg_dir, f"user_neg_{i}.jpg")
                    if analysis_mode == 'MA':
                        create_chart(df_neg, bg_save_path)
                    else:
                        create_kline_skeleton_chart(df_neg, bg_save_path)
                    user_bg_count += 1
                except Exception:
                    pass

        # 不足15张时自动补充
        needed = max(15, len(segments)) - user_bg_count
        if needed > 0:
            bg_pool_codes = []
            try:
                stock_pool_data = data.get('stock_pool', [])
                bg_pool_codes = [s['code'] if isinstance(s, dict) else s for s in stock_pool_data][:50]
            except Exception:
                pass
            print(f"   用户负样本 {user_bg_count} 张，补充 {needed} 张...")
            ensure_background_class(image_root, num_samples=needed,
                                    analysis_mode=analysis_mode, stock_pool_codes=bg_pool_codes,
                                    model_bg_dir=model_bg_dir)
        else:
            print(f"   ✅ 用户负样本已满足背景需求 ({user_bg_count} 张)")

        # 6. 动态计算 K-Shot 和 Q-Query
        num_images = len(segments)
        k_shot = max(1, num_images // 2)
        q_query = max(1, num_images - k_shot)
        print(f"⚙️ 自动适配小样本学习设置: 2-Way, {k_shot}-Shot, {q_query}-Query")

        # 7. 调用你 main.py 里的元学习微调引擎
        success = meta_main.run_meta_training_pipeline(model_name, save_dir, k_shot, q_query, epochs=50)

        if success:
            # 8. 【成果同步】：计算并保存背景参照类的特征原型
            from few_shot_utils import get_ai_engine
            model = meta_main.FewShotKLineModel().to(DEVICE)
            model.adapter.load_state_dict(
                torch.load(os.path.join("custom_modes", f"{model_name}_adapter.pth"), map_location=DEVICE))
            model.eval()

            with torch.no_grad():
                bg_paths = [os.path.join(model_bg_dir, f) for f in os.listdir(model_bg_dir) if f.endswith('.jpg')]
                bg_tensors = torch.stack([meta_main.transform(Image.open(p).convert('RGB')) for p in bg_paths]).to(
                    DEVICE)
                bg_feats = model(bg_tensors).cpu().numpy()
                bg_prototype = np.mean(bg_feats, axis=0)
                bg_prototype /= (np.linalg.norm(bg_prototype) + 1e-8)
                np.save(os.path.join("custom_modes", f"{model_name}_bg.npy"), bg_prototype)
                print(f"💾 模型专属背景原型已固化: {model_name}_bg.npy")

            # 9. 保存骨架和片段数据到模型目录的元数据文件
            import json as _json
            meta_data = {
                'analysisMode': analysis_mode,
                'custom_skeleton': data.get('custom_skeleton', []),
                'segmentData': segments[:3] if isinstance(segments, list) else [],
            }
            meta_path = os.path.join(save_dir, "meta.json")
            with open(meta_path, 'w', encoding='utf-8') as f:
                _json.dump(meta_data, f, ensure_ascii=False, indent=2)
            print(f"💾 模型元数据已保存: {meta_path}")

            # 10. 写入 JSON 配置索引
            formatted_lines = ["MA4", "MA8", "MA12", "MA16", "MA20", "MA47"]
            new_mode_entry = {
                "index": model_name,
                "name": model_name,
                "lines": formatted_lines,
                "is_custom": True,
                "analysis_mode": analysis_mode,  # 存入自适应判定出来的模式
                "recentNDaysValue": "近30天",
                "modeDescription": f"基于 {len(segments)} 个用户勾选样本元学习微调而成"
            }

            current_modes = read_json_data()
            current_modes = [m for m in current_modes if m['name'] != model_name]
            current_modes.append(new_mode_entry)
            write_json_data(current_modes)
            print(f"📝 模式索引已注册至 modeListSelf.json")

            print(f"✨ [训练任务圆满完成] 模式名称: {model_name}")
            print(f"{'=' * 40}\n")
            return jsonify({"success": True, "mode_id": model_name, "msg": f"模型【{model_name}】训练完成"})
        else:
            return jsonify({"success": False, "msg": "微调训练失败"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "msg": str(e)}), 500

# ================= 新增：专门处理大模型语义检索的接口 =================
CORS(app, resources={r"/find_similar_stocks_llm": {
    "origins": Config.CORS_ORIGINS,
    "methods": ["POST", "OPTIONS"],
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})
@app.route('/find_similar_stocks_llm', methods=['POST'])
def handle_find_similar_stocks_llm():
    try:
        data = request.get_json(force=True)

        # 1. 提取大模型专属的语义参数并生成代码
        semantic_features = data.get('semantic_features', {})
        tags = semantic_features.get('tags', [])
        custom_prompt = semantic_features.get('custom_prompt', "")

        print("\n" + "🚀" * 20)
        print(f"🤖 [AI 智能体已接管请求] 正在解析多模态语义特征...")

        from llm_agent import generate_ai_filter
        ai_filter_func = generate_ai_filter(tags, custom_prompt)

        print("🚀" * 20 + "\n")

        # 2. 提取【基准片段】和【历史扫描区间】参数
        target_code = data.get('target_code', '')
        # 【核心修复】：强行截取前10位，把 "2016-01-02T00:00:00.000Z" 变成纯净的 "2016-01-02"
        target_start_date = str(data.get('target_start_date', ''))[:10]
        target_end_date = str(data.get('target_end_date', ''))[:10]
        search_start_date = str(data.get('search_start_date', '2016-01-01'))[:10]
        search_end_date = str(data.get('search_end_date', '2024-12-31'))[:10]

        stock_pool = data.get('stock_pool', [])
        ma_list = data.get('ma_list', [4, 8, 12, 16, 20, 47])
        data_folder = data.get('data_folder', DATA_FOLDER)

        print(f"🔎[历史回测模式开启] 全局扫描区间: {search_start_date} 至 {search_end_date}")

        ma_cols = [f"MA{m}" for m in ma_list]  # 需要对比的均线列名

        # ==========================================
        # 【核心新增1】：获取你画框的基准数据，并动态确定窗口大小
        # ==========================================
        ts_target_code = f"{target_code}.SH" if str(target_code).startswith('6') else f"{target_code}.SZ"

        # 【修复】：计算前置缓冲期 (往前推 100 天，确保连半年线 MA120 都能算出来)
        dt_target_start = pd.to_datetime(target_start_date)
        padded_start_date = (dt_target_start - pd.Timedelta(days=100)).strftime('%Y-%m-%d')

        # 1. 先用带缓冲期的时间去获取长周期数据
        target_df_full = get_stock_data(ts_target_code, padded_start_date, target_end_date, data_folder=data_folder)

        if target_df_full is None or target_df_full.empty:
            return jsonify({"error": "无法获取基准片段数据，请重新框选"}), 400

        # 2. 在长周期数据上计算所有的 MA 均线（此时不会产生全是 NaN 的情况了）
        target_df_full = calculate_ma(target_df_full, ma_list)

        # 3. 均线算完后，用 Pandas 切片把时间精确卡回用户在前端实际框选的范围！
        target_df_full['trade_date_dt'] = pd.to_datetime(target_df_full['trade_date'])
        target_df = target_df_full[
            (target_df_full['trade_date_dt'] >= dt_target_start) &
            (target_df_full['trade_date_dt'] <= pd.to_datetime(target_end_date))
            ].copy()

        if target_df.empty:
            return jsonify({"error": "基准片段均线计算后数据为空，请尝试框选更长的时间"}), 400

        # 动态设定窗口大小：优先用前端滑块传来的 window_size，未传/非法则回退为实际框选天数
        try:
            requested_window_size = int(data.get('window_size') or 0)
        except (TypeError, ValueError):
            requested_window_size = 0
        if requested_window_size > 0:
            window_size = max(5, min(250, requested_window_size))  # 夹取到合法范围 [5, 250]
        else:
            window_size = len(target_df)
        step_size = 3  # 步长设小一点，搜得更细致

        window_src = f"（前端滑块指定: {requested_window_size}）" if requested_window_size > 0 else "（未指定，使用框选长度）"
        print(f"🎯 基准片段确立: {target_code} ({target_start_date} 至 {target_end_date}), 窗口大小: {window_size}天{window_src}")
        print(f"🔎 全局扫描区间: {search_start_date} 至 {search_end_date}")

        # ==========================================
        # 【核心新增2】：定义纯数学形态相似度计算函数 (Pearson)
        # ==========================================
        # 算法1：均线形态相似度 (Pearson 相关系数)
        # ==========================================
        # ==========================================
        # 优化后：基于单线（Close 或 核心主图线）的形态相似度
        # ==========================================
        from deal_sim_time_range import unify_series_length  # 不等长窗口的均线序列对齐（线性插值）

        def calc_shape_similarity(df_target, df_window, ma_cols=None):
            try:
                # 多线 Pearson：对每条均线分别算皮尔逊相关系数，再取算术平均
                if ma_cols is None:
                    ma_cols = [c for c in df_target.columns if c.startswith('MA')]
                if not ma_cols:
                    ma_cols = ['close']
                corrs = []
                for col in ma_cols:
                    if col not in df_target.columns or col not in df_window.columns:
                        continue
                    t = np.asarray(df_target[col].values, dtype=float)
                    w = np.asarray(df_window[col].values, dtype=float)
                    # 窗口长度≠模板长度时（前端滑块可调窗口），先线性插值统一到相同长度再算 Pearson
                    if len(t) != len(w):
                        t, w = unify_series_length(t, w)  # 默认统一到 max(len)：长者不动、短者拉伸
                    mask = ~(np.isnan(t) | np.isnan(w))
                    if mask.sum() < 3:
                        continue
                    t, w = t[mask], w[mask]
                    if np.std(t) < 1e-8 or np.std(w) < 1e-8:
                        continue
                    # Z-score 标准化
                    tn = (t - t.mean()) / (t.std() + 1e-8)
                    wn = (w - w.mean()) / (w.std() + 1e-8)
                    corr = np.corrcoef(tn, wn)[0, 1]
                    corrs.append(0.0 if np.isnan(corr) else float(corr))
                return float(np.mean(corrs)) if corrs else 0.0
            except Exception:
                return 0.0

        # ==========================================
        # 🌟 算法2：K线骨架相似度 (DTW 动态时间弯曲)
        # ==========================================
        def calc_kline_dtw_similarity(df_target, df_window):
            try:
                # 提取收盘价序列作为趋势代表
                t_data = df_target['close'].values
                w_data = df_window['close'].values

                # 归一化 (Min-Max) 以消除绝对价格差异
                t_norm = (t_data - np.min(t_data)) / (np.ptp(t_data) + 1e-8)
                w_norm = (w_data - np.min(w_data)) / (np.ptp(w_data) + 1e-8)

                n, m = len(t_norm), len(w_norm)
                # 初始化 DTW 矩阵
                dtw_matrix = np.full((n + 1, m + 1), float('inf'))
                dtw_matrix[0, 0] = 0

                # 动态规划计算最小弯曲路径距离
                for i in range(1, n + 1):
                    for j in range(1, m + 1):
                        cost = abs(t_norm[i - 1] - w_norm[j - 1])
                        dtw_matrix[i, j] = cost + min(dtw_matrix[i - 1, j],  # 插入
                                                      dtw_matrix[i, j - 1],  # 删除
                                                      dtw_matrix[i - 1, j - 1])  # 匹配

                dist = dtw_matrix[n, m]
                # 将距离转化为相似度得分 (距离越小，相似度越接近 1.0)
                sim = np.exp(-dist / max(n, m))
                return float(sim) if sim > 0 else 0.0
            except Exception as e:
                print("DTW 计算出错:", e)
                return 0.0

        results = []
        # 获取前端传来的分析模式
        analysis_mode = data.get('analysis_mode', 'MA')
        # 【新增】：初始化三个计数器
        stats = {"total": 0, "after_llm_filter": 0, "after_similarity_filter": 0}
        # 3. 开启真正的历史滑动窗口扫描
        for code in stock_pool:
            ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
            df = get_stock_data(ts_code, search_start_date, search_end_date, data_folder=data_folder)

            if df is None or df.empty or len(df) < window_size: continue
            df = calculate_ma(df, ma_list)
            if df.empty: continue
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

            # 滑动窗口
            for i in range(0, len(df) - window_size + 1, step_size):
                window_df = df.iloc[i: i + window_size].copy()
                stats["total"] += 1  # 计数：所有片段
                # 第一关：AI 大模型语义过滤剪枝
                if ai_filter_func is not None and not ai_filter_func(window_df):
                    stats["after_llm_filter"] += 1  # 计数：AI过滤的片段
                    continue
                    # 第二关：根据模式，分发给不同的底层数学引擎
                if analysis_mode == 'KLINE':
                    # K 线模式 -> 走 DTW 算法
                    sim_score = calc_kline_dtw_similarity(target_df, window_df)
                else:
                    # 均线模式 -> 走 皮尔逊 算法
                    sim_score = calc_shape_similarity(target_df, window_df, ma_cols)

                start_dt = window_df.iloc[0]['trade_date']
                end_dt = window_df.iloc[-1]['trade_date']

                # 相似度阈值
                if sim_score > 0.6:
                    stats["after_similarity_filter"] += 1  # 【修复】：在这里加计数！
                    mode_str = "K线DTW" if analysis_mode == 'KLINE' else "均线Pearson"
                    print(
                        f"    ✨ [命中] {code} ({start_dt} 至 {end_dt}) | AI逻辑: 通过 | {mode_str}相似度: {sim_score:.4f}")

                    results.append({
                        "stock_code": code,
                        "stock_name": code,
                        "similarity": round(sim_score, 4),
                        "recent_data": window_df.to_dict('records'),
                        "ma_list": ma_list,
                    })
                else:
                    # 如果逻辑符合，但长得实在太丑（相似度太低），也打印出来看看
                    print(
                        f"    ❌ [淘汰] {code} ({start_dt} 至 {end_dt}) | AI逻辑: 通过 | 但形态相似度过低: {sim_score:.4f}")

        # 4. 按真实的相似度降序排列，将最像的放在最上面
        results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:50]

        # 5. 宽松兜底：如果 AI 规则过滤太严（通过率<5%）导致0结果，跳过第一关重扫
        ai_pass_rate = (stats['total'] - stats['after_llm_filter']) / max(stats['total'], 1)
        if len(results) == 0 and ai_pass_rate < 0.05 and stats['total'] > 0:
            print(f"⚠️ [AI规则太严] 通过率仅 {ai_pass_rate*100:.1f}%，启动宽松模式：跳过AI规则，仅用相似度筛选")
            lenient_threshold = 0.45
            stats["after_llm_filter"] = 0  # 宽松模式不计AI过滤
            stats["after_similarity_filter"] = 0
            for code in stock_pool:
                ts_code = f"{code}.SH" if str(code).startswith('6') else f"{code}.SZ"
                df = get_stock_data(ts_code, search_start_date, search_end_date, data_folder=data_folder)
                if df is None or df.empty or len(df) < window_size: continue
                df = calculate_ma(df, ma_list)
                if df.empty: continue
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

                for i in range(0, len(df) - window_size + 1, step_size):
                    window_df = df.iloc[i: i + window_size].copy()
                    if analysis_mode == 'KLINE':
                        sim_score = calc_kline_dtw_similarity(target_df, window_df)
                    else:
                        sim_score = calc_shape_similarity(target_df, window_df, ma_cols)
                    if sim_score > lenient_threshold:
                        stats["after_similarity_filter"] += 1
                        results.append({
                            "stock_code": code,
                            "stock_name": code,
                            "similarity": round(sim_score, 4),
                            "recent_data": window_df.to_dict('records'),
                            "ma_list": ma_list,
                        })
            results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:50]
            print(f"✅ [宽松模式] 补救找到 {len(results)} 个结果（阈值 {lenient_threshold}）")

        print(
            f"✅ 历史扫描完成: 总计{stats['total']}个，AI逻辑过滤{stats['after_llm_filter']}个，最终命中{stats['after_similarity_filter']}个")

        return jsonify({
            "result": results,
            "filter_stats": stats,
            "count": len(results),
            "target_code": target_code,
            "base_ma_periods": ma_list,
            "base_segment": target_df[['trade_date'] + ma_cols].to_dict('records')
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ 处理大模型检索请求出错: {str(e)}")
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500

CORS(app, resources={r"/api/extract_skeleton": {"origins": Config.CORS_ORIGINS, "methods": ["POST", "OPTIONS"]}})
@app.route('/api/extract_skeleton', methods=['POST'])
def extract_skeleton():
    try:
        data = request.get_json(force=True)
        target_code = data.get('target_code')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        data_folder = data.get('data_folder', DATA_FOLDER)

        # 1. 获取包含开高低收的真实 K线数据
        ts_code = f"{target_code}.SH" if str(target_code).startswith('6') else f"{target_code}.SZ"
        df = get_stock_data(ts_code, start_date, end_date, data_folder=data_folder)

        if df is None or df.empty:
            return jsonify({"success": False, "msg": "未获取到该区间的历史数据"})

        # 确保 trade_date 是 datetime 类型
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        # 2. 初始化你的学习器配置
        config = {
            'min_time_gap': 2,
            'importance_threshold': 1.0,
            'min_points': 4,
            'max_points': 8
        }
        learner = SkeletonLearner(config)

        # 3. 提取骨架
        start_idx = 0
        end_idx = len(df) - 1
        skeleton = learner.extract_skeleton_from_segment(df, start_idx, end_idx)

        # 4. 转换为前端画图需要的格式
        points = []
        for p in skeleton.points:
            points.append({
                "id": str(uuid.uuid4()),  # 生成前端去重用的唯一ID
                "date": p.date.strftime('%Y-%m-%d'),
                "price": float(p.price),
                "weight": 1.0,  # 默认交互权重
                "type": p.point_type
            })

        return jsonify({"success": True, "points": points})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "msg": f"骨架提取算法报错: {str(e)}"}), 500
@app.route('/save_brush_record', methods=['POST'])
def save_brush_record():
    data = request.get_json()
    ts = str(data.get('timestamp'))

    # 🌟【新增】：将 analysisMode 和提取好的片段数据(segmentData)存入记录
    record = {
        'startDate': data.get('startDate'),
        'endDate': data.get('endDate'),
        'dynamicFeatures': data.get('dynamicFeatures'),
        'analysisMode': data.get('analysisMode'),
        'segmentData': data.get('segmentData'),
        'custom_skeleton': data.get('custom_skeleton', []),
        'extracted_features': data.get('extracted_features', [])
    }
    history = {}
    if os.path.exists(BRUSH_HISTORY_FILE):
        with open(BRUSH_HISTORY_FILE, 'r') as f:
            try:
                history = json.load(f)
            except:
                history = {}

    history[ts] = record

    with open(BRUSH_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)  # 加上 indent=4 让 JSON 可读

    return jsonify({"success": True})

@app.route('/api/get_model_meta', methods=['POST'])
def get_model_meta():
    """获取自定义模型的元数据（骨架、片段、分析模式）"""
    try:
        data = request.get_json()
        model_name = data.get('model_name', '')
        # 优先从模型图片目录读取
        image_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'few_shot_learning', 'version525', 'data', 'Images')
        meta_path = os.path.join(image_root, model_name, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            return jsonify({"success": True, "meta": meta})
        # 兜底：从 custom_modes 读取旧格式
        old_meta_path = os.path.join("custom_modes", f"{model_name}_meta.json")
        if os.path.exists(old_meta_path):
            with open(old_meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            return jsonify({"success": True, "meta": meta})
        return jsonify({"success": False, "msg": "元数据不存在"})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route('/get_brush_info', methods=['POST'])
def get_brush_info():
    try:
        data = request.get_json()
        ts = str(data.get('timestamp'))
        if os.path.exists(BRUSH_HISTORY_FILE):
            with open(BRUSH_HISTORY_FILE, 'r') as f:
                history = json.load(f)
                if ts in history:
                    return jsonify({"success": True, "info": history[ts]})
        return jsonify({"success": False, "msg": "记录不存在"})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500
@app.route('/update_brush_params', methods=['POST'])
def update_brush_params():
    data = request.get_json()
    ts = str(data.get('timestamp'))
    new_vol = data.get('new_volatility')

    # 读取现有的 brush_history.json
    if os.path.exists('brush_history.json'):
        with open('brush_history.json', 'r') as f:
            history = json.load(f)

        if ts in history:
            # 更新其中波动率特征的数值
            for feat in history[ts].get('dynamicFeatures', []):
                if '波动幅度' in feat['desc']:
                    feat['value'] = new_vol

            # 写回文件
            with open('brush_history.json', 'w') as f:
                json.dump(history, f)
            return jsonify({"success": True})

    return jsonify({"success": False, "msg": "记录不存在"})

if __name__ == "__main__":
    app.run(debug=Config.DEBUG)