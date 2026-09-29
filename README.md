# CBR 新能源汽车 LCC 估算系统

<p align="center"><img src="docs/assets/retro-anime-banner.svg" alt="新能源汽车生命周期成本估算主题装饰" width="760"></p>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](requirements.txt)
[![Storage](https://img.shields.io/badge/Storage-SQLite-003B57?style=flat-square)](data)
[![License](https://img.shields.io/badge/License-MIT-2D8CFF?style=flat-square)](LICENSE)

</div>

## 项目介绍

这是一个用案例推理估算新能源汽车生命周期成本的桌面工具。用户可以导入车辆案例，清洗参数，检索相似案例，查看购置、使用和回收成本，再把估算结果与验证记录导出。

项目使用 SQLite 保存案例库，提供 manhattan、cosine 和 experimental_hybrid 三种相似度算法。模型验证采用留一法，统计 MAPE、RMSE 和误差分布，便于比较不同参数和算法的结果。

## 估算流程

~~~mermaid
flowchart LR
    A[CSV 案例] --> B[参数清洗]
    B --> C[相似案例检索]
    C --> D[LCC 分项估算]
    D --> E[结果与验证记录]
    E --> F[Excel / CSV]
~~~

## 功能

- 导入 CSV 案例并检查字段、缺失值和数值格式。
- 以 manhattan、cosine 或 experimental_hybrid 检索相似案例。
- 展示购置、使用、维护和回收等 LCC 分项。
- 使用留一法记录 MAPE、RMSE 和误差分布。
- 通过 SQLite 管理案例、估算记录和验证记录。
- 导出 Excel 或 CSV，方便继续分析。

## 数据格式

示例文件位于 data/data_sample.csv，标准列为：

~~~text
车型, 长, 宽, 高, 轴距, 最大功率, 最大扭矩, 续航里程, 电池类型, 快充时间, 价格, LCC（10年）
~~~

## 环境和安装

- Python 3.11+
- Windows（仓库提供 launcher/launch.bat）

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py
~~~

也可以直接双击 launcher/launch.bat。

## 目录

~~~text
delivery/
├── src/          # 主程序、数据库和估算逻辑
├── data/         # 示例案例数据
├── docs/         # 使用说明和设计文档
├── launcher/     # 启动脚本
└── packaging/    # PyInstaller 打包配置
~~~

### 从哪里开始

| 你准备做什么 | 建议入口 |
| --- | --- |
| 第一次运行项目 | 按照安装步骤启动 src/main.py |
| 查看案例字段 | data/data_sample.csv |
| 查看算法和验证 | src/ 与 docs/ |
| 打包桌面程序 | packaging/ |

## 估算记录

案例库、估算记录和验证记录都写入本地 SQLite。导入新数据前建议保留一份数据库备份；导出文件适合用于复核和后续分析。

## 当前边界

- src/fetcher.py 只是采集接口预留，目前没有稳定的网页抓取实现。
- 仓库只保存源码和示例数据，不包含虚拟环境、打包中间产物或发布 exe。
- LCC 结果取决于案例质量、字段单位和输入假设，使用前应先检查数据口径。

## 许可

本项目采用 [MIT License](LICENSE)。示例数据和第三方依赖按各自的许可证使用。
