"""SQLite 数据访问模块。

当前阶段先提供数据库层骨架，后续可把 CSV 案例库迁移为长期积累的 SQLite 案例库。
默认按当前项目使用的中文 CSV 表头进行字段映射。
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


class CaseDatabase:
    """案例库 SQLite 访问类。"""

    COLUMN_MAPPING = {
        '车型': 'model_name',
        '长': 'length',
        '宽': 'width',
        '高': 'height',
        '轴距': 'wheelbase',
        '最大功率': 'power',
        '最大扭矩': 'torque',
        '续航里程': 'range_km',
        '电池类型': 'battery_type',
        '快充时间': 'charge_time',
        '价格': 'sale_price',
        'LCC（10年）': 'lcc_total',
    }

    def __init__(self, db_path):
        self.db_path = Path(db_path)

    def connect(self):
        """创建数据库连接。"""
        return sqlite3.connect(self.db_path)

    def initialize(self):
        """初始化案例表结构。

        当前只建立基础表，字段设计后续可随需求继续扩展。
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicle_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT,
                    length REAL,
                    width REAL,
                    height REAL,
                    wheelbase REAL,
                    power REAL,
                    torque REAL,
                    range_km REAL,
                    battery_type TEXT,
                    charge_time REAL,
                    sale_price REAL,
                    lcc_total REAL,
                    data_source TEXT,
                    collected_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_batches (
                    batch_id TEXT PRIMARY KEY,
                    algorithm TEXT,
                    sample_count INTEGER,
                    avg_error REAL,
                    mape REAL,
                    rmse REAL,
                    max_error REAL,
                    min_error REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT,
                    model_name TEXT,
                    actual_lcc REAL,
                    estimated_lcc REAL,
                    relative_error REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(batch_id) REFERENCES validation_batches(batch_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS estimate_batches (
                    batch_id TEXT PRIMARY KEY,
                    algorithm TEXT,
                    estimated_lcc REAL,
                    relative_error REAL,
                    confidence TEXT,
                    purchase_cost REAL,
                    use_cost REAL,
                    recycle_income REAL,
                    total_lcc REAL,
                    input_snapshot TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS estimate_neighbors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT,
                    model_name TEXT,
                    case_lcc REAL,
                    similarity REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(batch_id) REFERENCES estimate_batches(batch_id)
                )
                """
            )

    def import_csv(self, csv_path, data_source='CSV导入', replace_existing=False):
        """按当前项目 CSV 结构导入案例数据。

        预期表头：
        车型, 长, 宽, 高, 轴距, 最大功率, 最大扭矩, 续航里程, 电池类型, 快充时间, 价格, LCC（10年）
        """
        df = pd.read_csv(csv_path)
        missing_columns = [col for col in self.COLUMN_MAPPING if col not in df.columns]
        if missing_columns:
            raise ValueError(f'CSV 缺少必要列: {missing_columns}')

        renamed_df = df.rename(columns=self.COLUMN_MAPPING).copy()
        renamed_df['data_source'] = data_source
        renamed_df['collected_at'] = ''

        ordered_columns = [
            'model_name', 'length', 'width', 'height', 'wheelbase',
            'power', 'torque', 'range_km', 'battery_type', 'charge_time',
            'sale_price', 'lcc_total', 'data_source', 'collected_at',
        ]
        renamed_df = renamed_df[ordered_columns]

        with self.connect() as conn:
            if replace_existing:
                conn.execute('DELETE FROM vehicle_cases')
                conn.execute("DELETE FROM sqlite_sequence WHERE name='vehicle_cases'")
            renamed_df.to_sql('vehicle_cases', conn, if_exists='append', index=False)

    def count_cases(self):
        """返回当前案例库记录数。"""
        with self.connect() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM vehicle_cases')
            return cursor.fetchone()[0]

    def get_cases(self, keyword='', sort_by='id', ascending=False):
        """查询案例库数据。"""
        allowed_sort_fields = {
            'id': 'id',
            '车型': 'model_name',
            '价格': 'sale_price',
            'LCC（10年）': 'lcc_total',
            '创建时间': 'created_at',
            '更新时间': 'updated_at',
        }
        sort_column = allowed_sort_fields.get(sort_by, 'id')
        sort_order = 'ASC' if ascending else 'DESC'

        sql = """
        SELECT id, model_name, length, width, height, wheelbase, power, torque,
               range_km, battery_type, charge_time, sale_price, lcc_total,
               data_source, collected_at, created_at, updated_at
        FROM vehicle_cases
        """
        params = []
        if keyword:
            sql += ' WHERE model_name LIKE ? '
            params.append(f'%{keyword}%')
        sql += f' ORDER BY {sort_column} {sort_order}'
        with self.connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def export_cases_dataframe(self):
        """导出案例库为 DataFrame。"""
        df = self.get_cases()
        if df.empty:
            return pd.DataFrame(columns=list(self.COLUMN_MAPPING.keys()))
        export_df = df.rename(
            columns={
                'model_name': '车型',
                'length': '长',
                'width': '宽',
                'height': '高',
                'wheelbase': '轴距',
                'power': '最大功率',
                'torque': '最大扭矩',
                'range_km': '续航里程',
                'battery_type': '电池类型',
                'charge_time': '快充时间',
                'sale_price': '价格',
                'lcc_total': 'LCC（10年）',
            }
        )
        return export_df[['车型', '长', '宽', '高', '轴距', '最大功率', '最大扭矩', '续航里程', '电池类型', '快充时间', '价格', 'LCC（10年）']]

    def insert_case(self, case_data):
        """新增案例。"""
        fields = [
            'model_name', 'length', 'width', 'height', 'wheelbase', 'power', 'torque',
            'range_km', 'battery_type', 'charge_time', 'sale_price', 'lcc_total',
            'data_source', 'collected_at'
        ]
        values = [case_data.get(field) for field in fields]
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO vehicle_cases ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
                values,
            )

    def update_case(self, case_id, case_data):
        """更新案例。"""
        fields = [
            'model_name', 'length', 'width', 'height', 'wheelbase', 'power', 'torque',
            'range_km', 'battery_type', 'charge_time', 'sale_price', 'lcc_total',
            'data_source', 'collected_at'
        ]
        assignments = ', '.join([f'{field} = ?' for field in fields] + ['updated_at = CURRENT_TIMESTAMP'])
        values = [case_data.get(field) for field in fields] + [case_id]
        with self.connect() as conn:
            conn.execute(f'UPDATE vehicle_cases SET {assignments} WHERE id = ?', values)

    def delete_cases(self, case_ids):
        """批量删除案例。"""
        if not case_ids:
            return
        placeholders = ','.join(['?'] * len(case_ids))
        with self.connect() as conn:
            conn.execute(f'DELETE FROM vehicle_cases WHERE id IN ({placeholders})', case_ids)

    def clear_cases(self):
        """清空案例库并重置自增 ID。"""
        with self.connect() as conn:
            conn.execute('DELETE FROM vehicle_cases')
            conn.execute("DELETE FROM sqlite_sequence WHERE name='vehicle_cases'")

    def save_validation_results(self, algorithm, validation_results, metrics):
        """保存一次模型验证结果。"""
        batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
        rows = [
            (batch_id, row[0], float(row[1]), float(row[2]), float(row[3]))
            for row in validation_results
        ]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO validation_batches (
                    batch_id, algorithm, sample_count, avg_error, mape, rmse, max_error, min_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    algorithm,
                    metrics['sample_count'],
                    metrics['avg_error'],
                    metrics['mape'],
                    metrics['rmse'],
                    metrics['max_error'],
                    metrics['min_error'],
                ),
            )
            conn.executemany(
                """
                INSERT INTO validation_results (
                    batch_id, model_name, actual_lcc, estimated_lcc, relative_error
                ) VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )
        return batch_id

    def get_validation_batches(self, keyword=''):
        """查询验证批次。"""
        sql = """
        SELECT batch_id, algorithm, sample_count, avg_error, mape, rmse, max_error, min_error, created_at
        FROM validation_batches
        """
        params = []
        if keyword:
            sql += ' WHERE algorithm LIKE ? OR batch_id LIKE ? '
            params.extend([f'%{keyword}%'] * 2)
        sql += ' ORDER BY created_at DESC'
        with self.connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def get_validation_results(self, batch_id):
        """查询某个批次的验证明细。"""
        sql = """
        SELECT id, batch_id, model_name, actual_lcc, estimated_lcc, relative_error, created_at
        FROM validation_results
        WHERE batch_id = ?
        ORDER BY id ASC
        """
        params = [batch_id]
        with self.connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def export_validation_batch(self, batch_id):
        """导出某个验证批次的批次信息和明细。"""
        batch_df = self.get_validation_batches(batch_id)
        details_df = self.get_validation_results(batch_id)
        return batch_df, details_df

    def delete_validation_batches(self, batch_ids):
        """按批次删除验证记录（含明细）。"""
        if not batch_ids:
            return
        placeholders = ','.join(['?'] * len(batch_ids))
        with self.connect() as conn:
            conn.execute(f'DELETE FROM validation_results WHERE batch_id IN ({placeholders})', batch_ids)
            conn.execute(f'DELETE FROM validation_batches WHERE batch_id IN ({placeholders})', batch_ids)

    def clear_validation_records(self):
        """清空全部验证批次与明细。"""
        with self.connect() as conn:
            conn.execute('DELETE FROM validation_results')
            conn.execute('DELETE FROM validation_batches')
            conn.execute("DELETE FROM sqlite_sequence WHERE name='validation_results'")

    def save_estimate_result(self, algorithm, estimated_lcc, relative_error, confidence, lcc_breakdown, input_snapshot, neighbors):
        """保存一次估算结果和相似案例明细。"""
        batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO estimate_batches (
                    batch_id, algorithm, estimated_lcc, relative_error, confidence,
                    purchase_cost, use_cost, recycle_income, total_lcc, input_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    algorithm,
                    float(estimated_lcc),
                    float(relative_error),
                    confidence,
                    float(lcc_breakdown['购置成本']),
                    float(lcc_breakdown['使用成本']),
                    float(lcc_breakdown['回收收益']),
                    float(lcc_breakdown['总LCC']),
                    input_snapshot,
                ),
            )
            conn.executemany(
                """
                INSERT INTO estimate_neighbors (batch_id, model_name, case_lcc, similarity)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (batch_id, neighbor['车型'], float(neighbor['LCC（10年）']), float(neighbor['similarity']))
                    for neighbor in neighbors
                ],
            )
        return batch_id

    def get_estimate_batches(self, keyword=''):
        """查询估算批次。"""
        sql = """
        SELECT batch_id, algorithm, estimated_lcc, relative_error, confidence,
               purchase_cost, use_cost, recycle_income, total_lcc, created_at
        FROM estimate_batches
        """
        params = []
        if keyword:
            sql += ' WHERE algorithm LIKE ? OR batch_id LIKE ? OR confidence LIKE ? '
            params.extend([f'%{keyword}%'] * 3)
        sql += ' ORDER BY created_at DESC'
        with self.connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def get_estimate_neighbors(self, batch_id):
        """查询估算批次对应的相似案例明细。"""
        with self.connect() as conn:
            return pd.read_sql_query(
                """
                SELECT id, batch_id, model_name, case_lcc, similarity, created_at
                FROM estimate_neighbors
                WHERE batch_id = ?
                ORDER BY id ASC
                """,
                conn,
                params=[batch_id],
            )

    def export_estimate_batch(self, batch_id):
        """导出某个估算批次及相似案例明细。"""
        batch_df = self.get_estimate_batches(batch_id)
        details_df = self.get_estimate_neighbors(batch_id)
        return batch_df, details_df

    def delete_estimate_batches(self, batch_ids):
        """按批次删除估算记录（含相似案例明细）。"""
        if not batch_ids:
            return
        placeholders = ','.join(['?'] * len(batch_ids))
        with self.connect() as conn:
            conn.execute(f'DELETE FROM estimate_neighbors WHERE batch_id IN ({placeholders})', batch_ids)
            conn.execute(f'DELETE FROM estimate_batches WHERE batch_id IN ({placeholders})', batch_ids)

    def clear_estimate_records(self):
        """清空全部估算批次与相似案例明细。"""
        with self.connect() as conn:
            conn.execute('DELETE FROM estimate_neighbors')
            conn.execute('DELETE FROM estimate_batches')
            conn.execute("DELETE FROM sqlite_sequence WHERE name='estimate_neighbors'")
