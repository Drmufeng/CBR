"""界面复用组件。"""

import tkinter as tk
from tkinter import ttk

import numpy as np


class WheelEntry(ttk.Entry):
    """支持鼠标滚轮调整数值的输入框。"""

    def __init__(self, master=None, **kwargs):
        self.step = kwargs.pop('step', 1.0)
        self.min_val = kwargs.pop('min_val', -np.inf)
        self.max_val = kwargs.pop('max_val', np.inf)
        self.is_int = kwargs.pop('is_int', False)
        super().__init__(master, **kwargs)

        self.bind("<MouseWheel>", self.on_mousewheel)
        self.bind("<Button-4>", self.on_mousewheel)
        self.bind("<Button-5>", self.on_mousewheel)

    def on_mousewheel(self, event):
        """根据滚轮方向与按键状态调整当前值。"""
        try:
            current = float(self.get())
        except ValueError:
            return

        delta = self.step
        if event.delta < 0 or getattr(event, 'num', None) == 5:
            delta = -delta

        if event.state & 0x0001:
            delta *= 10
        elif event.state & 0x0004:
            delta *= 0.1

        new_val = current + delta
        new_val = max(self.min_val, min(new_val, self.max_val))
        if self.is_int:
            new_val = int(round(new_val))

        self.delete(0, tk.END)
        self.insert(0, f"{new_val:.0f}" if self.is_int else f"{new_val:.1f}")
