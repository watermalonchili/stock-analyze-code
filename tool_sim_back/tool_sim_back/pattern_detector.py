"""
W底形态检测模块
负责检测和提取W底形态
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import pickle
import warnings
warnings.filterwarnings('ignore')


class WBottomPattern:
    """W底形态数据类"""

    def __init__(self, stock_code: str, df: pd.DataFrame,
                 left_bottom_idx: int, head_idx: int,
                 right_bottom_idx: int, confirm_idx: int,
                 pattern_info: Dict):
        """
        初始化W底形态

        参数:
            stock_code: 股票代码
            df: 股票数据
            left_bottom_idx: 左底索引
            head_idx: 头部索引
            right_bottom_idx: 右底索引
            confirm_idx: 确认点索引
            pattern_info: 形态信息字典
        """
        self.stock_code = stock_code
        self.df = df
        self.left_bottom_idx = left_bottom_idx
        self.head_idx = head_idx
        self.right_bottom_idx = right_bottom_idx
        self.confirm_idx = confirm_idx
        self.pattern_info = pattern_info

    def get_segment(self, expand_days: int = 5) -> pd.DataFrame:
        """
        获取形态所在的数据段

        参数:
            expand_days: 前后扩展天数

        返回:
            数据段DataFrame
        """
        start_idx = max(0, self.left_bottom_idx - expand_days)
        end_idx = min(len(self.df) - 1, self.confirm_idx + expand_days)
        return self.df.loc[start_idx:end_idx].copy().reset_index(drop=True)

    def get_key_points(self) -> Dict[str, Tuple[int, float, pd.Timestamp]]:
        """
        获取关键点信息

        返回:
            关键点字典: {点名称: (索引, 价格, 日期)}
        """
        return {
            'left_bottom': (self.left_bottom_idx,
                           self.df.loc[self.left_bottom_idx, 'low'],
                           self.df.loc[self.left_bottom_idx, 'trade_date']),
            'head': (self.head_idx,
                    self.df.loc[self.head_idx, 'high'],
                    self.df.loc[self.head_idx, 'trade_date']),
            'right_bottom': (self.right_bottom_idx,
                            self.df.loc[self.right_bottom_idx, 'low'],
                            self.df.loc[self.right_bottom_idx, 'trade_date']),
            'confirm': (self.confirm_idx,
                       self.df.loc[self.confirm_idx, 'high'],
                       self.df.loc[self.confirm_idx, 'trade_date'])
        }

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'left_bottom_idx': self.left_bottom_idx,
            'head_idx': self.head_idx,
            'right_bottom_idx': self.right_bottom_idx,
            'confirm_idx': self.confirm_idx,
            **self.pattern_info
        }


class WBottomDetector:
    """W底形态检测器"""

    def __init__(self, config: Dict):
        """
        初始化检测器

        参数:
            config: 配置字典
        """
        self.config = config
        self.patterns: List[WBottomPattern] = []

    def detect_single_stock(self, stock_code: str, df: pd.DataFrame) -> List[WBottomPattern]:
        """
        检测单个股票的W底形态
        使用固定跨度非重叠滑动窗口，避免同一形态重复检测

        参数:
            stock_code: 股票代码
            df: 股票数据

        返回:
            检测到的W底形态列表
        """
        patterns = []

        min_data_len = self.config.get('min_pattern_span', 5) + 10  # 最少需要的数据长度
        if len(df) < min_data_len:
            return patterns

        # 配置参数
        min_span = self.config['min_pattern_span']
        max_span = self.config['max_pattern_span']
        skip_step = self.config.get('skip_step', 20)  # 窗口滑动步长，默认20天（非重叠）
        fixed_pattern_span = self.config.get('fixed_pattern_span', None)  # 固定形态跨度，None表示使用min_span-max_span

        # 如果设置了固定跨度，使用它；否则使用min_span
        window_span = fixed_pattern_span if fixed_pattern_span else min_span

        # 从第5天开始扫描（预留前面数据）
        start_idx = 5

        # 非重叠滑动窗口：每次窗口移动skip_step天
        for window_start in range(start_idx, len(df) - window_span, skip_step):
            window_end = min(window_start + window_span, len(df) - 3)

            if window_end - window_start < min_span:
                continue

            # 在窗口内搜索四个关键点的最优组合
            best_pattern = self._find_best_pattern_in_window(stock_code, df, window_start, window_end)

            if best_pattern:
                patterns.append(best_pattern)

        return patterns

    def _find_best_pattern_in_window(self, stock_code: str, df: pd.DataFrame,
                                     window_start: int, window_end: int) -> Optional[WBottomPattern]:
        """
        在指定窗口内寻找最优的W底形态

        参数:
            stock_code: 股票代码
            df: 股票数据
            window_start: 窗口起始索引
            window_end: 窗口结束索引

        返回:
            最优的W底形态，如果没有找到则返回None
        """
        min_span = self.config['min_pattern_span']
        max_span = self.config['max_pattern_span']
        min_gap_between_points = self.config.get('min_gap_between_points', 2)  # 关键点之间最小间隔天数

        best_pattern = None
        best_score = -1

        # 四个关键点可以独立移动，但必须保持顺序：
        # left_bottom < head < right_bottom < confirm

        # 左底范围：窗口开始到窗口结束-最小形态跨度
        for left_bottom_idx in range(window_start, window_end - min_span):
            left_bottom_low = df.loc[left_bottom_idx, 'low']

            # 左底必须是局部低点
            if left_bottom_idx > window_start:
                if df.loc[left_bottom_idx - 1, 'low'] <= left_bottom_low:
                    continue

            # 头部范围：左底+最小间隔 到 窗口结束-剩余最小天数
            head_start = left_bottom_idx + min_gap_between_points
            for head_idx in range(head_start, window_end - min_gap_between_points * 2):
                head_high = df.loc[head_idx, 'high']

                # 头部应该高于前后高点（局部高点）
                head_window_start = max(left_bottom_idx, head_idx - 2)
                head_window_end = min(window_end, head_idx + 3)
                head_window = df.loc[head_window_start:head_window_end]
                if head_high < head_window['high'].max():
                    continue

                # 右底范围：头部+最小间隔 到 窗口结束-最小间隔
                right_start = head_idx + min_gap_between_points
                for right_bottom_idx in range(right_start, window_end - min_gap_between_points):
                    right_bottom_low = df.loc[right_bottom_idx, 'low']

                    # 右底必须是局部低点
                    if right_bottom_idx < window_end - 1:
                        if df.loc[right_bottom_idx + 1, 'low'] <= right_bottom_low:
                            continue

                    # 确认点范围：右底+最小间隔 到 窗口结束
                    confirm_start = right_bottom_idx + min_gap_between_points
                    for confirm_idx in range(confirm_start, min(window_end, len(df))):
                        confirm_high = df.loc[confirm_idx, 'high']

                        # 形态跨度检查
                        pattern_span = right_bottom_idx - left_bottom_idx + 1
                        if pattern_span < min_span or pattern_span > max_span:
                            continue

                        # 获取关键点价格
                        left_bottom_low = df.loc[left_bottom_idx, 'low']
                        head_high = df.loc[head_idx, 'high']
                        right_bottom_low = df.loc[right_bottom_idx, 'low']
                        confirm_high = df.loc[confirm_idx, 'high']

                        # 应用检测规则
                        if not self._check_w_bottom_rules(df, left_bottom_idx, head_idx,
                                                          right_bottom_idx, confirm_idx,
                                                          left_bottom_low, head_high,
                                                          right_bottom_low, confirm_high):
                            continue

                        # 计算形态质量分数
                        score = self._calculate_pattern_score(
                            left_bottom_low, head_high, right_bottom_low, confirm_high,
                            pattern_span, df, left_bottom_idx, head_idx, right_bottom_idx
                        )

                        # 保留分数最高的形态
                        if score > best_score:
                            best_score = score

                            # 创建形态信息
                            pattern_info = self._create_pattern_info(df, left_bottom_idx, head_idx,
                                                                     right_bottom_idx, confirm_idx,
                                                                     left_bottom_low, head_high,
                                                                     right_bottom_low, confirm_high)

                            # 创建W底形态对象
                            best_pattern = WBottomPattern(stock_code, df, left_bottom_idx, head_idx,
                                                        right_bottom_idx, confirm_idx, pattern_info)

        return best_pattern

    def _calculate_pattern_score(self, left_bottom_low: float, head_high: float,
                                right_bottom_low: float, confirm_high: float,
                                pattern_span: int, df: pd.DataFrame,
                                left_bottom_idx: int, head_idx: int,
                                right_bottom_idx: int) -> float:
        """
        计算W底形态的质量分数

        参数:
            left_bottom_low: 左底价格
            head_high: 头部价格
            right_bottom_low: 右底价格
            confirm_high: 确认点价格
            pattern_span: 形态跨度
            df: 股票数据
            left_bottom_idx: 左底索引
            head_idx: 头部索引
            right_bottom_idx: 右底索引

        返回:
            形态质量分数（越高越好）
        """
        score = 0

        # 1. 底部对称性：两个底部越接近越好
        bottom_diff_pct = abs(left_bottom_low - right_bottom_low) / left_bottom_low
        symmetry_score = (1 - bottom_diff_pct) * 30  # 最大30分
        score += symmetry_score

        # 2. 涨幅：从底部到头部的涨幅越大越好
        avg_rise_pct = ((head_high - left_bottom_low) / left_bottom_low +
                        (head_high - right_bottom_low) / right_bottom_low) / 2
        rise_score = min(avg_rise_pct / 0.2, 1) * 25  # 最大25分
        score += rise_score

        # 3. 确认突破：确认点突破头部越多越好
        breakout_pct = (confirm_high - head_high) / head_high
        breakout_score = min(breakout_pct / 0.05, 1) * 25  # 最大25分
        score += breakout_score

        # 4. 形态完整性：头部在区间内的相对位置（中间位置最优）
        head_ratio = (head_idx - left_bottom_idx) / pattern_span
        optimal_ratio = 0.5
        position_score = (1 - abs(head_ratio - optimal_ratio) / optimal_ratio) * 20  # 最大20分
        score += position_score

        return score

    def _check_w_bottom_rules(self, df: pd.DataFrame,
                             left_bottom_idx: int, head_idx: int,
                             right_bottom_idx: int, confirm_idx: int,
                             left_bottom_low: float, head_high: float,
                             right_bottom_low: float, confirm_high: float) -> bool:
        """
        检查W底形态规则

        参数:
            df: 股票数据
            left_bottom_idx: 左底索引
            head_idx: 头部索引
            right_bottom_idx: 右底索引
            confirm_idx: 确认点索引
            left_bottom_low: 左底价格
            head_high: 头部价格
            right_bottom_low: 右底价格
            confirm_high: 确认点价格

        返回:
            是否符合W底形态规则
        """
        # 规则1：头部必须高于两个底部（至少5%）
        if head_high <= left_bottom_low * 1.05 or head_high <= right_bottom_low * 1.05:
            return False

        # 规则2：两个底部价格相近
        bottom_diff_pct = abs(left_bottom_low - right_bottom_low) / left_bottom_low * 100
        if bottom_diff_pct > self.config['max_bottom_diff_pct']:
            return False

        # 规则3：低点到中间高点的涨幅足够
        left_rise_pct = (head_high - left_bottom_low) / left_bottom_low * 100
        right_rise_pct = (head_high - right_bottom_low) / right_bottom_low * 100
        if left_rise_pct < self.config['min_rise_pct'] or right_rise_pct < self.config['min_rise_pct']:
            return False

        # 规则4：确认K线突破头部
        if confirm_high <= head_high:
            return False

        # 规则5：两个底部必须是局部低点（已在窗口搜索中检查，这里额外确认）
        min_check_window = 2  # 检查前后2天
        # 检查左底前min_check_window天
        for i in range(max(0, left_bottom_idx - min_check_window), left_bottom_idx):
            if df.loc[i, 'low'] <= left_bottom_low:
                return False
        # 检查左底后min_check_window天（到头部之前）
        for i in range(left_bottom_idx + 1, min(head_idx, left_bottom_idx + min_check_window + 1)):
            if df.loc[i, 'low'] <= left_bottom_low:
                return False

        # 检查右底前min_check_window天（从头部之后）
        for i in range(max(head_idx + 1, right_bottom_idx - min_check_window), right_bottom_idx):
            if df.loc[i, 'low'] <= right_bottom_low:
                return False
        # 检查右底后min_check_window天
        for i in range(right_bottom_idx + 1, min(len(df), right_bottom_idx + min_check_window + 1)):
            if df.loc[i, 'low'] <= right_bottom_low:
                return False

        # 规则6：形态跨度合理（从左底到右底）
        pattern_span = right_bottom_idx - left_bottom_idx + 1
        if pattern_span < self.config['min_pattern_span'] or pattern_span > self.config['max_pattern_span']:
            return False

        # 规则7：头部应该是左底和右底之间的最高点
        if head_idx > left_bottom_idx and head_idx < right_bottom_idx:
            head_window = df.loc[left_bottom_idx + 1:right_bottom_idx - 1]
            if len(head_window) > 0 and head_high < head_window['high'].max():
                return False

        # 规则8：头部应该是局部高点
        head_check_window = min(3, head_idx - left_bottom_idx, right_bottom_idx - head_idx)
        for i in range(max(left_bottom_idx, head_idx - head_check_window), head_idx):
            if df.loc[i, 'high'] >= head_high:
                return False
        for i in range(head_idx + 1, min(right_bottom_idx, head_idx + head_check_window + 1)):
            if df.loc[i, 'high'] >= head_high:
                return False

        return True

    def _create_pattern_info(self, df: pd.DataFrame,
                            left_bottom_idx: int, head_idx: int,
                            right_bottom_idx: int, confirm_idx: int,
                            left_bottom_low: float, head_high: float,
                            right_bottom_low: float, confirm_high: float) -> Dict:
        """
        创建形态信息字典

        参数:
            df: 股票数据
            各关键点的索引和价格

        返回:
            形态信息字典
        """
        left_bottom_date = df.loc[left_bottom_idx, 'trade_date'].strftime('%Y-%m-%d')
        head_date = df.loc[head_idx, 'trade_date'].strftime('%Y-%m-%d')
        right_bottom_date = df.loc[right_bottom_idx, 'trade_date'].strftime('%Y-%m-%d')
        confirm_date = df.loc[confirm_idx, 'trade_date'].strftime('%Y-%m-%d')

        pattern_span = right_bottom_idx - left_bottom_idx + 1
        bottom_diff_pct = abs(left_bottom_low - right_bottom_low) / left_bottom_low * 100
        left_rise_pct = (head_high - left_bottom_low) / left_bottom_low * 100
        right_rise_pct = (head_high - right_bottom_low) / right_bottom_low * 100

        return {
            'left_bottom_price': left_bottom_low,
            'head_price': head_high,
            'right_bottom_price': right_bottom_low,
            'confirm_price': confirm_high,
            'left_bottom_date': left_bottom_date,
            'head_date': head_date,
            'right_bottom_date': right_bottom_date,
            'confirm_date': confirm_date,
            'pattern_span': pattern_span,
            'bottom_diff_pct': bottom_diff_pct,
            'left_rise_pct': left_rise_pct,
            'right_rise_pct': right_rise_pct
        }

    def detect_all_stocks(self, data_dict: Dict[str, pd.DataFrame]) -> List[WBottomPattern]:
        """
        检测所有股票的W底形态

        参数:
            data_dict: {股票代码: DataFrame} 字典

        返回:
            检测到的所有W底形态
        """
        self.patterns = []

        print(f"开始检测 {len(data_dict)} 只股票的W底形态...")

        for i, (stock_code, df) in enumerate(data_dict.items(), 1):
            print(f"处理股票 {i}/{len(data_dict)}: {stock_code}")

            try:
                stock_patterns = self.detect_single_stock(stock_code, df)
                self.patterns.extend(stock_patterns)

                if stock_patterns:
                    print(f"  发现 {len(stock_patterns)} 个W底形态")

            except Exception as e:
                print(f"  处理股票 {stock_code} 时出错: {e}")
                continue

        print(f"\n检测完成，共发现 {len(self.patterns)} 个W底形态")
        return self.patterns

    def extract_samples(self, num_samples: int, random_seed: int = 42) -> List[WBottomPattern]:
        """
        提取指定数量的W底形态样本

        参数:
            num_samples: 要提取的样本数量
            random_seed: 随机种子

        返回:
            提取的样本列表
        """
        if len(self.patterns) <= num_samples:
            return self.patterns

        # 随机选择
        np.random.seed(random_seed)
        selected_indices = np.random.choice(len(self.patterns), num_samples, replace=False)
        return [self.patterns[i] for i in selected_indices]

    def save_patterns(self, filepath: str):
        """
        保存检测到的形态

        参数:
            filepath: 保存路径
        """
        patterns_data = [pattern.to_dict() for pattern in self.patterns]

        with open(filepath, 'wb') as f:
            pickle.dump(patterns_data, f)

        print(f"W底形态已保存到: {filepath}")

    def load_patterns(self, filepath: str):
        """
        加载保存的形态

        参数:
            filepath: 文件路径
        """
        with open(filepath, 'rb') as f:
            patterns_data = pickle.load(f)

        self.patterns = []
        for pattern_data in patterns_data:
            # 需要重建df对象，这里暂时简化处理
            # 实际使用时需要从原始数据加载
            pass

        print(f"已加载 {len(patterns_data)} 个W底形态")


def create_w_bottom_detector(config: Dict) -> WBottomDetector:
    """
    创建W底检测器的便捷函数

    参数:
        config: 配置字典

    返回:
        WBottomDetector实例
    """
    return WBottomDetector(config)
