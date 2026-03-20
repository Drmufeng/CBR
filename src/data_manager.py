"""数据读取、清洗与归一化处理。"""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from config import FEATURES, TARGET_COLUMN


class DataProcessor:
    """负责案例库数据的读入、清洗和标准化。"""

    def __init__(self, file_path):
        self.data = pd.read_csv(file_path)
        self._initialize()

    @classmethod
    def from_dataframe(cls, dataframe):
        """根据已有 DataFrame 创建处理器。"""
        instance = cls.__new__(cls)
        instance.data = dataframe.copy()
        instance._initialize()
        return instance

    def _initialize(self):
        """统一初始化字段和归一化流程。"""
        self.features = FEATURES.copy()
        self.target = TARGET_COLUMN
        self._clean_data()
        self.scaler = MinMaxScaler()
        self.data_normalized = self._normalize_data()

    def _clean_data(self):
        """移除缺失值和非正数特征行。

        数据可能来自 CSV、SQLite 或手工录入，因此这里统一做一次数值转换，
        避免字符串类型参与比较时报错。
        """
        numeric_columns = self.features + [self.target]
        for column in numeric_columns:
            self.data[column] = pd.to_numeric(self.data[column], errors='coerce')

        self.data = self.data.dropna().reset_index(drop=True)
        self.data = self.data[(self.data[self.features] > 0).all(axis=1)]

    def _normalize_data(self):
        """对特征列进行最小-最大归一化。"""
        return pd.DataFrame(
            self.scaler.fit_transform(self.data[self.features]),
            columns=self.features,
        )

    def normalize_input(self, input_data):
        """将单条输入按训练特征名归一化，避免特征名告警。"""
        input_df = pd.DataFrame([input_data], columns=self.features)
        return self.scaler.transform(input_df)[0]

    def find_exact_matches(self, input_data):
        """查找与输入特征完全一致的案例。"""
        query = pd.Series(dict(zip(self.features, input_data)))
        matches = self.data[self.data[self.features].apply(lambda row: all(row == query), axis=1)]
        return matches[self.target].values if not matches.empty else None

    def create_subset_without_index(self, exclude_index):
        """生成排除指定样本后的临时处理器，用于留一验证。"""
        new_processor = DataProcessor.__new__(DataProcessor)
        new_processor.data = self.data.drop(index=exclude_index).reset_index(drop=True)
        new_processor.features = self.features.copy()
        new_processor.target = self.target
        new_processor.scaler = MinMaxScaler()
        new_processor.data_normalized = pd.DataFrame(
            new_processor.scaler.fit_transform(new_processor.data[new_processor.features]),
            columns=new_processor.features,
        )
        return new_processor
