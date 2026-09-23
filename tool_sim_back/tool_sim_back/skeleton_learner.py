"""
骨架学习模块
负责从多个W底形态中学习骨架特征
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import pickle
import warnings
from collections import defaultdict
warnings.filterwarnings('ignore')


class SkeletonPoint:
    """骨架点类"""

    def __init__(self, idx: int, price: float, date: pd.Timestamp,
                 point_type: str, importance_score: float = 0.0,
                 is_fixed: bool = False, additional_info: Dict = None):
        self.idx = idx  # 绝对索引
        self.price = price  # 价格
        self.date = date  # 日期
        self.point_type = point_type  # 点类型: 'local_max', 'local_min', 'intermediate', 'turning_point'
        self.importance_score = importance_score  # 重要性分数
        self.is_fixed = is_fixed  # 是否为固定点
        self.additional_info = additional_info or {}  # 额外信息

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'idx': self.idx,
            'price': self.price,
            'date': self.date.strftime('%Y-%m-%d'),
            'point_type': self.point_type,
            'importance_score': self.importance_score,
            'is_fixed': self.is_fixed,
            'additional_info': self.additional_info
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SkeletonPoint':
        """从字典创建"""
        return cls(
            idx=data['idx'],
            price=data['price'],
            date=pd.Timestamp(data['date']),
            point_type=data['point_type'],
            importance_score=data.get('importance_score', 0.0),
            is_fixed=data.get('is_fixed', False),
            additional_info=data.get('additional_info', {})
        )


class SegmentSkeleton:
    """片段骨架"""

    def __init__(self, segment_id: str, points: List[SkeletonPoint],
                 segment_info: Dict = None):
        self.segment_id = segment_id
        self.points = points  # 骨架点列表（按时间排序）
        self.segment_info = segment_info or {}  # 片段信息

    def get_fixed_points(self) -> List[SkeletonPoint]:
        """获取固定点"""
        return [p for p in self.points if p.is_fixed]

    def get_non_fixed_points(self) -> List[SkeletonPoint]:
        """获取非固定点"""
        return [p for p in self.points if not p.is_fixed]

    def get_price_range(self) -> Tuple[float, float]:
        """获取价格范围"""
        prices = [p.price for p in self.points]
        return min(prices), max(prices)


class SkeletonLearner:
    """骨架学习器"""

    def __init__(self, config: Dict):
        """
        初始化学习器

        参数:
            config: 配置字典
        """
        self.config = config
        self.learned_features = {
            'relative_position_distribution': defaultdict(list),  # 相对位置分布
            'price_change_importance': [],  # 价格变化重要性
            'point_type_importance': defaultdict(float),  # 点类型重要性
            'total_segments': 0,  # 学习的总片段数
            'converged': False  # 是否收敛
        }

    def extract_skeleton_from_segment(self, df: pd.DataFrame,
                                     start_idx: int,
                                     end_idx: int,
                                     segment_id: str = "unknown") -> SegmentSkeleton:
        """
        从单个片段中提取骨架

        参数:
            df: K线数据
            start_idx: 起始索引
            end_idx: 结束索引
            segment_id: 片段ID

        返回:
            SegmentSkeleton: 片段骨架
        """
        # 验证索引
        start_idx = max(0, int(start_idx))
        end_idx = min(len(df) - 1, int(end_idx))

        if start_idx >= end_idx:
            return SegmentSkeleton(segment_id, [], {})

        # 1. 提取真正的最高价和最低价
        true_max_idx = df.loc[start_idx:end_idx+1, 'high'].idxmax()
        true_min_idx = df.loc[start_idx:end_idx+1, 'low'].idxmin()

        true_max_price = df.loc[true_max_idx, 'high']
        true_min_price = df.loc[true_min_idx, 'low']

        # 2. 创建固定四个核心关键点
        fixed_points = self._create_fixed_four_points(df, start_idx, end_idx,
                                                     true_max_idx, true_min_idx,
                                                     true_max_price, true_min_price)

        # 3. 提取候选点
        candidate_points = self._extract_candidate_points(df, start_idx, end_idx)

        # 4. 计算重要性分数
        self._calculate_importance_scores(candidate_points, df, start_idx, end_idx)

        # 5. 选择额外关键点
        additional_points = self._select_additional_points(candidate_points, fixed_points)

        # 6. 合并并排序
        all_points = fixed_points + additional_points
        all_points = sorted(all_points, key=lambda p: p.idx)

        # 7. 创建骨架对象
        segment_info = {
            'start_idx': start_idx,
            'end_idx': end_idx,
            'total_days': end_idx - start_idx + 1,
            'num_fixed_points': len(fixed_points),
            'num_skeleton_points': len(all_points),
            'true_max_price': true_max_price,
            'true_min_price': true_min_price
        }

        return SegmentSkeleton(segment_id, all_points, segment_info)

    def _create_fixed_four_points(self, df: pd.DataFrame,
                                 start_idx: int, end_idx: int,
                                 true_max_idx: int, true_min_idx: int,
                                 true_max_price: float, true_min_price: float) -> List[SkeletonPoint]:
        """
        创建固定四个核心关键点

        参数:
            df: K线数据
            start_idx, end_idx: 索引范围
            true_max_idx, true_min_idx: 真正的最高点和最低点索引
            true_max_price, true_min_price: 真正的最高点和最低点价格

        返回:
            固定四个核心关键点列表
        """
        fixed_points = []

        # 1. 最高价点（固定）
        max_point = SkeletonPoint(
            idx=int(true_max_idx),
            price=true_max_price,
            date=df.loc[true_max_idx, 'trade_date'],
            point_type='local_max',
            importance_score=10.0,
            is_fixed=True,
            additional_info={'is_true_max': True}
        )
        fixed_points.append(max_point)

        # 2. 最低价点（固定）
        min_point = SkeletonPoint(
            idx=int(true_min_idx),
            price=true_min_price,
            date=df.loc[true_min_idx, 'trade_date'],
            point_type='local_min',
            importance_score=10.0,
            is_fixed=True,
            additional_info={'is_true_min': True}
        )
        fixed_points.append(min_point)

        # 3. 最高价前的转折点（向外扩充）
        before_max_points = []
        for i in range(max(start_idx, true_max_idx - 15), true_max_idx):
            if i >= len(df):
                continue

            # 检查是否为转折点（局部极值）
            if i > start_idx and i < true_max_idx - 1:
                current_price = df.loc[i, 'close']
                prev_price = df.loc[i-1, 'close']
                next_price = df.loc[i+1, 'close'] if i+1 < len(df) else current_price

                is_local_extremum = (current_price >= prev_price and current_price >= next_price) or \
                                   (current_price <= prev_price and current_price <= next_price)

                if is_local_extremum:
                    # 计算价格变化幅度
                    price_change = abs(current_price - df.loc[true_max_idx-1, 'close'])

                    before_max_points.append({
                        'idx': i,
                        'price': current_price,
                        'date': df.loc[i, 'trade_date'],
                        'point_type': 'local_max' if current_price >= prev_price else 'local_min',
                        'importance_score': price_change
                    })

        # 选择价格变化最大的转折点
        if before_max_points:
            best_before = max(before_max_points, key=lambda p: p['importance_score'])
            before_max_point = SkeletonPoint(
                idx=best_before['idx'],
                price=best_before['price'],
                date=best_before['date'],
                point_type='turning_point',
                importance_score=8.0,
                is_fixed=True,
                additional_info={'is_turning_point_before_max': True}
            )
            fixed_points.append(before_max_point)
        else:
            # 如果没有找到转折点，创建一个中间点
            mid_idx = max(start_idx, true_max_idx - 5)
            before_max_point = SkeletonPoint(
                idx=mid_idx,
                price=df.loc[mid_idx, 'close'],
                date=df.loc[mid_idx, 'trade_date'],
                point_type='turning_point',
                importance_score=8.0,
                is_fixed=True,
                additional_info={'is_turning_point_before_max': True}
            )
            fixed_points.append(before_max_point)

        # 4. 最低价后的转折点（向外扩充）
        after_min_points = []
        for i in range(true_min_idx + 1, min(end_idx, true_min_idx + 15)):
            if i >= len(df):
                continue

            # 检查是否为转折点（局部极值）
            if i > true_min_idx + 1 and i < end_idx:
                current_price = df.loc[i, 'close']
                prev_price = df.loc[i-1, 'close']
                next_price = df.loc[i+1, 'close'] if i+1 < len(df) else current_price

                is_local_extremum = (current_price >= prev_price and current_price >= next_price) or \
                                   (current_price <= prev_price and current_price <= next_price)

                if is_local_extremum:
                    # 计算价格变化幅度
                    price_change = abs(current_price - df.loc[true_min_idx+1, 'close'])

                    after_min_points.append({
                        'idx': i,
                        'price': current_price,
                        'date': df.loc[i, 'trade_date'],
                        'point_type': 'local_max' if current_price >= prev_price else 'local_min',
                        'importance_score': price_change
                    })

        # 选择价格变化最大的转折点
        if after_min_points:
            best_after = max(after_min_points, key=lambda p: p['importance_score'])
            after_min_point = SkeletonPoint(
                idx=best_after['idx'],
                price=best_after['price'],
                date=best_after['date'],
                point_type='turning_point',
                importance_score=8.0,
                is_fixed=True,
                additional_info={'is_turning_point_after_min': True}
            )
            fixed_points.append(after_min_point)
        else:
            # 如果没有找到转折点，创建一个中间点
            mid_idx = min(end_idx, true_min_idx + 5)
            after_min_point = SkeletonPoint(
                idx=mid_idx,
                price=df.loc[mid_idx, 'close'],
                date=df.loc[mid_idx, 'trade_date'],
                point_type='turning_point',
                importance_score=8.0,
                is_fixed=True,
                additional_info={'is_turning_point_after_min': True}
            )
            fixed_points.append(after_min_point)

        # 按索引排序
        fixed_points = sorted(fixed_points, key=lambda p: p.idx)

        return fixed_points

    def _extract_candidate_points(self, df: pd.DataFrame,
                                 start_idx: int,
                                 end_idx: int) -> List[Dict]:
        """提取候选点"""
        candidate_points = []

        for i in range(start_idx + 1, end_idx):
            if i >= len(df) - 1:
                break

            current_price = df.loc[i, 'close']
            prev_price = df.loc[i-1, 'close']
            next_price = df.loc[i+1, 'close'] if i+1 < len(df) else current_price

            # 检测局部极值
            is_local_max = current_price >= prev_price and current_price >= next_price
            is_local_min = current_price <= prev_price and current_price <= next_price

            point_type = 'intermediate'
            if is_local_max:
                point_type = 'local_max'
            elif is_local_min:
                point_type = 'local_min'

            # 确定价格
            if is_local_max:
                price_to_use = df.loc[i, 'high']
            elif is_local_min:
                price_to_use = df.loc[i, 'low']
            else:
                price_to_use = current_price

            candidate_points.append({
                'idx': i,
                'price': price_to_use,
                'date': df.loc[i, 'trade_date'],
                'point_type': point_type,
                'importance_score': 0
            })

        return candidate_points

    def _calculate_importance_scores(self, candidate_points: List[Dict],
                                    df: pd.DataFrame,
                                    start_idx: int,
                                    end_idx: int):
        """计算重要性分数"""
        for i, point in enumerate(candidate_points):
            score = 0

            # 因素1：点类型权重
            type_weights = {
                'local_max': 2.5,
                'local_min': 2.5,
                'intermediate': 1.0
            }
            score += type_weights.get(point['point_type'], 1.0)

            # 因素2：价格变化幅度
            if i > 0:
                price_change = abs(point['price'] - candidate_points[i-1]['price'])
                relative_change = price_change / max(candidate_points[i-1]['price'], 1) * 100
                score += relative_change * 0.5

            # 因素3：时间间隔
            if i > 0:
                time_gap = (point['date'] - candidate_points[i-1]['date']).days
                if self.config['min_time_gap'] <= time_gap <= 10:
                    score += 1.0

            point['importance_score'] = score

    def _select_additional_points(self, candidate_points: List[Dict],
                                 fixed_points: List[SkeletonPoint]) -> List[SkeletonPoint]:
        """
        选择额外关键点（基于重要性阈值和数量限制）

        逻辑：
        1. 筛选超过重要性阈值的候选点
        2. 确保总点数在 min_points 到 max_points 之间
        3. 按重要性分数排序选择
        """
        # 过滤掉固定点
        fixed_indices = {p.idx for p in fixed_points}
        remaining_points = [p for p in candidate_points if p['idx'] not in fixed_indices]

        if not remaining_points:
            return []

        # 按重要性分数排序（从高到低）
        remaining_points.sort(key=lambda p: p['importance_score'], reverse=True)

        # 获取配置参数
        importance_threshold = self.config.get('importance_threshold', 1.5)
        min_points = self.config.get('min_points', 4)
        max_points = self.config.get('max_points', 8)

        # 第一步：筛选超过阈值的点
        high_importance_points = [
            p for p in remaining_points
            if p['importance_score'] >= importance_threshold
        ]

        # 第二步：计算还可以选择多少个点
        num_fixed = len(fixed_points)
        max_additional = max_points - num_fixed  # 最大额外点数
        min_additional = max(0, min_points - num_fixed)  # 最小额外点数

        # 第三步：确定最终选择的点数
        if len(high_importance_points) >= min_additional:
            # 如果有足够的超过阈值的点，使用它们
            if len(high_importance_points) > max_additional:
                # 如果超过最大限制，只选前 max_additional 个
                selected_points = high_importance_points[:max_additional]
            else:
                # 否则全部使用
                selected_points = high_importance_points
        else:
            # 如果超过阈值的点不够，补充选择次优的点，直到达到最小点数
            additional_needed = min_additional - len(high_importance_points)
            remaining_below_threshold = [
                p for p in remaining_points
                if p['importance_score'] < importance_threshold
            ]
            selected_points = high_importance_points + remaining_below_threshold[:additional_needed]

        # 转换为SkeletonPoint对象
        skeleton_points = []
        for point in selected_points:
            skeleton_points.append(SkeletonPoint(
                idx=point['idx'],
                price=point['price'],
                date=point['date'],
                point_type=point['point_type'],
                importance_score=point['importance_score'],
                is_fixed=False
            ))

        return skeleton_points

    def learn_from_patterns(self, patterns: List['WBottomPattern'], batch_size: int = 500):
        """
        从多个W底形态中学习（分批处理避免OOM）

        参数:
            patterns: W底形态列表
            batch_size: 每批处理的数量（默认500）
        """
        self.learned_features['total_segments'] = len(patterns)

        print(f"开始从 {len(patterns)} 个W底形态中学习骨架特征...")
        print(f"使用分批处理，每批 {batch_size} 个模式（避免内存溢出）")

        total_batches = (len(patterns) + batch_size - 1) // batch_size
        all_skeletons = []

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(patterns))
            batch_patterns = patterns[start_idx:end_idx]

            print(f"\n处理批次 {batch_idx + 1}/{total_batches} (模式 {start_idx + 1}-{end_idx})")

            batch_skeletons = []
            for i, pattern in enumerate(batch_patterns, start_idx + 1):
                if i % 50 == 0:
                    print(f"  处理进度: {i}/{len(patterns)}")

                # 提取骨架
                df = pattern.df
                start_idx_segment = pattern.left_bottom_idx
                end_idx_segment = pattern.confirm_idx
                segment_id = f"{pattern.stock_code}_{i}"

                skeleton = self.extract_skeleton_from_segment(df, start_idx_segment, end_idx_segment, segment_id)
                batch_skeletons.append(skeleton)

            # 对当前批次进行统计学习
            self._learn_statistical_features(batch_skeletons, accumulate=True)

            # 释放当前批次内存
            all_skeletons.extend(batch_skeletons)
            del batch_skeletons

            # 强制垃圾回收（Python会自动回收，但显式调用有助于及时释放内存）
            import gc
            gc.collect()

            print(f"  批次 {batch_idx + 1} 完成")

        # 学习统计特征
        # 注意：_learn_statistical_features 已经在批次中累积计算，这里只需要检查收敛
        # 重新计算最终的统计特征（确保一致性）
        self._learn_statistical_features(all_skeletons)

        # 检查是否收敛
        if len(patterns) >= self.config.get('min_learning_samples', 10):
            self.learned_features['converged'] = True

        print(f"\n学习完成！共学习 {len(patterns)} 个片段")
        print(f"模型收敛: {self.learned_features['converged']}")

    def _learn_statistical_features(self, skeletons: List[SegmentSkeleton], accumulate: bool = False):
        """
        学习统计特征

        参数:
            skeletons: 片段骨架列表
            accumulate: 是否累积到已有特征（用于分批处理）
        """
        # 如果不是累积模式，清空已有数据
        if not accumulate:
            self.learned_features['relative_position_distribution'] = defaultdict(list)
            self.learned_features['price_change_importance'] = []
            self.learned_features['point_type_importance'] = defaultdict(float)

        # 1. 学习相对位置分布
        position_bins = 10

        for skeleton in skeletons:
            fixed_points = skeleton.get_fixed_points()

            if len(fixed_points) < 2:
                continue

            start_idx = min(p.idx for p in skeleton.points)
            end_idx = max(p.idx for p in skeleton.points)
            total_span = end_idx - start_idx

            if total_span == 0:
                continue

            for point in fixed_points:
                rel_pos = (point.idx - start_idx) / total_span
                bin_idx = min(int(rel_pos * position_bins), position_bins - 1)
                position_key = f"bin_{bin_idx}"
                self.learned_features['relative_position_distribution'][position_key].append(rel_pos)

        # 2. 学习点类型重要性（如果是累积模式，需要重新计算）
        if not accumulate:
            type_counts = defaultdict(int)
            total_fixed = 0

            for skeleton in skeletons:
                fixed_points = skeleton.get_fixed_points()
                for point in fixed_points:
                    type_counts[point.point_type] += 1
                    total_fixed += 1

            if total_fixed > 0:
                for point_type, count in type_counts.items():
                    self.learned_features['point_type_importance'][point_type] = (count / total_fixed) * 3.0
        else:
            # 累积模式：重新计算所有点类型的统计
            # 这里需要访问所有已处理的骨架，为简化，我们只在最后统一计算
            pass

        # 3. 学习价格变化重要性
        batch_importances = []

        for skeleton in skeletons:
            points = skeleton.points
            for i in range(1, len(points)):
                price_change = abs(points[i].price - points[i-1].price)
                importance = price_change / max(points[i].price, 1) * 100
                batch_importances.append(importance)

        # 如果是累积模式，添加到现有列表
        if accumulate:
            self.learned_features['price_change_importance'].extend(batch_importances)
        else:
            self.learned_features['price_change_importance'] = batch_importances

    def save_model(self, filepath: str):
        """
        保存学习到的模型

        参数:
            filepath: 保存路径
        """
        model_data = {
            'config': self.config,
            'learned_features': self.learned_features
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"骨架学习模型已保存到: {filepath}")

    def load_model(self, filepath: str):
        """
        加载学习到的模型

        参数:
            filepath: 模型路径
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.config = model_data['config']
        self.learned_features = model_data['learned_features']

        print(f"骨架学习模型已加载: {filepath}")
        print(f"学习片段数: {self.learned_features['total_segments']}")
        print(f"模型收敛: {self.learned_features['converged']}")


# 导入WBottomPattern类型提示
from pattern_detector import WBottomPattern

def create_skeleton_learner(config: Dict) -> SkeletonLearner:
    """
    创建骨架学习器的便捷函数

    参数:
        config: 配置字典

    返回:
        SkeletonLearner实例
    """
    return SkeletonLearner(config)
