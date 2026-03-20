"""Tkinter 图形界面。"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from cbr_core import LCCEstimatorCore, SimilarityEngine
from config import ALGORITHMS, DEFAULT_DB_PATH, DEFAULT_VALUES, FEATURE_CONFIG, FEATURES, VALID_ERROR_THRESHOLD
from data_manager import DataProcessor
from database import CaseDatabase
from lcc_model import LCCCostModel
from record_windows import open_case_manager_window, open_estimate_records_window, open_validation_records_window
from validation import (
    ValidationService,
    build_error_distribution,
    build_validation_metrics,
    export_validation_results,
)
from widgets import WheelEntry


class LCCEstimatorApp(tk.Tk):
    """新能源汽车 LCC 估算系统主界面。"""

    def __init__(self):
        super().__init__()
        self.title('基于CBR方法的新能源汽车LCC估算系统')
        self.geometry('1100x780')

        self.default_values = DEFAULT_VALUES
        self.feature_config = FEATURE_CONFIG
        self.data_processor = None
        self.engine = None
        self.case_database = CaseDatabase(DEFAULT_DB_PATH)
        self.lcc_cost_model = LCCCostModel()
        self.current_algorithm = tk.StringVar(value='manhattan')
        self.validation_results = []
        self.validation_all_results = []
        self.last_validation_batch_id = ''
        self.last_estimate_batch_id = ''
        self.current_data_source = tk.StringVar(value='未加载')
        self.case_count_var = tk.StringVar(value='0')
        self.last_estimate_var = tk.StringVar(value='暂无')
        self.status_var = tk.StringVar(value='等待载入案例库')
        self.create_widgets()

    def create_widgets(self):
        """创建主界面控件。"""
        toolbar = ttk.Frame(self)
        ttk.Button(toolbar, text='载入CSV文件', command=self.load_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='案例库管理', command=self.open_case_manager).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='从数据库加载', command=self.load_cases_from_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='模型验证', command=self.validate_model).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='验证记录', command=self.open_validation_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='估算记录', command=self.open_estimate_records).pack(side=tk.LEFT, padx=5)

        algo_frame = ttk.Frame(toolbar)
        ttk.Label(algo_frame, text='算法:').pack(side=tk.LEFT)
        algo_selector = ttk.Combobox(
            algo_frame,
            textvariable=self.current_algorithm,
            values=ALGORITHMS,
            state='readonly',
            width=15,
        )
        algo_selector.set('manhattan')
        algo_selector.pack(side=tk.LEFT)
        algo_frame.pack(side=tk.LEFT, padx=10)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=5)

        self._build_status_panel()

        main_body = ttk.Frame(self)
        main_body.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        main_body.columnconfigure(0, weight=2)
        main_body.columnconfigure(1, weight=3)
        main_body.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(main_body)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        right_panel = ttk.Frame(main_body)
        right_panel.grid(row=0, column=1, sticky='nsew')

        self._build_input_panel(left_panel)
        self._build_action_panel(left_panel)
        self._build_result_panel(right_panel)
        self._build_neighbor_panel(right_panel)

        footer = ttk.Label(self, textvariable=self.status_var, foreground='gray')
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=6)

        self.current_algorithm.trace_add('write', self._update_algorithm_display)

    def _build_status_panel(self):
        """创建顶部状态面板。"""
        status_frame = ttk.LabelFrame(self, text='当前状态')
        status_frame.pack(fill=tk.X, padx=8, pady=6)
        items = [
            ('数据源', self.current_data_source),
            ('案例数', self.case_count_var),
            ('最近验证批次', tk.StringVar(value='暂无')),
            ('最近估算', self.last_estimate_var),
        ]
        self.last_batch_var = items[2][1]
        for index, (label_text, variable) in enumerate(items):
            frame = ttk.Frame(status_frame)
            frame.grid(row=0, column=index, padx=18, pady=6, sticky='w')
            ttk.Label(frame, text=f'{label_text}:').pack(side=tk.LEFT)
            ttk.Label(frame, textvariable=variable, foreground='blue').pack(side=tk.LEFT, padx=4)

    def _build_input_panel(self, parent):
        """创建参数输入区。"""
        input_frame = ttk.LabelFrame(parent, text='车辆参数输入（支持滚轮调整）')
        self.input_entries = {}
        feature_labels = [
            ('长（mm）', '长'), ('宽（mm）', '宽'), ('高（mm）', '高'),
            ('轴距（mm）', '轴距'), ('最大功率（kW）', '最大功率'),
            ('最大扭矩（N·m）', '最大扭矩'), ('续航里程（km）', '续航里程'),
            ('电池类型（1-4）', '电池类型'), ('快充时间（分钟）', '快充时间'),
        ]
        for i, (label, key) in enumerate(feature_labels):
            row, col = divmod(i, 2)
            frame = ttk.Frame(input_frame)
            ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
            config = self.feature_config[key]
            ent = WheelEntry(
                frame,
                width=12,
                step=config['step'],
                min_val=config['min'],
                max_val=config['max'],
                is_int=config['is_int'],
            )
            ent.insert(0, str(self.default_values[key]))
            ent.pack(side=tk.LEFT)
            self.input_entries[key] = ent
            frame.grid(row=row, column=col, padx=5, pady=5, sticky=tk.W)
        input_frame.pack(fill=tk.X, pady=(0, 8))

    def _build_action_panel(self, parent):
        """创建操作与说明区。"""
        action_frame = ttk.LabelFrame(parent, text='操作区')
        action_frame.pack(fill=tk.X)
        ttk.Button(action_frame, text='开始估算', command=self.calculate).pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(action_frame, text='模型验证', command=self.validate_model).pack(fill=tk.X, padx=8, pady=6)
        ttk.Separator(action_frame, orient='horizontal').pack(fill=tk.X, padx=8, pady=6)
        tip = (
            '模型说明：\n'
            '1. 使用车辆参数检索相似案例；\n'
            '2. 按相似度加权估算目标车型的 LCC；\n'
            '3. 验证时采用留一法逐条回代评估误差。'
        )
        ttk.Label(action_frame, text=tip, justify='left', foreground='gray').pack(fill=tk.X, padx=8, pady=6)

    def _build_result_panel(self, parent):
        """创建结果展示区。"""
        result_frame = ttk.LabelFrame(parent, text='估算结果总览')
        self.lbl_algo = ttk.Label(result_frame, text='当前算法：曼哈顿距离', foreground='blue')
        self.lbl_algo.pack(anchor='w', pady=3, padx=8)
        self.lbl_result = ttk.Label(result_frame, text='LCC估算值：', font=('Arial', 18, 'bold'))
        self.lbl_result.pack(anchor='w', pady=6, padx=8)
        self.lbl_error = ttk.Label(result_frame, text='相对误差：')
        self.lbl_error.pack(anchor='w', pady=2, padx=8)
        self.lbl_confidence = ttk.Label(result_frame, text='置信度评估：')
        self.lbl_confidence.pack(anchor='w', pady=2, padx=8)

        cost_frame = ttk.Frame(result_frame)
        cost_frame.pack(fill=tk.X, padx=8, pady=8)
        self.lbl_purchase = ttk.Label(cost_frame, text='购置成本：-')
        self.lbl_use_cost = ttk.Label(cost_frame, text='使用成本：-')
        self.lbl_recycle = ttk.Label(cost_frame, text='回收收益：-')
        self.lbl_purchase.grid(row=0, column=0, sticky='w', padx=4, pady=2)
        self.lbl_use_cost.grid(row=0, column=1, sticky='w', padx=12, pady=2)
        self.lbl_recycle.grid(row=0, column=2, sticky='w', padx=12, pady=2)

        result_frame.pack(fill=tk.X, pady=(0, 8))

    def _build_neighbor_panel(self, parent):
        """创建相似案例展示区。"""
        neighbor_frame = ttk.LabelFrame(parent, text='相似案例与估算依据')
        columns = ('车型', 'LCC（万元）', '相似度')
        self.tree = ttk.Treeview(neighbor_frame, columns=columns, show='headings', height=12)
        for col in columns:
            self.tree.heading(col, text=col, anchor='center')
            self.tree.column(col, width=180, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        neighbor_frame.pack(fill=tk.BOTH, expand=True)

    def _update_algorithm_display(self, *args):
        """更新当前算法标签。"""
        algorithm_names = {
            'manhattan': '曼哈顿距离（标准版）',
            'cosine': '余弦相似度（标准版）',
            'experimental_hybrid': '混合相似度（实验版）',
        }
        algorithm = algorithm_names.get(self.current_algorithm.get(), self.current_algorithm.get())
        self.lbl_algo.config(text=f'当前使用算法：{algorithm}')

    def load_csv(self):
        """载入案例 CSV 文件。"""
        file_path = filedialog.askopenfilename(filetypes=[('CSV文件', '*.csv')])
        if not file_path:
            return
        try:
            self.data_processor = DataProcessor(file_path)
            self.engine = SimilarityEngine(self.data_processor)

            self.case_database.initialize()
            self.case_database.import_csv(file_path, data_source='用户提供CSV', replace_existing=True)
            case_count = self.case_database.count_cases()
            self.current_data_source.set('CSV + SQLite初始化')
            self.case_count_var.set(str(case_count))
            self.status_var.set('已完成 CSV 载入，并同步初始化 SQLite 案例库')

            messagebox.showinfo(
                '成功',
                f'已载入{len(self.data_processor.data)}条数据，并已初始化 SQLite 案例库（共 {case_count} 条）',
            )
        except Exception as exc:
            messagebox.showerror('错误', f'文件读取失败：{str(exc)}')

    def load_cases_from_database(self):
        """将数据库中的案例库加载为当前估算数据源。"""
        try:
            self.case_database.initialize()
            df = self.case_database.export_cases_dataframe()
            if df.empty:
                messagebox.showwarning('提示', '数据库中暂无案例数据，请先导入 CSV。')
                return
            self.data_processor = DataProcessor.from_dataframe(df)
            self.engine = SimilarityEngine(self.data_processor)
            self.current_data_source.set('SQLite')
            self.case_count_var.set(str(len(self.data_processor.data)))
            self.status_var.set('已从 SQLite 案例库加载当前估算数据源')
            messagebox.showinfo('成功', f'已从 SQLite 案例库加载 {len(self.data_processor.data)} 条数据')
        except Exception as exc:
            messagebox.showerror('错误', f'数据库加载失败：{str(exc)}')

    def calculate(self):
        """读取输入参数并执行估算。"""
        if not self.engine:
            messagebox.showwarning('警告', '请先载入CSV文件')
            return

        try:
            input_data = self._collect_input_values()
            result = LCCEstimatorCore.estimate(self.engine, input_data, self.current_algorithm.get())
            self._display_results(input_data, *result)
            self.last_estimate_var.set('刚刚完成')
            self.status_var.set('已完成一次 LCC 估算，可查看相似案例和成本拆解')
        except ValueError as exc:
            messagebox.showerror('输入错误', str(exc))

    def _collect_input_values(self):
        """从界面收集输入特征。"""
        input_data = []
        for key in FEATURES:
            value = self.input_entries[key].get()
            if key == '电池类型':
                input_data.append(int(value))
            else:
                input_data.append(float(value))
        return input_data

    def _display_results(self, input_data, estimated_lcc, top_models, confidence, relative_error):
        """把估算结果刷新到界面上。"""
        self.lbl_result.config(text=f'LCC估算值：{estimated_lcc:.2f} 万元')
        self.lbl_error.config(text=f'相对误差：±{relative_error:.2f}%')
        self.lbl_confidence.config(text=f'置信度评估：{confidence}')

        purchase_price = 0.0
        if top_models:
            purchase_price = float(sum(float(model['LCC（10年）']) for model in top_models) / len(top_models))
        lcc_breakdown = self.lcc_cost_model.calculate(
            purchase_price=purchase_price,
            energy_consumption=max(float(input_data[6]) / 20, 0.0),
        )
        self.lbl_purchase.config(text=f"购置成本：{lcc_breakdown['购置成本']:.2f} 万元")
        self.lbl_use_cost.config(text=f"使用成本：{lcc_breakdown['使用成本']:.2f} 元")
        self.lbl_recycle.config(text=f"回收收益：{lcc_breakdown['回收收益']:.2f} 万元")

        input_snapshot = ', '.join([f'{key}={value}' for key, value in zip(FEATURES, input_data)])
        self.case_database.initialize()
        self.last_estimate_batch_id = self.case_database.save_estimate_result(
            self.current_algorithm.get(),
            estimated_lcc,
            relative_error,
            confidence,
            lcc_breakdown,
            input_snapshot,
            top_models,
        )

        for item in self.tree.get_children():
            self.tree.delete(item)
        for model in top_models:
            self.tree.insert('', tk.END, values=(
                model['车型'],
                model['LCC（10年）'],
                f"{model['similarity'] * 100:.2f}%",
            ))

    def validate_model(self):
        """执行模型验证并显示报告。"""
        if not self.data_processor:
            messagebox.showwarning('警告', '请先载入CSV文件')
            return

        progress = self._create_progress_window()
        validator = ValidationService(self.data_processor, self.current_algorithm.get(), VALID_ERROR_THRESHOLD)
        try:
            validation_data = validator.validate_all(
                progress_callback=lambda idx, total: self._update_progress(progress, idx, total)
            )
            self.validation_all_results = validation_data['all_results']
            self.validation_results = validation_data['valid_results']
            self._process_validation_results(validation_data['total_count'])
        except Exception as exc:
            messagebox.showerror('验证错误', str(exc))
        finally:
            progress.destroy()

    def _create_progress_window(self):
        """创建验证进度窗口。"""
        progress = tk.Toplevel(self)
        progress.title('验证进度')
        progress.geometry('300x100')
        ttk.Label(progress, text='正在验证模型...0%').pack(pady=10)
        ttk.Progressbar(progress, length=200, mode='determinate').pack()
        return progress

    def _update_progress(self, window, index, total):
        """更新进度窗口状态。"""
        progress_percent = int((index + 1) / total * 100)
        window.children['!label'].config(text=f'正在验证模型...{progress_percent}%')
        window.children['!progressbar']['value'] = progress_percent
        self.update()

    def _process_validation_results(self, total_count):
        """处理验证结果并决定是否展示报告。"""
        valid_count = len(self.validation_results)
        evaluated_count = len(self.validation_all_results)
        if valid_count == 0:
            messagebox.showwarning('提示', '没有符合误差要求的验证结果')
            return
        self.case_database.initialize()
        metrics = build_validation_metrics(self.validation_all_results, total_count)
        batch_id = self.case_database.save_validation_results(self.current_algorithm.get(), self.validation_all_results, metrics)
        avg_error = sum(res[3] for res in self.validation_all_results) / evaluated_count
        self.last_validation_batch_id = batch_id
        self.last_batch_var.set(batch_id)
        self.status_var.set('已完成模型验证，并保存验证批次记录')
        self._show_validation_report(avg_error, total_count, valid_count, evaluated_count, metrics)

    def _show_validation_report(self, avg_error, total_count, valid_count, evaluated_count, metrics):
        """展示模型验证结果窗口。"""
        report_window = tk.Toplevel(self)
        report_window.title('模型验证报告')
        report_window.geometry('950x650')

        pass_rate = (valid_count / evaluated_count * 100) if evaluated_count else 0.0
        stats_text = (
            f'总样本：{total_count} | 可评估样本：{evaluated_count} | '
            f'误差≤{VALID_ERROR_THRESHOLD}%样本：{valid_count}（占比 {pass_rate:.2f}%）'
        )
        ttk.Label(report_window, text=stats_text, font=('Arial', 12, 'bold')).pack(pady=8)
        metric_text = (
            f"平均误差：{avg_error:.2f}%   MAPE：{metrics['mape']:.2f}%   RMSE：{metrics['rmse']:.2f}   "
            f"最大误差：{metrics['max_error']:.2f}%   最小误差：{metrics['min_error']:.2f}%"
        )
        ttk.Label(report_window, text=metric_text, foreground='blue').pack(pady=4)

        distribution_df = build_error_distribution(self.validation_all_results)
        distribution_text = ' | '.join(
            [
                f"{row['误差区间']}: {int(row['样本数'])} ({float(row['占比(%)']):.2f}%)"
                for _, row in distribution_df.iterrows()
            ]
        )
        ttk.Label(report_window, text=f'误差分布：{distribution_text}', foreground='gray').pack(pady=4)

        columns = ('车型', '实际LCC', '估计LCC', '相对误差')
        tree = ttk.Treeview(report_window, columns=columns, show='headings', height=20)
        for col in columns:
            tree.heading(col, text=col, anchor='center')
            tree.column(col, width=200 if col == '车型' else 120, anchor='center')

        scrollbar = ttk.Scrollbar(report_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=lambda first, last: scrollbar.set(first, last))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        for res in self.validation_all_results:
            tree.insert('', tk.END, values=(res[0], f'{res[1]:.2f}', f'{res[2]:.2f}', f'{res[3]:.2f}%'))

        ttk.Button(report_window, text='导出结果', command=self._export_validation_data).pack(pady=10)

    def _export_validation_data(self):
        """导出验证报告。"""
        if not self.validation_all_results:
            messagebox.showwarning('警告', '没有可导出的验证结果')
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel文件', '*.xlsx'), ('CSV文件', '*.csv')],
        )
        if not file_path:
            return

        try:
            processor = self.data_processor
            total_count = len(processor.data) if processor is not None else len(self.validation_all_results)
            export_validation_results(file_path, self.validation_all_results, total_count)
            if file_path.lower().endswith('.csv'):
                messagebox.showinfo('成功', 'CSV 报告已导出（汇总/误差分布/明细三个文件）')
            else:
                messagebox.showinfo('成功', 'Excel 报告已导出（含汇总/误差分布/明细）')
        except Exception as exc:
            messagebox.showerror('导出失败', f'错误信息：{str(exc)}')

    def open_case_manager(self):
        """打开案例库管理窗口。"""
        open_case_manager_window(self, self.case_database)

    def open_validation_records(self):
        """打开验证记录窗口。"""
        open_validation_records_window(self, self.case_database)

    def open_estimate_records(self):
        """打开估算记录窗口。"""
        open_estimate_records_window(self, self.case_database)
