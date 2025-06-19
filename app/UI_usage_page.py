# UI_usage_page.py

import os
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from tkcalendar import Calendar
from datetime import date, datetime, timedelta
from PIL import Image, ImageTk

from app.services import usage_record_service
from app.repositories.sneaker_repository import SneakerRepository
from app.database import get_db


class UsagePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d")  # 深色背景

        # Grid: row0=title, row1=calendar+details (60%), row2=stats cards (40%)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=6)
        self.grid_rowconfigure(2, weight=4)
        self.grid_columnconfigure((0, 1), weight=1)

        # ——— 第一行：页面标题 ———
        title = ctk.CTkLabel(
            self,
            text="球鞋使用",
            font=("微软雅黑", 20, "bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 5))

        # ——— 第二行左：日历区域 ———
        cal_frame = ctk.CTkFrame(self, fg_color="transparent")
        cal_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        cal_frame.grid_rowconfigure(0, weight=0)
        cal_frame.grid_rowconfigure(1, weight=1)
        cal_frame.grid_columnconfigure(0, weight=1)

        today = date.today()
        self.calendar = Calendar(
            cal_frame,
            selectmode='day',
            year=today.year, month=today.month, day=today.day,
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
        # push weekday header down a bit
        self.calendar.grid(row=1, column=0, padx=10, pady=(30, 5), sticky="nsew")
        self.calendar.bind("<<CalendarSelected>>", self.on_date_selected)

        # 内嵌“今天”按钮
        go_today = ctk.CTkButton(
            cal_frame,
            text="今天",
            width=60, height=24,
            corner_radius=8,
            fg_color="#3e3e5b",
            hover_color="#4c4c70",
            text_color="white",
            command=self._go_today
        )
        go_today.place(in_=self.calendar, relx=0.493, y=1)  # 贴到日历右上

        # 标记有记录的日期
        self._mark_used_dates()

        # ——— 第二行右：详情 & 操作按钮 ———
        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        detail_frame.grid_rowconfigure(1, weight=1)
        detail_frame.grid_columnconfigure(0, weight=1)

        btn_bar = ctk.CTkFrame(detail_frame, fg_color="transparent")
        btn_bar.grid(row=0, column=0, sticky="e", pady=(0,5))
        ctk.CTkButton(btn_bar, text="添加/修改记录", command=self.open_add_record_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_bar, text="删除记录", command=self.delete_records).pack(side="left", padx=5)

        # 使用可滚动区域来显示记录
        self.details_area = ctk.CTkScrollableFrame(detail_frame, fg_color="transparent")
        self.details_area.grid(row=1, column=0, sticky="nsew")

        # ——— 第三行：统计卡片 ———
        stats_container = ctk.CTkFrame(self, fg_color="transparent")
        stats_container.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        stats_container.grid_columnconfigure((0,1,2), weight=1)

        self.stat_cards = []
        colors = ["#9AA5FC", "#4CCEAC", "#FFB476"]
        titles = ["近30天最常穿", "近30天最长时长", "历史累计最多"]
        funcs = [
            usage_record_service.get_monthly_most_frequent,
            usage_record_service.get_monthly_longest_duration,
            usage_record_service.get_all_time_most_frequent
        ]

        for i in range(3):
            card = ctk.CTkFrame(stats_container, fg_color=colors[i], corner_radius=10)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            self.stat_cards.append((card, titles[i], funcs[i]))

        # render stats
        self._render_stats_cards()

    def _mark_used_dates(self):
        used = usage_record_service.get_daily_usage_records()
        for d in used:
            dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
            self.calendar.calevent_create(dt, '使用记录', 'used')
        self.calendar.tag_config('used', background='lightgreen', foreground='black')

    def _go_today(self):
        """跳到今天并高亮"""
        today = date.today().strftime("%Y-%m-%d")
        self.calendar.selection_set(today)
        self.on_date_selected(None)

    def on_date_selected(self, event):
        sel = self.calendar.get_date()
        self.selected_date = sel
        self.show_records_for_date(sel)

    def show_records_for_date(self, date_str):
        """在右侧详情区渲染文字 + 照片（可左右切换）"""
        # 先清空
        for w in self.details_area.winfo_children():
            w.destroy()

        records = usage_record_service.get_usage_records_by_date(date_str)
        if not records:
            ctk.CTkLabel(self.details_area, text=f"{date_str} 没有穿鞋记录。", text_color="white").pack(pady=10)
            return

        for rec in records:
            card = ctk.CTkFrame(self.details_area, fg_color="#2d2d44", corner_radius=8)
            card.pack(fill="x", pady=5, padx=5)

            # 文本部分
            txt = (
                f"✔ {rec['sneaker']}（{rec['activity']}）\n"
                f"地点：{rec.get('location') or '无'}    时长：{rec.get('duration') or 0} 分钟\n"
                f"备注：{rec.get('notes') or '无'}"
            )
            ctk.CTkLabel(card, text=txt, text_color="white", justify="left").pack(anchor="w", padx=10, pady=(5,0))

            # 照片部分
            imgs = rec.get("image_paths", [])
            if imgs:
                # 用 lbl.idx 存当前索引
                img_frame = ctk.CTkFrame(card, fg_color="transparent")
                img_frame.pack(pady=5)
                lbl = tk.Label(img_frame, bg="#2d2d44")
                lbl.idx = 0
                lbl.pack()

                def render_image(lbl, paths):
                    idx = lbl.idx
                    try:
                        pil = Image.open(paths[idx]).resize((200, 200))
                        photo = ImageTk.PhotoImage(pil)
                        lbl.configure(image=photo, text="")
                        lbl.image = photo
                    except Exception:
                        lbl.configure(text="图片加载失败", fg="white")

                # 初始渲染
                render_image(lbl, imgs)

                if len(imgs) > 1:
                    btns = ctk.CTkFrame(card, fg_color="transparent")
                    btns.pack(pady=(0,10))
                    # 上一张
                    ctk.CTkButton(
                        btns, text="〈", width=30, height=30,
                        command=lambda lbl=lbl, paths=imgs, fn=-1: self._change_image(lbl, paths, fn)
                    ).pack(side="left", padx=5)
                    # 下一张
                    ctk.CTkButton(
                        btns, text="〉", width=30, height=30,
                        command=lambda lbl=lbl, paths=imgs, fn=+1: self._change_image(lbl, paths, fn)
                    ).pack(side="left", padx=5)

    def _change_image(self, lbl, paths, direction):
        """统一的上一张／下一张切换"""
        lbl.idx = (lbl.idx + direction) % len(paths)
        try:
            pil = Image.open(paths[lbl.idx]).resize((200, 200))
            photo = ImageTk.PhotoImage(pil)
            lbl.configure(image=photo, text="")
            lbl.image = photo
        except Exception:
            lbl.configure(text="图片加载失败", fg="white")

    def open_add_record_dialog(self):
        if not hasattr(self, 'selected_date') or not self.selected_date:
            messagebox.showinfo("提示", "请先选择日期。")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"编辑记录 - {self.selected_date}")
        dialog.geometry("600x600")
        dialog.grab_set()

        with get_db() as db:
            sneakers = SneakerRepository.get_all(db)

        existing = usage_record_service.get_usage_records_by_date(self.selected_date)

        # 滚动容器
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, bg="#f5f7fa", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = ctk.CTkFrame(canvas, fg_color="transparent")
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        entries = []

        def add_entry(rec=None):
            frame = ctk.CTkFrame(scrollable, fg_color="#2d2d44", corner_radius=8)
            frame.pack(fill="x", pady=5, padx=5)

            v_sneaker = tk.StringVar()
            ctk.CTkOptionMenu(frame, values=[s.name for s in sneakers], variable=v_sneaker, width=120) \
                .grid(row=0, column=0, padx=5, pady=5)
            v_act = tk.StringVar(value="穿着通勤")
            ctk.CTkOptionMenu(
                frame,
                values=["购入", "穿着打球", "穿着通勤", "穿着休闲",
                        "穿着旅游", "损坏", "送修复", "挂卖", "卖出"],
                variable=v_act,
                width=100
            ).grid(row=0, column=1, padx=5, pady=5)

            ent_loc = ctk.CTkEntry(frame, placeholder_text="地点", width=100)
            ent_loc.grid(row=1, column=0, padx=5, pady=5)
            ent_dur = ctk.CTkEntry(frame, placeholder_text="时长(分钟)", width=100)
            ent_dur.grid(row=1, column=1, padx=5, pady=5)

            txt_notes = ctk.CTkTextbox(frame, height=60)
            txt_notes.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

            # 多张照片支持
            image_paths = rec.get("image_paths", [])[:] if rec else []
            def upload_photos():
                paths = filedialog.askopenfilenames(
                    title="选择照片",
                    filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
                )
                if paths:
                    image_paths.clear()
                    image_paths.extend(paths)

            ctk.CTkButton(frame, text="上传照片", command=upload_photos)\
                .grid(row=0, column=2, rowspan=2, padx=5, pady=5)

            if rec:
                v_sneaker.set(rec["sneaker"])
                v_act.set(rec["activity"])
                ent_loc.insert(0, rec.get("location", ""))
                ent_dur.insert(0, str(rec.get("duration", "")))
                txt_notes.insert("1.0", rec.get("notes", ""))

            entries.append({
                "sneaker_var": v_sneaker,
                "activity_var": v_act,
                "location_entry": ent_loc,
                "duration_entry": ent_dur,
                "notes_entry": txt_notes,
                "image_paths": image_paths
            })

        # 先加载已有，再加一条空的
        for r in existing:
            add_entry(r)
        if not existing:
            add_entry()

        btn_bar = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_bar.pack(pady=10)
        ctk.CTkButton(btn_bar, text="添加一条", command=add_entry).pack(side="left", padx=10)

        def save_all():
            usage_record_service.delete_records_by_date(self.selected_date)
            recs = []
            for e in entries:
                name = e["sneaker_var"].get()
                sk = next((s for s in sneakers if s.name == name), None)
                if not sk:
                    continue
                recs.append({
                    "sneaker_id": sk.id,
                    "date": self.selected_date,
                    "activity": e["activity_var"].get(),
                    "location": e["location_entry"].get(),
                    "duration": int(e["duration_entry"].get() or 0),
                    "notes": e["notes_entry"].get("1.0", "end").strip(),
                    "image_paths": e["image_paths"]
                })
            usage_record_service.add_usage_records(recs)
            messagebox.showinfo("成功", f"已保存 {len(recs)} 条记录。")
            dialog.destroy()
            self._mark_used_dates()
            self.on_date_selected(None)

        ctk.CTkButton(btn_bar, text="保存全部", command=save_all).pack(side="left", padx=10)

    def delete_records(self):
        if not self.selected_date:
            messagebox.showinfo("提示", "请先选择日期。")
            return
        if messagebox.askyesno("确认删除", f"确定要删除 {self.selected_date} 的所有记录吗？"):
            if usage_record_service.delete_records_by_date(self.selected_date):
                messagebox.showinfo("成功", "已删除该日所有记录。")
                self._mark_used_dates()
                self.on_date_selected(None)
            else:
                messagebox.showinfo("提示", "当日无记录可删。")

    def _render_stats_cards(self):
        """渲染底部三个统计卡片"""
        for card, title, func in self.stat_cards:
            for w in card.winfo_children():
                w.destroy()

            result = func()
            ctk.CTkLabel(card, text=title, font=("微软雅黑", 14, "bold"), text_color="white")\
                .pack(pady=(10,5))

            if not result:
                ctk.CTkLabel(card, text="暂无数据", text_color="white").pack(pady=20)
                continue

            snk = result["sneaker"]
            # 显示第一张鞋图
            paths = (snk.image_path or "").split(";")
            if paths and os.path.exists(paths[0]):
                try:
                    img = Image.open(paths[0]).resize((100, 80))
                    photo = ImageTk.PhotoImage(img)
                    lbl = tk.Label(card, image=photo, bg=card.cget("fg_color"))
                    lbl.image = photo
                    lbl.pack(pady=5)
                except:
                    pass

            # 名称、品牌、已拥有
            days = "-"
            try:
                pd = datetime.strptime(snk.purchase_date, "%Y-%m-%d").date()
                days = (date.today() - pd).days
            except:
                pass

            ctk.CTkLabel(card, text=f"{snk.name}", font=("微软雅黑", 12, "bold"), text_color="white")\
                .pack(pady=(5,0))
            ctk.CTkLabel(card, text=f"{snk.brand} | 已拥有 {days} 天", text_color="white")\
                .pack(pady=(0,10))

            # 次数或时长
            val = result.get("value", 0)
            unit = "次" if title != "近30天最长时长" else "分钟"
            ctk.CTkLabel(card, text=f"{val}{unit}", font=("微软雅黑", 12), text_color="white")\
                .pack(pady=(0,10))
