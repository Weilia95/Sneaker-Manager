import tkinter as tk
from tkcalendar import Calendar
from tkinter import ttk
from datetime import date


class CalendarWithUsage(tk.Frame):
    def __init__(self, master=None, used_dates=None, on_date_select=None):
        super().__init__(master)
        self.used_dates = set(used_dates or [])  # 格式为 YYYY-MM-DD 字符串
        self.on_date_select = on_date_select

        self._build_widgets()

    def _build_widgets(self):
        # 日历组件
        self.cal = Calendar(
            self,
            selectmode='day',
            date_pattern='yyyy-mm-dd',
            firstweekday='sunday'
        )
        self.cal.pack(padx=10, pady=10, fill='both', expand=True)

        # 标记已使用日期
        self._mark_used_dates()

        # 绑定点击事件
        self.cal.bind("<<CalendarSelected>>", self._on_date_selected)

        # 详情展示框
        self.detail_label = ttk.Label(self, text="请选择日期查看记录", anchor='center', justify='left')
        self.detail_label.pack(fill='x', padx=10, pady=5)

    def _mark_used_dates(self):
        # 通过为有记录的日期加绿色背景标记
        for d in self.used_dates:
            try:
                self.cal.calevent_create(date.fromisoformat(d), '使用记录', 'used')
            except Exception as e:
                print(f"[错误] 日期标记失败：{d} -> {e}")

        # 设置绿色背景样式
        self.cal.tag_config('used', background='lightgreen', foreground='black')

    def _on_date_selected(self, event):
        selected_date = self.cal.get_date()  # 格式 yyyy-mm-dd
        print(f"[调试] 用户选择日期：{selected_date}")

        if self.on_date_select:
            details = self.on_date_select(selected_date)
            self.detail_label.configure(text=details or "暂无记录")
        else:
            self.detail_label.configure(text=f"你选择了：{selected_date}")

    def update_used_dates(self, new_dates):
        self.used_dates = set(new_dates)
        self.cal.calevent_remove('all')
        self._mark_used_dates()

    def clear_details(self):
        self.detail_label.configure(text="请选择日期查看记录")
