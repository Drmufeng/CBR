"""项目中的静态配置项。"""

from pathlib import Path

DEFAULT_VALUES = {
    '长': 5885,
    '宽': 2027,
    '高': 1930,
    '轴距': 3874,
    '最大功率': 750,
    '最大扭矩': 1350,
    '续航里程': 547,
    '电池类型': 4,
    '快充时间': 25,
}

FEATURE_CONFIG = {
    '长': {'step': 10, 'min': 1000, 'max': 6000, 'is_int': True},
    '宽': {'step': 10, 'min': 1000, 'max': 2500, 'is_int': True},
    '高': {'step': 10, 'min': 1000, 'max': 2500, 'is_int': True},
    '轴距': {'step': 10, 'min': 1000, 'max': 3500, 'is_int': True},
    '最大功率': {'step': 5, 'min': 50, 'max': 500, 'is_int': False},
    '最大扭矩': {'step': 10, 'min': 100, 'max': 1000, 'is_int': False},
    '续航里程': {'step': 10, 'min': 100, 'max': 1000, 'is_int': True},
    '电池类型': {'step': 1, 'min': 1, 'max': 4, 'is_int': True},
    '快充时间': {'step': 1, 'min': 10, 'max': 120, 'is_int': True},
}

FEATURES = ['长', '宽', '高', '轴距', '最大功率', '最大扭矩', '续航里程', '电池类型', '快充时间']
TARGET_COLUMN = 'LCC（10年）'
ALGORITHMS = ['manhattan', 'cosine', 'experimental_hybrid']
VALID_ERROR_THRESHOLD = 30

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
DEFAULT_DB_PATH = DATA_DIR / 'cases.db'
