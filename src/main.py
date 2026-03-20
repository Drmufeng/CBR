"""程序入口。

当前文件仅负责启动图形界面，具体逻辑已拆分到独立模块。
"""

from gui_app import LCCEstimatorApp


def main():
    """启动应用。"""
    app = LCCEstimatorApp()
    app.mainloop()


if __name__ == '__main__':
    main()
