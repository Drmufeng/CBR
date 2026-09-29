# CBR 新能源汽车 LCC 估算系统

<p align="center"><img src="docs/assets/retro-anime-banner.svg" alt="复古二次元风格装饰" width="760"></p>

这是一个用案例推理估算新能源汽车生命周期成本的桌面工具。它把案例导入、参数清洗、相似案例检索、LCC 估算和验证记录放在同一个流程里，并支持把结果导出为 Excel 或 CSV。

项目使用 SQLite 管理案例库，提供 `manhattan`、`cosine` 和 `experimental_hybrid` 三种相似度算法，并通过留一法统计 MAPE、RMSE 和误差分布。
## 功能概览

- CSV 案例导入与参数清洗
- `manhattan` / `cosine` / `experimental_hybrid` 三种算法估算
- LCC 分项结果展示（购置、使用、回收）
- 留一法模型验证与误差统计（MAPE、RMSE、误差分布）
- SQLite 案例库管理（增删改查、导入导出）
- 验证记录与估算记录留痕（可导出 Excel/CSV）

## 环境要求

- Python 3.11+
- Windows（当前提供了 `launcher/launch.bat` 启动脚本）

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

也可以直接双击 `launcher/launch.bat` 启动。

## 项目结构

```text
delivery/
  src/                # 主程序与核心模块
  data/               # 示例数据
  docs/               # 项目说明文档
  launcher/           # 启动脚本
  packaging/          # PyInstaller 打包配置
```

## 数据说明

示例数据位于 `data/data_sample.csv`，标准列为：

`车型, 长, 宽, 高, 轴距, 最大功率, 最大扭矩, 续航里程, 电池类型, 快充时间, 价格, LCC（10年）`

## 说明

- `src/fetcher.py` 目前为采集接口预留，尚未实现稳定网页抓取。
- 本仓库为源码仓库，不包含虚拟环境、打包中间产物和发布 exe。
