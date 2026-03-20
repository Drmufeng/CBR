"""实验版 CBR 估算算法。

该模块与现有 cbr_core 基线算法并行存在，
用于在不影响现有流程稳定性的前提下做增强试验。
"""

import numpy as np


class ExperimentalEstimator:
    """混合相似度实验算法（数值 + 类别）。"""

    @staticmethod
    def estimate(engine, input_data):
        """输出与基线一致的估算结果结构。"""
        exact_values = engine.processor.find_exact_matches(input_data)
        if exact_values is not None and len(exact_values) > 0:
            return (
                float(np.max(exact_values)),
                [{'车型': '完全匹配车辆', 'LCC（10年）': val, 'similarity': 1.0} for val in exact_values],
                '精确匹配',
                0.0,
            )

        similarities = ExperimentalEstimator._hybrid_similarity(engine, input_data)
        top_indices = ExperimentalEstimator._select_top_indices(similarities, top_k=5)
        top_models = ExperimentalEstimator._build_top_models(engine, top_indices, similarities)
        weights = np.maximum(similarities[top_indices], 1e-6)
        estimated_lcc = float(np.average([model['LCC（10年）'] for model in top_models], weights=weights))
        relative_error = ExperimentalEstimator._calculate_relative_error(top_models, estimated_lcc, weights)
        confidence = ExperimentalEstimator._evaluate_confidence(float(np.max(similarities[top_indices])))
        return estimated_lcc, top_models, confidence, relative_error

    @staticmethod
    def _hybrid_similarity(engine, input_data):
        """构建混合相似度：数值相似度 + 类别匹配度。"""
        input_normalized = engine.processor.normalize_input(input_data)
        data_normalized = engine.processor.data_normalized.values
        raw_data = engine.processor.data
        features = engine.processor.features
        weights = engine.weights

        battery_index = features.index('电池类型') if '电池类型' in features else -1
        numeric_indices = [idx for idx in range(len(features)) if idx != battery_index]

        numeric_weights = weights[numeric_indices]
        numeric_weights = numeric_weights / np.sum(numeric_weights)

        abs_diff = np.abs(data_normalized[:, numeric_indices] - input_normalized[numeric_indices])
        numeric_distance = np.sum(abs_diff * numeric_weights, axis=1)
        numeric_similarity = np.clip(1 - numeric_distance, 0.0, 1.0)

        if battery_index >= 0:
            battery_matches = (
                raw_data[features[battery_index]].astype(float).values == float(input_data[battery_index])
            ).astype(float)
        else:
            battery_matches = np.zeros(len(raw_data), dtype=float)

        return np.clip(0.85 * numeric_similarity + 0.15 * battery_matches, 0.0, 1.0)

    @staticmethod
    def _select_top_indices(similarities, top_k=5):
        """选择 Top-K 相似案例。"""
        k = min(top_k, len(similarities))
        return np.argsort(-similarities)[:k]

    @staticmethod
    def _build_top_models(engine, top_indices, similarities):
        """构建界面展示所需的相似车型列表。"""
        return [
            {
                '车型': engine.processor.data.iloc[i]['车型'],
                'LCC（10年）': engine.processor.data.iloc[i][engine.processor.target],
                'similarity': float(similarities[i]),
            }
            for i in top_indices
        ]

    @staticmethod
    def _calculate_relative_error(top_models, estimated_lcc, weights):
        """根据候选案例估算相对误差指标。"""
        lcc_values = [model['LCC（10年）'] for model in top_models]
        weighted_errors = [
            abs((lcc - estimated_lcc) / estimated_lcc) * weight
            for lcc, weight in zip(lcc_values, weights)
        ]
        return float((sum(weighted_errors) / sum(weights)) * 100)

    @staticmethod
    def _evaluate_confidence(best_similarity):
        """根据最优相似度给出置信度。"""
        if best_similarity > 0.92:
            return '极高'
        if best_similarity > 0.82:
            return '高'
        if best_similarity > 0.70:
            return '中'
        return '低'
