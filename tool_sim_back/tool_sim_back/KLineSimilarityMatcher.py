import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime, timedelta
import torch
from ultralytics import YOLO
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import time
import glob


class KLineSimilarityMatcher:
    # 修改初始化方法，使用预训练的YOLO模型
    def __init__(self, data_folder, model_path="E:/gitClone/tool_sim_back/models/weights/best.pt"):
        """
        初始化K线相似性匹配器
        :param data_folder: 股票数据文件夹路径
        :param model_path: YOLO模型路径（如果为None，则使用预训练模型）
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 初始化K线相似性匹配器...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   数据文件夹: {data_folder}")
        start_time = time.time()

        self.data_folder = data_folder
        self.temp_image_folder = "temp_kline_images"
        os.makedirs(self.temp_image_folder, exist_ok=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   创建临时图像文件夹: {self.temp_image_folder}")

        # 加载YOLO模型
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   📦 加载YOLO模型...")
        try:
            if model_path and os.path.exists(model_path):
                print(f"[{datetime.now().strftime('%H:%M:%S')}]   使用指定模型: {model_path}")
                self.model = YOLO(model_path)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}]   使用预训练的YOLOv8n模型")
                self.model = YOLO('yolov8n.pt')  # 使用预训练的YOLOv8n模型

            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ✅ YOLO模型加载成功")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ❌ YOLO模型加载失败: {str(e)}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   🤔 将使用备用特征提取方法")
            self.model = None

        # 存储检测到的模式特征
        self.reference_patterns = {}
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   初始化参考模式存储字典")

        end_time = time.time()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 匹配器初始化完成，耗时: {end_time - start_time:.2f} 秒")
        print("-" * 80)

    def load_stock_data(self, stock_code, start_date=None, end_date=None):
        """
        加载股票数据
        :param stock_code: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 股票数据DataFrame
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📂 加载股票数据: {stock_code}")
        if start_date and end_date:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   日期范围: {start_date} ~ {end_date}")

        # 尝试不同的文件扩展名和股票代码后缀组合
        possible_files = []

        # 尝试不同的文件扩展名
        for ext in ['.xls', '.xlsx', '.csv']:
            # 尝试不同的股票代码格式
            for code_format in [
                stock_code,
                f"{stock_code}.SH",
                f"{stock_code}.SZ",
                stock_code.replace('.SH', '').replace('.SZ', '')
            ]:
                file_path = os.path.join(self.data_folder, f"{code_format}{ext}")
                if os.path.exists(file_path):
                    possible_files.append(file_path)

        if not possible_files:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 未找到股票数据文件: {stock_code}")
            return None

        # 使用第一个找到的文件
        file_path = possible_files[0]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 找到数据文件: {file_path}")

        try:
            # 根据文件扩展名读取文件
            if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📖 读取Excel文件...")
                df = pd.read_excel(file_path)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📖 读取CSV文件...")
                df = pd.read_csv(file_path)

            print(f"[{datetime.now().strftime('%H:%M:%S')}]   原始数据形状: {df.shape}")

            # 确保日期列存在并转换为datetime
            date_col = 'timestamps'  # 根据您的文件格式，日期列名为'timestamps'
            if date_col not in df.columns:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 未找到日期列: {date_col}")
                return None

            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   数据排序完成")

            # 筛选日期范围
            if start_date and end_date:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 筛选日期范围...")
                # 【新增：清洗日期字符串】
                # 将 "2016-01-02T00:00:00.000Z" 变为 "2016-01-02"
                clean_start = str(start_date).split('T')[0]
                clean_end = str(end_date).split('T')[0]

                # 使用清洗后的日期进行转换和对比
                start_ts = pd.to_datetime(clean_start)
                end_ts = pd.to_datetime(clean_end)

                # ...
                # 确保 mask 使用的是无时区的 Timestamp
                mask = (df[date_col] >= start_ts) & (df[date_col] <= end_ts)
                df = df.loc[mask]
                print(f"[{datetime.now().strftime('%H:%M:%S')}]   筛选后数据形状: {df.shape}")

            # 数据清洗：处理可能的NaN值
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧹 数据清洗: 处理NaN值...")
            numeric_cols = ['open', 'high', 'low', 'close', 'vol']
            for col in numeric_cols:
                if col in df.columns:
                    # 先向前填充，再向后填充，最后用0填充
                    df[col] = df[col].fillna(method='ffill').fillna(method='bfill').fillna(0)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]    处理列 '{col}' 的NaN值")

            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 成功加载 {len(df)} 条数据")
            return df

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 加载股票数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def generate_kline_image(self, df, image_path, title="", width=10, height=6):
        """
        生成K线图
        :param df: 股票数据DataFrame
        :param image_path: 图像保存路径
        :param title: 图表标题
        :param width: 图表宽度
        :param height: 图表高度
        :return: 是否成功生成
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 生成K线图: {title}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   保存路径: {image_path}")

        try:
            # 确保有足够的数据
            if df is None or len(df) < 5:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 数据不足，无法生成K线图")
                return False

            print(f"[{datetime.now().strftime('%H:%M:%S')}]   数据量: {len(df)} 条")

            # 确定价格列 - 根据您的文件格式调整列名
            open_col = 'open'
            high_col = 'high'
            low_col = 'low'
            close_col = 'close'
            volume_col = 'vol'  # 根据您的文件格式，成交量列名为'vol'
            date_col = 'timestamps'

            print(f"[{datetime.now().strftime('%H:%M:%S')}]   使用的列 - 日期: {date_col}, 开盘: {open_col}, "
                  f"最高: {high_col}, 最低: {low_col}, 收盘: {close_col}, 成交量: {volume_col}")

            # 准备数据 - 创建mplfinance所需的格式
            plot_data = df.set_index(date_col)
            plot_data = plot_data[[open_col, high_col, low_col, close_col]]
            plot_data.columns = ['Open', 'High', 'Low', 'Close']

            # 检查是否有成交量数据并处理NaN值
            volume_data = None
            if volume_col in df.columns:
                # 处理成交量数据中的NaN值
                volume_series = df[volume_col].fillna(0)
                if not volume_series.isna().all():  # 确保不是全部为NaN
                    # 添加Volume列到plot_data中（mplfinance要求列名为Volume）
                    plot_data['Volume'] = volume_series.values
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   包含成交量数据")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   ⚠️ 成交量数据全为NaN，将不绘制成交量")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}]   无成交量数据")

            # 创建图表
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎨 创建K线图表...")

            # 设置mplfinance参数
            mpf_style = mpf.make_marketcolors(
                up='red',
                down='green',
                edge='inherit',
                wick='inherit',
                volume='gray'
            )

            mpf_style = mpf.make_mpf_style(
                marketcolors=mpf_style,
                gridstyle=':',
                y_on_right=False
            )

            # 根据是否有有效的成交量数据决定是否绘制成交量
            add_volume = 'Volume' in plot_data.columns

            fig, axes = mpf.plot(
                plot_data,
                type='candle',
                title=title,
                style=mpf_style,
                volume=add_volume,
                figsize=(width, height),
                returnfig=True
            )

            # 保存图像
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 保存图像...")
            fig.savefig(image_path, bbox_inches='tight', dpi=100)
            plt.close(fig)


            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ K线图已保存: {image_path}")
            return True

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 生成K线图失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def detect_patterns(self, image_path, confidence_threshold=0.5):
        """
        使用YOLO检测K线图中的模式
        :param image_path: 图像路径
        :param confidence_threshold: 置信度阈值
        :return: 检测到的模式列表
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 检测K线模式: {os.path.basename(image_path)}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   置信度阈值: {confidence_threshold}")
        start_time = time.time()

        try:
            # 使用YOLO进行目标检测
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 运行YOLO检测...")
            results = self.model(image_path, conf=confidence_threshold)

            detected_patterns = []
            for result in results:
                boxes = result.boxes
                print(f"[{datetime.now().strftime('%H:%M:%S')}]   检测到 {len(boxes)} 个边界框")

                for box in boxes:
                    # 提取检测结果
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]

                    detected_patterns.append({
                        'class_name': class_name,
                        'class_id': class_id,
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2],
                        'center': [(x1 + x2) / 2, (y1 + y2) / 2]
                    })

                    print(f"[{datetime.now().strftime('%H:%M:%S')}]     ✅ 检测到模式: {class_name} "
                          f"(置信度: {confidence:.2f}, 位置: {[int(x1), int(y1), int(x2), int(y2)]})")

            end_time = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ✅ 模式检测完成，找到 {len(detected_patterns)} 个模式，"
                  f"耗时: {end_time - start_time:.2f} 秒")
            print("-" * 80)

            return detected_patterns

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ❌ 模式检测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def extract_pattern_features(self, patterns):
        """
        提取检测到的模式的特征
        :param patterns: 检测到的模式列表
        :return: 特征向量
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧮 提取模式特征...")
        start_time = time.time()

        features = []
        for i, pattern in enumerate(patterns):
            # 提取模式特征
            pattern_feature = [
                pattern['class_id'] / 100,  # 类别ID归一化
                pattern['confidence'],  # 置信度
                pattern['center'][0] / 1000,  # 中心X坐标归一化
                pattern['center'][1] / 1000,  # 中心Y坐标归一化
                (pattern['bbox'][2] - pattern['bbox'][0]) / 1000,  # 宽度归一化
                (pattern['bbox'][3] - pattern['bbox'][1]) / 1000  # 高度归一化
            ]

            features.extend(pattern_feature)
            print(f"[{datetime.now().strftime('%H:%M:%S')}]    模式 {i + 1} 特征提取完成: {pattern_feature}")

        # 如果未检测到模式，使用默认特征
        if not features:
            features = [0] * 6  # 6个特征维度
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ⚠️ 使用默认特征")

        features = np.array(features)
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   ✅ 特征提取完成，特征维度: {len(features)}，"
              f"耗时: {time.time() - start_time:.2f} 秒")
        print("-" * 80)

        return features

    def add_reference_pattern(self, target_code, start_date, end_date, label="target_pattern"):
        """
        添加参考模式
        :param target_code: 目标股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param label: 参考模式标签
        :return: 是否成功添加
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📌 添加参考模式: {label}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   目标股票: {target_code}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   时间范围: {start_date} ~ {end_date}")

        # 加载目标股票数据
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   1. 加载目标股票数据...")
        target_df = self.load_stock_data(target_code, start_date, end_date)
        if target_df is None:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ❌ 无法加载目标股票数据")
            return False

        # 生成K线图
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   2. 生成K线图...")
        image_path = os.path.join(self.temp_image_folder, f"{label}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        title = f"{target_code} {start_date}~{end_date}"
        if not self.generate_kline_image(target_df, image_path, title):
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ❌ 无法生成目标K线图")
            return False

        # 检测模式
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   3. 检测K线模式...")
        patterns = self.detect_patterns(image_path)

        # 提取特征
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   4. 提取模式特征...")
        features = self.extract_pattern_features(patterns)

        if features.size > 0:
            self.reference_patterns[label] = {
                'features': features,
                'patterns': patterns,
                'image_path': image_path,
                'stock_code': target_code,
                'start_date': start_date,
                'end_date': end_date
            }
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}]   ✅ 参考模式添加成功，当前参考模式数量: {len(self.reference_patterns)}")
            print("-" * 80)
            return True

        print(f"[{datetime.now().strftime('%H:%M:%S')}]   ❌ 参考模式添加失败")
        print("-" * 80)
        return False

    def find_similar_segments(self, stock_codes, window_size=20, step_size=5,
                              confidence_threshold=0.5, similarity_threshold=0.7):
        """
        在股票池中寻找相似的K线片段
        :param stock_codes: 股票代码列表
        :param window_size: 滑动窗口大小
        :param step_size: 滑动步长
        :param confidence_threshold: 置信度阈值
        :param similarity_threshold: 相似度阈值
        :return: 相似片段列表
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔎 开始在股票池中寻找相似K线片段...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   股票池大小: {len(stock_codes)}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   窗口大小: {window_size}, 步长: {step_size}")
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}]   置信度阈值: {confidence_threshold}, 相似度阈值: {similarity_threshold}")

        similar_segments = []
        total_segments_processed = 0

        for stock_idx, stock_code in enumerate(stock_codes):
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] 📈 处理股票 [{stock_idx + 1}/{len(stock_codes)}]: {stock_code}")

            # 加载股票数据
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   1. 加载股票数据...")
            stock_df = self.load_stock_data(stock_code)
            if stock_df is None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}]   ❌ 跳过股票 {stock_code}，无法加载数据")
                continue

            # 确定日期列
            date_col = 'timestamps'
            dates = stock_df[date_col].tolist()
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   数据量: {len(stock_df)} 条，日期列: {date_col}")

            # 计算可能的窗口数量
            num_windows = (len(stock_df) - window_size) // step_size + 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   可能的窗口数量: {num_windows}")

            # 滑动窗口遍历数据
            for i in range(0, len(stock_df) - window_size + 1, step_size):
                total_segments_processed += 1
                if total_segments_processed % 10 == 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   已处理 {total_segments_processed} 个片段...")

                window_df = stock_df.iloc[i:i + window_size]
                start_date = window_df[date_col].iloc[0].strftime('%Y-%m-%d')
                end_date = window_df[date_col].iloc[-1].strftime('%Y-%m-%d')

                # 生成K线图
                image_path = os.path.join(
                    self.temp_image_folder,
                    f"{stock_code}_{start_date}_{end_date}_{datetime.now().strftime('%H%M%S')}.png"
                )
                title = f"{stock_code} {start_date}~{end_date}"

                if not self.generate_kline_image(window_df, image_path, title):
                    continue

                # 检测模式
                patterns = self.detect_patterns(image_path, confidence_threshold)

                # 提取特征
                features = self.extract_pattern_features(patterns)

                if features.size == 0:
                    continue

                # 计算与所有参考模式的相似度
                for label, ref_data in self.reference_patterns.items():
                    ref_features = ref_data['features']

                    # 确保特征向量长度相同
                    min_len = min(len(features), len(ref_features))
                    if min_len == 0:
                        similarity = 0
                    else:
                        # 截取相同长度的特征向量
                        q_features = features[:min_len]
                        r_features = ref_features[:min_len]

                        # 计算余弦相似度
                        similarity = cosine_similarity([q_features], [r_features])[0][0]

                    if similarity >= similarity_threshold:
                        similar_segments.append({
                            'stock_code': stock_code,
                            'start_date': start_date,
                            'end_date': end_date,
                            'similarity': similarity,
                            'reference_pattern': label,
                            'image_path': image_path,
                            'patterns_detected': len(patterns)
                        })

                        print(
                            f"[{datetime.now().strftime('%H:%M:%S')}]   🎯 找到相似片段: {stock_code} {start_date}~{end_date} "
                            f"(相似度: {similarity:.4f}, 参考模式: {label})")

            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ✅ 完成股票 {stock_code} 的处理")

        # 按相似度排序
        similar_segments.sort(key=lambda x: x['similarity'], reverse=True)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 搜索完成，找到 {len(similar_segments)} 个相似片段")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   总共处理了 {total_segments_processed} 个K线片段")
        print("-" * 80)

        return similar_segments

    def clear_temp_files(self):
        """清空临时文件"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧹 清空临时文件...")
        temp_files = glob.glob(os.path.join(self.temp_image_folder, "*.png"))
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   找到 {len(temp_files)} 个临时文件")

        for file in temp_files:
            try:
                os.remove(file)
                print(f"[{datetime.now().strftime('%H:%M:%S')}]    删除临时文件: {os.path.basename(file)}")
            except Exception as e:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}]    ❌ 删除文件失败: {os.path.basename(file)}, 错误: {str(e)}")

        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 临时文件清理完成")
        print("-" * 80)

    def clear_references(self):
        """清空所有参考模式"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧹 清空参考模式...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   当前参考模式数量: {len(self.reference_patterns)}")
        self.reference_patterns = {}
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 参考模式已清空")
        print("-" * 80)