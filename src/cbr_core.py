"""CBR 相似度计算与估算核心逻辑。"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from cbr_experimental import ExperimentalEstimator


class SimilarityEngine:
    """根据处理后的案例库计算相似度或距离。"""

    def __init__(self, processor):
        self.processor = processor
        self.weights = np.array([1.2, 1.0, 0.9, 1.4, 1.3, 1.1, 1.5, 0.7, 1.0])

    def calculate_distance(self, input_data, algorithm):
        """根据算法返回与所有案例的距离值。"""
        input_normalized = self.processor.normalize_input(input_data).reshape(1, -1)

        if algorithm == 'manhattan':
            return np.sum(
                self.weights * np.abs(self.processor.data_normalized - input_normalized),
                axis=1,
            )

        similarities = cosine_similarity(
            self.processor.data_normalized * self.weights,
            input_normalized * self.weights,
        ).flatten()
        return 1 - similarities


class LCCEstimatorCore:
    """基于相似案例输出估算值、相似车型与置信信息。"""

    @staticmethod
    def estimate(engine, input_data, algorithm):
        """执行一次 CBR 估算。"""
        if algorithm == 'experimental_hybrid':
            return ExperimentalEstimator.estimate(engine, input_data)

        exact_values = engine.processor.find_exact_matches(input_data)
        if exact_values is not None and len(exact_values) > 0:
            return (
                float(np.max(exact_values)),
                [{'车型': '完全匹配车辆', 'LCC（10年）': val, 'similarity': 1.0} for val in exact_values],
                '精确匹配',
                0.0,
            )

        distances = engine.calculate_distance(input_data, algorithm)
        top_indices, similarity_scores = LCCEstimatorCore._select_top_cases(distances, algorithm)
        top_models = LCCEstimatorCore._build_top_models(engine, top_indices, similarity_scores)
        weights = LCCEstimatorCore._calculate_weights(distances, top_indices, similarity_scores, algorithm)
        estimated_lcc = float(np.average([model['LCC（10年）'] for model in top_models], weights=weights))
        relative_error = LCCEstimatorCore._calculate_relative_error(top_models, estimated_lcc, weights)
        confidence = LCCEstimatorCore._evaluate_confidence(distances, top_indices, similarity_scores, algorithm)
        return estimated_lcc, top_models, confidence, relative_error

    @staticmethod
    def _select_top_cases(distances, algorithm):
        """选择候选相似案例，并生成对应相似度。"""
        if algorithm == 'manhattan':
            top_indices = np.argsort(distances)[:3]
            similarity_scores = 1 / (1 + distances)
        else:
            top_indices = np.argsort(distances)[:2]
            similarity_scores = 1 - distances
        return top_indices, similarity_scores

    @staticmethod
    def _build_top_models(engine, top_indices, similarity_scores):
        """构建界面展示所需的相似车型列表。"""
        return [
            {
                '车型': engine.processor.data.iloc[i]['车型'],
                'LCC（10年）': engine.processor.data.iloc[i][engine.processor.target],
                'similarity': float(similarity_scores[i]),
            }
            for i in top_indices
        ]

    @staticmethod
    def _calculate_weights(distances, top_indices, similarity_scores, algorithm):
        """计算加权平均时使用的权重。"""
        if algorithm == 'manhattan':
            return np.exp(-distances[top_indices])
        return similarity_scores[top_indices]

    @staticmethod
    @staticmethod
    def _calculate_relative_error(top_models, estimated_lcc, weights):
        """根据候选案例估算一个相对误差指标。"""
        lcc_values = [model['LCC（10年）'] for model in top_models]
        weighted_errors = [
            abs((lcc - estimated_lcc) / estimated_lcc) * weight
            for lcc, weight in zip(lcc_values, weights)
        ]
        return float((sum(weighted_errors) / sum(weights)) * 100)

    @staticmethod
    def _evaluate_confidence(distances, top_indices, similarity_scores, algorithm):
        """根据最优匹配质量给出简单置信度。"""
        if algorithm == 'manhattan':
            min_distance = distances[top_indices[0]]
            if min_distance < 0.2:
                return '极高'
            if min_distance < 0.4:
                return '高'
            if min_distance < 0.6:
                return '中'
            return '低'

        max_similarity = similarity_scores[top_indices[0]]
        if max_similarity > 0.9:
            return '极高'
        if max_similarity > 0.7:
            return '高'
        if max_similarity > 0.5:
            return '中'
        return '低'
