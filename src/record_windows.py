"""案例库、验证记录、估算记录窗口。"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd


def open_case_manager_window(parent, case_database):
    """打开案例库管理窗口。"""
    case_database.initialize()
    window = tk.Toplevel(parent)
    window.title('案例库管理')
    window.geometry('1250x650')

    top_bar = ttk.Frame(window)
    keyword_var = tk.StringVar()
    sort_var = tk.StringVar(value='id')
    order_var = tk.StringVar(value='倒序')
    ttk.Label(top_bar, text='车型筛选:').pack(side=tk.LEFT, padx=5)
    ttk.Entry(top_bar, textvariable=keyword_var, width=30).pack(side=tk.LEFT, padx=5)
    ttk.Label(top_bar, text='排序字段:').pack(side=tk.LEFT, padx=(12, 5))
    ttk.Combobox(
        top_bar,
        textvariable=sort_var,
        values=['id', '车型', '价格', 'LCC（10年）', '创建时间', '更新时间'],
        state='readonly',
        width=12,
    ).pack(side=tk.LEFT, padx=5)
    ttk.Combobox(top_bar, textvariable=order_var, values=['正序', '倒序'], state='readonly', width=8).pack(side=tk.LEFT, padx=5)
    ttk.Label(top_bar, text='提示：支持 Ctrl 多选、Shift 区间选择').pack(side=tk.RIGHT, padx=5)
    top_bar.pack(fill=tk.X, padx=10, pady=10)

    columns = ('id', '车型', '长', '宽', '高', '轴距', '最大功率', '最大扭矩', '续航里程', '电池类型', '快充时间', '价格', 'LCC（10年）', '来源', '创建时间')
    tree = ttk.Treeview(window, columns=columns, show='headings', height=22, selectmode='extended')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=85 if col != '车型' else 180, anchor='center')
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    button_bar = ttk.Frame(window)
    button_bar.pack(fill=tk.X, padx=10, pady=5)

    def refresh_cases():
        df = case_database.get_cases(
            keyword=keyword_var.get().strip(),
            sort_by=sort_var.get(),
            ascending=(order_var.get() == '正序'),
        )
        for item in tree.get_children():
            tree.delete(item)
        for _, row in df.iterrows():
            tree.insert('', tk.END, values=(
                row['id'], row['model_name'], row['length'], row['width'], row['height'], row['wheelbase'],
                row['power'], row['torque'], row['range_km'], row['battery_type'], row['charge_time'],
                row['sale_price'], row['lcc_total'], row['data_source'], row['created_at'],
            ))

    def export_cases():
        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel文件', '*.xlsx')])
        if not file_path:
            return
        df = case_database.export_cases_dataframe()
        df.to_excel(file_path, index=False)
        messagebox.showinfo('成功', '案例库已导出')

    def import_cases():
        file_path = filedialog.askopenfilename(filetypes=[('CSV文件', '*.csv')])
        if not file_path:
            return
        case_database.import_csv(file_path, data_source='案例库管理导入', replace_existing=False)
        refresh_cases()
        messagebox.showinfo('成功', 'CSV 已导入数据库')

    def open_case_form(case_values=None):
        form = tk.Toplevel(window)
        form.title('新增案例' if case_values is None else '编辑案例')
        form.geometry('520x560')

        field_map = [
            ('车型', 'model_name'), ('长', 'length'), ('宽', 'width'), ('高', 'height'), ('轴距', 'wheelbase'),
            ('最大功率', 'power'), ('最大扭矩', 'torque'), ('续航里程', 'range_km'), ('电池类型', 'battery_type'),
            ('快充时间', 'charge_time'), ('价格', 'sale_price'), ('LCC（10年）', 'lcc_total'), ('来源', 'data_source'), ('采集时间', 'collected_at'),
        ]
        entries = {}
        initial = {}
        if case_values is not None:
            initial = {
                'id': case_values[0], 'model_name': case_values[1], 'length': case_values[2], 'width': case_values[3],
                'height': case_values[4], 'wheelbase': case_values[5], 'power': case_values[6], 'torque': case_values[7],
                'range_km': case_values[8], 'battery_type': case_values[9], 'charge_time': case_values[10], 'sale_price': case_values[11],
                'lcc_total': case_values[12], 'data_source': case_values[13], 'collected_at': '',
            }

        body = ttk.Frame(form)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        for idx, (label, key) in enumerate(field_map):
            ttk.Label(body, text=label, width=12).grid(row=idx, column=0, sticky='w', pady=4)
            entry = ttk.Entry(body, width=35)
            entry.grid(row=idx, column=1, sticky='ew', pady=4)
            if key in initial and initial[key] is not None:
                entry.insert(0, str(initial[key]))
            entries[key] = entry

        def save_case():
            data = {key: entries[key].get().strip() for _, key in field_map}
            numeric_fields = ['length', 'width', 'height', 'wheelbase', 'power', 'torque', 'range_km', 'charge_time', 'sale_price', 'lcc_total']
            for field in numeric_fields:
                data[field] = float(data[field]) if data[field] else None
            if case_values is None:
                case_database.insert_case(data)
            else:
                case_database.update_case(initial['id'], data)
            form.destroy()
            refresh_cases()
            messagebox.showinfo('成功', '案例已保存')

        ttk.Button(body, text='保存', command=save_case).grid(row=len(field_map), column=1, sticky='e', pady=12)

    def select_all_cases():
        for item in tree.get_children():
            tree.selection_add(item)

    def delete_selected_cases():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning('提示', '请先选择要删除的案例')
            return
        if not messagebox.askyesno('确认', '确定删除选中的案例吗？'):
            return
        case_ids = [int(tree.item(item, 'values')[0]) for item in selected]
        case_database.delete_cases(case_ids)
        refresh_cases()
        messagebox.showinfo('成功', '选中案例已删除')

    def clear_all_cases():
        if not messagebox.askyesno('确认', '确定清空整个案例库吗？该操作不可撤销。'):
            return
        case_database.clear_cases()
        refresh_cases()
        messagebox.showinfo('成功', '案例库已清空，ID 已重置')

    ttk.Button(top_bar, text='查询', command=refresh_cases).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_bar, text='排序刷新', command=refresh_cases).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_bar, text='新增案例', command=lambda: open_case_form()).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        button_bar,
        text='编辑选中案例',
        command=lambda: open_case_form(tree.item(tree.selection()[0], 'values')) if tree.selection() else messagebox.showwarning('提示', '请先选择一条案例'),
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_bar, text='全选', command=select_all_cases).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_bar, text='删除选中', command=delete_selected_cases).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_bar, text='清空案例库', command=clear_all_cases).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_bar, text='导入CSV', command=import_cases).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_bar, text='导出案例库', command=export_cases).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_bar, text='刷新', command=refresh_cases).pack(side=tk.LEFT, padx=5)

    refresh_cases()


def open_validation_records_window(parent, case_database):
    """打开验证记录窗口。"""
    case_database.initialize()
    window = tk.Toplevel(parent)
    window.title('验证记录')
    window.geometry('1100x700')

    top_bar = ttk.Frame(window)
    keyword_var = tk.StringVar()
    ttk.Label(top_bar, text='筛选:').pack(side=tk.LEFT, padx=5)
    ttk.Entry(top_bar, textvariable=keyword_var, width=30).pack(side=tk.LEFT, padx=5)
    top_bar.pack(fill=tk.X, padx=10, pady=10)

    batch_frame = ttk.LabelFrame(window, text='验证批次')
    batch_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
    batch_columns = ('批次号', '算法', '样本数', '平均误差', 'MAPE', 'RMSE', '最大误差', '最小误差', '保存时间')
    batch_tree = ttk.Treeview(batch_frame, columns=batch_columns, show='headings', height=8, selectmode='extended')
    for col in batch_columns:
        batch_tree.heading(col, text=col)
        batch_tree.column(col, width=110 if col != '批次号' else 150, anchor='center')
    batch_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    detail_frame = ttk.LabelFrame(window, text='批次明细')
    detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    detail_columns = ('序号', '车型', '实际LCC', '估计LCC', '相对误差', '保存时间')
    detail_tree = ttk.Treeview(detail_frame, columns=detail_columns, show='headings', height=16)
    for col in detail_columns:
        detail_tree.heading(col, text=col)
        detail_tree.column(col, width=120 if col != '车型' else 220, anchor='center')
    detail_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def refresh_batch_list():
        df = case_database.get_validation_batches(keyword_var.get().strip())
        for item in batch_tree.get_children():
            batch_tree.delete(item)
        for item in detail_tree.get_children():
            detail_tree.delete(item)
        for _, row in df.iterrows():
            batch_tree.insert('', tk.END, values=(
                row['batch_id'], row['algorithm'], row['sample_count'],
                f"{row['avg_error']:.2f}%", f"{row['mape']:.2f}%", f"{row['rmse']:.2f}",
                f"{row['max_error']:.2f}%", f"{row['min_error']:.2f}%", row['created_at'],
            ))

    def refresh_detail_list(batch_id):
        df = case_database.get_validation_results(batch_id)
        for item in detail_tree.get_children():
            detail_tree.delete(item)
        for index, (_, row) in enumerate(df.iterrows(), start=1):
            detail_tree.insert('', tk.END, values=(
                index, row['model_name'], row['actual_lcc'], row['estimated_lcc'],
                f"{row['relative_error']:.2f}%", row['created_at'],
            ))

    def handle_batch_select(_event=None):
        selected = batch_tree.selection()
        if not selected:
            return
        batch_id = batch_tree.item(selected[0], 'values')[0]
        refresh_detail_list(batch_id)

    def export_records():
        selected = batch_tree.selection()
        if not selected:
            messagebox.showwarning('提示', '请先选择一个验证批次')
            return
        batch_id = batch_tree.item(selected[0], 'values')[0]
        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel文件', '*.xlsx'), ('CSV文件', '*.csv')],
        )
        if not file_path:
            return
        batch_df, details_df = case_database.export_validation_batch(batch_id)
        if file_path.lower().endswith('.csv'):
            base_path, _ = os.path.splitext(file_path)
            summary_csv = f'{base_path}_批次汇总.csv'
            details_csv = f'{base_path}_批次明细.csv'
            batch_df.to_csv(summary_csv, index=False, encoding='utf-8-sig')
            details_df.to_csv(details_csv, index=False, encoding='utf-8-sig')
            messagebox.showinfo('成功', f'验证记录已导出为 CSV:\n{summary_csv}\n{details_csv}')
            return

        with pd.ExcelWriter(file_path) as writer:
            batch_df.to_excel(writer, sheet_name='批次汇总', index=False)
            details_df.to_excel(writer, sheet_name='批次明细', index=False)
        messagebox.showinfo('成功', '验证记录已导出为 Excel')

    def delete_selected_batches():
        selected = batch_tree.selection()
        if not selected:
            messagebox.showwarning('提示', '请先选择要删除的验证批次')
            return
        if not messagebox.askyesno('确认', '确定删除选中的验证批次吗？'):
            return
        batch_ids = [batch_tree.item(item, 'values')[0] for item in selected]
        case_database.delete_validation_batches(batch_ids)
        refresh_batch_list()
        messagebox.showinfo('成功', '选中验证批次已删除')

    def clear_all_records():
        if not messagebox.askyesno('确认', '确定清空全部验证记录吗？该操作不可撤销。'):
            return
        case_database.clear_validation_records()
        refresh_batch_list()
        messagebox.showinfo('成功', '验证记录已清空')

    ttk.Button(top_bar, text='查询', command=refresh_batch_list).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_bar, text='导出', command=export_records).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_bar, text='删除选中批次', command=delete_selected_batches).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_bar, text='清空验证记录', command=clear_all_records).pack(side=tk.LEFT, padx=5)
    batch_tree.bind('<<TreeviewSelect>>', handle_batch_select)
    refresh_batch_list()


def open_estimate_records_window(parent, case_database):
    """打开估算记录窗口。"""
    case_database.initialize()
    window = tk.Toplevel(parent)
    window.title('估算记录')
    window.geometry('1100x700')

    top_bar = ttk.Frame(window)
    keyword_var = tk.StringVar()
    ttk.Label(top_bar, text='筛选:').pack(side=tk.LEFT, padx=5)
    ttk.Entry(top_bar, textvariable=keyword_var, width=30).pack(side=tk.LEFT, padx=5)
    top_bar.pack(fill=tk.X, padx=10, pady=10)

    batch_frame = ttk.LabelFrame(window, text='估算批次')
    batch_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
    batch_columns = ('批次号', '算法', '估算LCC', '相对误差', '置信度', '购置成本', '使用成本', '回收收益', '保存时间')
    batch_tree = ttk.Treeview(batch_frame, columns=batch_columns, show='headings', height=8, selectmode='extended')
    for col in batch_columns:
        batch_tree.heading(col, text=col)
        batch_tree.column(col, width=110 if col != '批次号' else 150, anchor='center')
    batch_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    detail_frame = ttk.LabelFrame(window, text='相似案例明细')
    detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    detail_columns = ('序号', '车型', '案例LCC', '相似度', '保存时间')
    detail_tree = ttk.Treeview(detail_frame, columns=detail_columns, show='headings', height=16)
    for col in detail_columns:
        detail_tree.heading(col, text=col)
        detail_tree.column(col, width=140 if col != '车型' else 220, anchor='center')
    detail_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def refresh_batch_list():
        df = case_database.get_estimate_batches(keyword_var.get().strip())
        for item in batch_tree.get_children():
            batch_tree.delete(item)
        for item in detail_tree.get_children():
            detail_tree.delete(item)
        for _, row in df.iterrows():
            batch_tree.insert('', tk.END, values=(
                row['batch_id'], row['algorithm'], f"{row['estimated_lcc']:.2f}",
                f"{row['relative_error']:.2f}%", row['confidence'],
                f"{row['purchase_cost']:.2f}", f"{row['use_cost']:.2f}", f"{row['recycle_income']:.2f}", row['created_at'],
            ))

    def refresh_detail_list(batch_id):
        df = case_database.get_estimate_neighbors(batch_id)
        for item in detail_tree.get_children():
            detail_tree.delete(item)
        for index, (_, row) in enumerate(df.iterrows(), start=1):
            detail_tree.insert('', tk.END, values=(
                index, row['model_name'], row['case_lcc'], f"{row['similarity'] * 100:.2f}%", row['created_at'],
            ))

    def handle_batch_select(_event=None):
        selected = batch_tree.selection()
        if not selected:
            return
        batch_id = batch_tree.item(selected[0], 'values')[0]
        refresh_detail_list(batch_id)

    def export_records():
        selected = batch_tree.selection()
        if not selected:
            messagebox.showwarning('提示', '请先选择一个估算批次')
            return
        batch_id = batch_tree.item(selected[0], 'values')[0]
        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel文件', '*.xlsx'), ('CSV文件', '*.csv')],
        )
        if not file_path:
            return
        batch_df, details_df = case_database.export_estimate_batch(batch_id)
        if file_path.lower().endswith('.csv'):
            base_path, _ = os.path.splitext(file_path)
            summary_csv = f'{base_path}_估算汇总.csv'
            details_csv = f'{base_path}_相似案例明细.csv'
            batch_df.to_csv(summary_csv, index=False, encoding='utf-8-sig')
            details_df.to_csv(details_csv, index=False, encoding='utf-8-sig')
            messagebox.showinfo('成功', f'估算记录已导出为 CSV:\n{summary_csv}\n{details_csv}')
            return

        with pd.ExcelWriter(file_path) as writer:
            batch_df.to_excel(writer, sheet_name='估算汇总', index=False)
            details_df.to_excel(writer, sheet_name='相似案例明细', index=False)
        messagebox.showinfo('成功', '估算记录已导出为 Excel')

    def delete_selected_batches():
        selected = batch_tree.selection()
        if not selected:
            messagebox.showwarning('提示', '请先选择要删除的估算批次')
            return
        if not messagebox.askyesno('确认', '确定删除选中的估算批次吗？'):
            return
        batch_ids = [batch_tree.item(item, 'values')[0] for item in selected]
        case_database.delete_estimate_batches(batch_ids)
        refresh_batch_list()
        messagebox.showinfo('成功', '选中估算批次已删除')

    def clear_all_records():
        if not messagebox.askyesno('确认', '确定清空全部估算记录吗？该操作不可撤销。'):
            return
        case_database.clear_estimate_records()
        refresh_batch_list()
        messagebox.showinfo('成功', '估算记录已清空')

    ttk.Button(top_bar, text='查询', command=refresh_batch_list).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_bar, text='导出', command=export_records).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_bar, text='删除选中批次', command=delete_selected_batches).pack(side=tk.LEFT, padx=5)
    ttk.Button(top_bar, text='清空估算记录', command=clear_all_records).pack(side=tk.LEFT, padx=5)
    batch_tree.bind('<<TreeviewSelect>>', handle_batch_select)
    refresh_batch_list()
