"""模型验证与结果导出。"""

import math
from pathlib import Path

import pandas as pd

from cbr_core import LCCEstimatorCore, SimilarityEngine


class ValidationService:
    """负责留一验证、结果过滤与导出。"""

    def __init__(self, processor, algorithm, valid_error_threshold):
        self.processor = processor
        self.algorithm = algorithm
        self.valid_error_threshold = valid_error_threshold

    def validate_all(self, progress_callback=None):
        """遍历所有样本并返回完整验证结果与阈值内结果。"""
        total = len(self.processor.data)
        raw_results = []

        for idx in range(total):
            if progress_callback is not None:
                progress_callback(idx, total)
            result = self.validate_single_sample(idx)
            if result:
                raw_results.append(result)

        valid_results = [res for res in raw_results if res is not None and res[3] <= self.valid_error_threshold]
        return {
            'all_results': raw_results,
            'valid_results': valid_results,
            'total_count': total,
        }

    def validate_single_sample(self, index):
        """对单个样本执行留一法验证。"""
        try:
            temp_processor = self.processor.create_subset_without_index(index)
            temp_engine = SimilarityEngine(temp_processor)
            current_row = self.processor.data.iloc[index]

            input_data = current_row[self.processor.features].values.astype(float)
            actual_lcc = current_row[self.processor.target]
            estimated_lcc, _, _, _ = LCCEstimatorCore.estimate(temp_engine, input_data, self.algorithm)

            if actual_lcc == 0:
                return None

            error = abs(estimated_lcc - actual_lcc) / actual_lcc * 100
            return (current_row['车型'], actual_lcc, estimated_lcc, error)
        except Exception:
            return None


def build_validation_summary(validation_results, total_count):
    """根据验证结果生成汇总信息。"""
    df = pd.DataFrame(validation_results, columns=['车型', '实际LCC', '估计LCC', '相对误差'])
    if df.empty:
        return pd.DataFrame(
            {
                '总样本数': [total_count],
                '可评估样本数': [0],
                '最大误差': [0.0],
                '最小误差': [0.0],
                '平均误差': [0.0],
                'MAPE': [0.0],
                'RMSE': [0.0],
            }
        )

    mape = df['相对误差'].mean()
    rmse = math.sqrt(((df['估计LCC'] - df['实际LCC']) ** 2).mean())
    return pd.DataFrame(
        {
            '总样本数': [total_count],
            '可评估样本数': [len(df)],
            '最大误差': [df['相对误差'].max()],
            '最小误差': [df['相对误差'].min()],
            '平均误差': [df['相对误差'].mean()],
            'MAPE': [mape],
            'RMSE': [rmse],
        }
    )


def build_validation_metrics(validation_results, total_count):
    """返回便于数据库保存的验证统计指标。"""
    summary = build_validation_summary(validation_results, total_count).iloc[0]
    return {
        'sample_count': int(summary['可评估样本数']),
        'evaluated_count': int(summary['可评估样本数']),
        'avg_error': float(summary['平均误差']),
        'mape': float(summary['MAPE']),
        'rmse': float(summary['RMSE']),
        'max_error': float(summary['最大误差']),
        'min_error': float(summary['最小误差']),
    }


def build_error_distribution(validation_results, bins=None):
    """按误差区间统计分布。"""
    bins = bins or [0, 10, 20, 30, 50, float('inf')]
    labels = ['0-10%', '10-20%', '20-30%', '30-50%', '>=50%']

    df = pd.DataFrame(validation_results, columns=['车型', '实际LCC', '估计LCC', '相对误差'])
    if df.empty:
        return pd.DataFrame({'误差区间': labels, '样本数': [0] * len(labels), '占比(%)': [0.0] * len(labels)})

    categories = pd.cut(df['相对误差'], bins=bins, labels=labels, include_lowest=True, right=False)
    counts = categories.value_counts(sort=False).fillna(0).astype(int)
    total = int(len(df))
    rates = (counts / total * 100).round(2)
    return pd.DataFrame({'误差区间': labels, '样本数': counts.tolist(), '占比(%)': rates.tolist()})


def export_validation_results(file_path, validation_results, total_count):
    """将验证结果导出为 Excel 或 CSV。"""
    df = pd.DataFrame(validation_results, columns=['车型', '实际LCC', '估计LCC', '相对误差'])
    summary = build_validation_summary(validation_results, total_count)
    distribution = build_error_distribution(validation_results)

    output_path = Path(file_path)
    if output_path.suffix.lower() == '.csv':
        base = output_path.with_suffix('')
        summary.to_csv(base.with_name(f'{base.name}_汇总.csv'), index=False, encoding='utf-8-sig')
        distribution.to_csv(base.with_name(f'{base.name}_误差分布.csv'), index=False, encoding='utf-8-sig')
        df.to_csv(base.with_name(f'{base.name}_明细.csv'), index=False, encoding='utf-8-sig')
        return

    with pd.ExcelWriter(output_path) as writer:
        summary.to_excel(writer, sheet_name='汇总', index=False)
        distribution.to_excel(writer, sheet_name='误差分布', index=False)
        df.to_excel(writer, sheet_name='详细数据', index=False)
