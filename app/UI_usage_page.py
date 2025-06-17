import tkinter as tk
import customtkinter as ctk
from tkcalendar import Calendar
from datetime import date, datetime
from tkinter import messagebox
from app.services import usage_record_service
from app.repositories.sneaker_repository import SneakerRepository
from app.database import get_db
import os
from PIL import Image, ImageTk

class UsagePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d")  # 深色背景

        self.selected_date = None

        # ——— 网格布局：0行 放标题，1行 放 日历+详情（60%），2行 放 统计卡片（40%） ———
        self.grid_rowconfigure(0, weight=0)  # 标题
        self.grid_rowconfigure(1, weight=6)  # 主区
        self.grid_rowconfigure(2, weight=4)  # 统计卡
        self.grid_columnconfigure((0, 1), weight=1)

        # ====== 第一行：页面标题 ======
        title = ctk.CTkLabel(
            self,
            text="球鞋使用",
            font=("微软雅黑", 20, "bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 5))

        # ====== 第二行左：日历区域 ======
        cal_frame = ctk.CTkFrame(self, fg_color="transparent")
        cal_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        cal_frame.grid_rowconfigure(1, weight=1)
        cal_frame.grid_columnconfigure(0, weight=1)

        # 日历控件
        today = date.today()
        self.calendar = Calendar(
            cal_frame,
            selectmode='day',
            year=today.year, month=today.month, day=today.day,
            todaybackground='lightgreen',
            todayforeground='black',
            date_pattern='yyyy-mm-dd',
            background='#f5f7fa',
            disabledbackground='#e0e0e0',
            bordercolor='#d0d7de',
            headersbackground='#dbe9f4',
            headersforeground='#000000',
            foreground='#000000',
            normalbackground='#ffffff',
            weekendbackground='#f0f4f8',
            selectbackground='#4caf50',
            selectforeground='#ffffff',
            font=('Microsoft YaHei', 10),
            borderwidth=2
        )
        self.calendar.grid(row=1, column=0, padx=10, pady=(30,10), sticky="nsew")
        self.calendar.bind("<<CalendarSelected>>", self.on_date_selected)

        # —— 内嵌“今天”按钮在日历右上 ——
        go_today_btn = ctk.CTkButton(
            self.calendar,
            text="今天",
            width=60, height=24,
            corner_radius=8,
            fg_color="#3e3e5b",
            hover_color="#4c4c70",
            text_color="white",
            command=self._go_to_today
        )
        # place 到 calendar 这个 canvas 内：
        go_today_btn.place(relx=0.48, y=2, anchor="n")

        # 标记有记录的日期
        self._refresh_used_dates()

        # ====== 第二行右：详情日志 ======
        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        detail_frame.grid_rowconfigure(1, weight=1)

        # 操作按钮
        op_frame = ctk.CTkFrame(detail_frame, fg_color="transparent")
        op_frame.grid(row=0, column=0, sticky="e", pady=(0,5), padx=5)
        self.add_button = ctk.CTkButton(op_frame, text="添加/修改记录", command=self.open_add_record_dialog)
        self.add_button.pack(side="left", padx=5)
        self.delete_button = ctk.CTkButton(op_frame, text="删除记录", command=self.delete_records)
        self.delete_button.pack(side="left", padx=5)

        # 日志显示
        self.details_label = ctk.CTkLabel(
            detail_frame,
            text="请选择日期查看穿鞋记录",
            justify="left",
            anchor="nw",
            text_color="white"
        )
        self.details_label.grid(row=1, column=0, sticky="nsew")

        # ====== 第三行：统计卡片 ======
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        stats_frame.grid_columnconfigure((0,1,2), weight=1)

        # 获取三个统计
        m1 = usage_record_service.get_monthly_most_frequent()
        m2 = usage_record_service.get_monthly_longest_duration()
        m3 = usage_record_service.get_all_time_most_frequent()

        def build_card(parent, title, stat):
            card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#2d2d44")
            ctk.CTkLabel(card, text=title, font=("微软雅黑",14,"bold")).pack(pady=(10,5))
            # 图片
            img_lbl = None
            if stat and stat["sneaker"].image_path:
                img_path = stat["sneaker"].image_path.split(";")[0]
                if os.path.exists(img_path):
                    pil = Image.open(img_path).resize((100,100))
                    img = ImageTk.PhotoImage(pil)
                    img_lbl = tk.Label(card, image=img, bg="#2d2d44")
                    img_lbl.image = img
                    img_lbl.pack()
            if not img_lbl:
                ctk.CTkLabel(card, text="无图片", text_color="white").pack(pady=20)
            # 文字信息
            if stat:
                snk = stat["sneaker"]
                days = self._calc_days(snk.purchase_date)
                for text in (snk.name, snk.brand, f"已拥有 {days} 天"):
                    ctk.CTkLabel(card, text=text, font=("微软雅黑",12), text_color="white").pack(pady=2)
            return card

        build_card(stats_frame, "近 30 天最常穿", m1).grid(row=0, column=0, sticky="nsew", padx=5)
        build_card(stats_frame, "近 30 天最长时长", m2).grid(row=0, column=1, sticky="nsew", padx=5)
        build_card(stats_frame, "历史穿着最多", m3).grid(row=0, column=2, sticky="nsew", padx=5)

    def get_used_dates(self):
        data = usage_record_service.get_daily_usage_records()
        return [datetime.strptime(d["date"], "%Y-%m-%d").date() for d in data]

    def on_date_selected(self, event):
        sel = self.calendar.get_date()
        self.selected_date = sel
        # 重新标记“今天”和已用日期
        self._refresh_used_dates()  # 先恢复绿色标记
        self.calendar.tag_config('today', background='lightyellow')
        # 刷新日志区
        self.show_records_for_date(sel)

    def show_records_for_date(self, date_str):
        records = usage_record_service.get_usage_records_by_date(date_str)
        if not records:
            self.details_label.configure(text=f"{date_str} 没有穿鞋记录。")
        else:
            lines = []
            for r in records:
                lines.append(
                    f"✔ {r['sneaker']}（{r['activity']}）\n"
                    f"   地点：{r['location'] or '未记录'}\n"
                    f"   时长: {r['duration']}分钟\n"
                    f"   备注：{r['notes'] or ' '}"
                )
            self.details_label.configure(text=f"{date_str} 穿鞋记录：\n\n" + "\n\n".join(lines))

    def open_add_record_dialog(self):
        if not self.selected_date:
            messagebox.showinfo("提示", "请先选择日期。")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"编辑记录 - {self.selected_date}")
        dialog.geometry("550x600")
        dialog.grab_set()

        with get_db() as db:
            sneakers = SneakerRepository.get_all(db)

        existing_records = usage_record_service.get_usage_records_by_date(self.selected_date)

        container = ctk.CTkFrame(dialog)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        entries = []

        def add_entry(existing=None):
            frame = ctk.CTkFrame(scrollable_frame)
            frame.pack(pady=5, fill='x')

            sneaker_var = tk.StringVar()
            sneaker_menu = ctk.CTkOptionMenu(frame, values=[s.name for s in sneakers], variable=sneaker_var)
            sneaker_menu.grid(row=0, column=0, padx=5)

            activity_var = tk.StringVar(value="穿着通勤")
            activity_menu = ctk.CTkOptionMenu(frame,
                                              values=["购入", "穿着打球", "穿着通勤", "穿着休闲", "穿着旅游", "损坏",
                                                      "送修复", "挂卖", "卖出"],
                                              variable=activity_var)
            activity_menu.grid(row=0, column=1, padx=5)

            location_entry = ctk.CTkEntry(frame, placeholder_text="地点")
            location_entry.grid(row=1, column=0, padx=5, pady=5)

            duration_entry = ctk.CTkEntry(frame, placeholder_text="时长（分钟）")
            duration_entry.grid(row=1, column=1, padx=5, pady=5)

            notes_entry = ctk.CTkTextbox(frame, height=60)
            notes_entry.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

            if existing:
                sneaker_var.set(existing['sneaker'])
                activity_var.set(existing['activity'])
                location_entry.insert(0, existing['location'])
                duration_entry.insert(0, str(existing['duration']))
                notes_entry.insert("1.0", existing['notes'])

            entries.append({
                "sneaker_var": sneaker_var,
                "activity_var": activity_var,
                "location_entry": location_entry,
                "duration_entry": duration_entry,
                "notes_entry": notes_entry
            })

        for record in existing_records:
            add_entry(record)

        if not existing_records:
            add_entry()

        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=10)

        def save_all():
            records = []
            for entry in entries:
                name = entry["sneaker_var"].get()
                sneaker = next((s for s in sneakers if s.name == name), None)
                if sneaker:
                    record = {
                        "sneaker_id": sneaker.id,
                        "date": self.selected_date,
                        "activity": entry["activity_var"].get(),
                        "location": entry["location_entry"].get(),
                        "duration": entry["duration_entry"].get(),
                        "notes": entry["notes_entry"].get("1.0", "end").strip()[:2000]
                    }
                    records.append(record)

            usage_record_service.delete_records_by_date(self.selected_date)
            usage_record_service.add_usage_records(records)
            messagebox.showinfo("成功", f"已保存{len(records)}条记录。")
            dialog.destroy()

            self.used_dates = self.get_used_dates()
            self.calendar.calevent_remove('all')
            for d in self.used_dates:
                self.calendar.calevent_create(d, '使用记录', 'used')
            self.calendar.tag_config('used', background='lightgreen', foreground='black')

            self.show_records_for_date(self.selected_date)

        ctk.CTkButton(button_frame, text="添加一双鞋", command=lambda: add_entry()).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="保存全部记录", command=save_all).pack(side="left", padx=10)

    def delete_records(self):
        if not self.selected_date:
            messagebox.showinfo("提示", "请先选择日期。")
            return

        confirm = messagebox.askyesno("确认删除", f"确定要删除 {self.selected_date} 的所有记录吗？")
        if not confirm:
            return

        deleted = usage_record_service.delete_records_by_date(self.selected_date)
        if deleted:
            messagebox.showinfo("成功", f"已删除 {self.selected_date} 的所有记录。")
        else:
            messagebox.showinfo("提示", f"{self.selected_date} 本来就没有记录。")

        self.used_dates = self.get_used_dates()
        self.calendar.calevent_remove('all')
        for d in self.used_dates:
            self.calendar.calevent_create(d, '使用记录', 'used')
        self.calendar.tag_config('used', background='lightgreen', foreground='black')

        self.show_records_for_date(self.selected_date)

    def _refresh_used_dates(self):
        """标记有记录的日期"""
        self.calendar.calevent_remove('all')
        data = usage_record_service.get_daily_usage_records()
        for d in data:
            dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
            self.calendar.calevent_create(dt, 'used', 'used')
        self.calendar.tag_config('used', background='lightgreen', foreground='black')

    def _go_to_today(self):
        """把选中的日期跳回今天并刷新记录"""
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        # ① 把 Calendar 的选中日期设为“今天”
        self.calendar.selection_set(today)
        # ② 保存到 self.selected_date
        self.selected_date = today
        # ③ 刷新详情面板
        self.show_records_for_date(today)

    def _calc_days(self, purchase_date_str):
        try:
            pd = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
            return (date.today() - pd).days
        except:
            return "-"