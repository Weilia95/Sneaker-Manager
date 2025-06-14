import tkinter as tk
import customtkinter as ctk
from tkcalendar import Calendar
from datetime import date, datetime
from tkinter import messagebox
from app.services import usage_record_service
from app.repositories.sneaker_repository import SneakerRepository
from app.database import get_db

class UsagePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d")

        # ── 第一行：标题栏 ───────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="球鞋使用",
            font=("微软雅黑", 20, "bold"),
            text_color="white"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # ── 从这里开始，把原本的 grid row 全部下移 1 ─────────────
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.used_dates = self.get_used_dates()
        self.selected_date = None

        today = date.today()
        self.calendar = Calendar(
            self,
            selectmode='day',
            year=today.year,
            month=today.month,
            day=today.day,
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
        self.calendar.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        for d in self.used_dates:
            self.calendar.calevent_create(d, '使用记录', 'used')
        self.calendar.tag_config('used', background='lightgreen', foreground='black')

        self.calendar.bind("<<CalendarSelected>>", self.on_date_selected)

        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)

        button_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="e", padx=10, pady=5)

        self.add_button = ctk.CTkButton(button_frame, text="添加/修改记录", fg_color="#3e3e5b", hover_color="#4c4c70", text_color="white", command=self.open_add_record_dialog)
        self.add_button.pack(side="left", padx=5)

        self.delete_button = ctk.CTkButton(button_frame, text="删除记录", fg_color="#3e3e5b", hover_color="#4c4c70", text_color="white", command=self.delete_records)
        self.delete_button.pack(side="left", padx=5)

        self.details_label = ctk.CTkLabel(right_frame, text="请选择日期查看穿鞋记录", justify="left", anchor="nw", text_color="white", font=("微软雅黑", 14))
        self.details_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    # 下面的逻辑无需改动，之前写得很好

    def get_used_dates(self):
        data = usage_record_service.get_daily_usage_records()
        return [datetime.strptime(d["date"], "%Y-%m-%d").date() for d in data]

    def on_date_selected(self, event):
        selected_date = self.calendar.get_date()
        self.selected_date = selected_date
        self.show_records_for_date(selected_date)

    def show_records_for_date(self, date_str):
        records = usage_record_service.get_usage_records_by_date(date_str)

        if not records:
            text = f"{date_str} 没有穿鞋记录。"
        else:
            lines = []
            for r in records:
                line = (
                    f"✔ {r['sneaker']}（{r['activity']}）\n"
                    f"地点：{r['location'] or '无'}\n"
                    f"时长：{r['duration']} 分钟\n"
                    f"备注：{r['notes'] or '无'}\n"
                    f"-------------------------"
                )
                lines.append(line)
            text = f"{date_str} 穿鞋记录：\n\n" + "\n".join(lines)

        self.details_label.configure(text=text)

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
