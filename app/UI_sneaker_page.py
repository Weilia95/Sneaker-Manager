# UI_sneaker_page.py 修改后
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from app.repositories.sneaker_repository import SneakerRepository
from app.database import get_db
from PIL import Image, ImageTk
import os
from datetime import datetime


class SneakerMainPage(ctk.CTkFrame):
    def __init__(self, master, sneaker_service, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d")  # 设置深色背景

        self.active_frame = None
        self.sneaker_service = sneaker_service
        self.sneakers = []
        self.selected_image_paths = []
        self.current_image_index = {}
        self.selected_sneaker = None
        self.selected_card = None
        self.filtered_sneakers = []

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 第一行 标题 + 按钮 - 卡片风格
        self.header_frame = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="球鞋主数据",
            font=("微软雅黑", 20, "bold"),
            text_color="white"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # 按钮容器
        button_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # 按钮样式
        button_style = {
            "width": 40,
            "height": 40,
            "corner_radius": 20,
            "fg_color": "#3e3e5b",
            "hover_color": "#4c4c70",
            "text_color": "white"
        }

        self.switch_button = ctk.CTkButton(
            button_frame, text="⇄切换视图", **button_style, command=self.switch_view
        )
        self.switch_button.pack(side="right", padx=5)

        self.delete_button = ctk.CTkButton(
            button_frame, text="🗑删除球鞋", **button_style, command=self.delete_sneaker
        )
        self.delete_button.pack(side="right", padx=5)

        self.edit_button = ctk.CTkButton(
            button_frame, text="✎修改球鞋", **button_style, command=self.edit_sneaker
        )
        self.edit_button.pack(side="right", padx=5)

        self.add_button = ctk.CTkButton(
            button_frame, text="+新增球鞋", **button_style, command=lambda: self.open_sneaker_form()

        )
        self.add_button.pack(side="right", padx=5)

        # 第二行统计信息 - 卡片风格
        self.stats_frame = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # 统计卡片
        stat_style = {
            "font": ("微软雅黑", 14),
            "text_color": "#e0e0e0"
        }

        self.total_label = ctk.CTkLabel(self.stats_frame, text="总球鞋数: 0", **stat_style)
        self.total_label.pack(side="left", padx=20, pady=10)

        self.total_value_label = ctk.CTkLabel(self.stats_frame, text="总价值: 0元", **stat_style)
        self.total_value_label.pack(side="left", padx=20, pady=10)

        self.average_value_label = ctk.CTkLabel(self.stats_frame, text="平均价值: 0元", **stat_style)
        self.average_value_label.pack(side="left", padx=20, pady=10)

        # 第三行 搜索区域 - 卡片风格
        self.search_frame = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        self.search_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        # 搜索框样式
        entry_style = {
            "fg_color": "#3e3e5b",
            "border_width": 0,
            "text_color": "white",
            "placeholder_text_color": "gray"
        }

        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="关键词搜索",
            **entry_style
        )
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.refresh_sneaker_list())

        self.min_price_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="最低价格",
            width=100,
            **entry_style
        )
        self.min_price_entry.pack(side="left", padx=5)
        self.min_price_entry.bind("<Return>", lambda e: self.refresh_sneaker_list())

        self.max_price_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="最高价格",
            width=100,
            **entry_style
        )
        self.max_price_entry.pack(side="left", padx=5)
        self.max_price_entry.bind("<Return>", lambda e: self.refresh_sneaker_list())

        # 按钮样式
        button_style_small = {
            "fg_color": "#3e3e5b",
            "hover_color": "#4c4c70",
            "text_color": "white",
            "height": 34
        }

        self.search_button = ctk.CTkButton(
            self.search_frame,
            text="搜索",
            **button_style_small,
            command=self.refresh_sneaker_list
        )
        self.search_button.pack(side="left", padx=5)

        self.clear_button = ctk.CTkButton(
            self.search_frame,
            text="清除搜索",
            **button_style_small,
            command=self.clear_search
        )
        self.clear_button.pack(side="left", padx=5)

        # 第四行 展示区域
        self.listbox_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_canvas = tk.Canvas(self.listbox_frame, bg="#1e1e2d", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical", command=self.list_canvas.yview)
        self.list_container = ctk.CTkFrame(self.list_canvas, fg_color="transparent")

        self.list_container.bind(
            "<Configure>", lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
        )

        self.list_canvas.create_window((0, 0), window=self.list_container, anchor="nw")
        self.list_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.list_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 鞋墙视图
        self.wall_canvas = tk.Canvas(self, bg="#1e1e2d", highlightthickness=0)
        self.wall_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.wall_canvas.yview)
        self.wall_container = ctk.CTkFrame(self.wall_canvas, fg_color="transparent")

        self.wall_container.bind(
            "<Configure>", lambda e: self.wall_canvas.configure(scrollregion=self.wall_canvas.bbox("all"))
        )

        self.wall_canvas.create_window((0, 0), window=self.wall_container, anchor="nw")
        self.wall_canvas.configure(yscrollcommand=self.wall_scrollbar.set)

        self.wall_background = None
        self.current_view = "list"

        self.refresh_sneaker_list()

    def open_sneaker_form(self, sneaker=None):
        form = ctk.CTkToplevel(self)
        form.title("新增球鞋" if sneaker is None else "修改球鞋")
        form.geometry("400x400")
        form.grab_set()

        fields = ["名称", "品牌", "系列", "购入日期", "购入价格", "尺码", "颜色"]
        entries = {}

        for idx, field in enumerate(fields):
            label = ctk.CTkLabel(form, text=field)
            label.grid(row=idx, column=0, padx=5, pady=5)
            entry = ctk.CTkEntry(form)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            entries[field] = entry

        image_paths = []

        if sneaker:
            entries["名称"].insert(0, sneaker.name)
            entries["品牌"].insert(0, sneaker.brand)
            entries["系列"].insert(0, sneaker.series)
            entries["购入日期"].insert(0, sneaker.purchase_date)
            entries["购入价格"].insert(0, str(sneaker.purchase_price))
            entries["尺码"].insert(0, str(sneaker.size))
            entries["颜色"].insert(0, sneaker.color)
            image_paths = sneaker.image_path.split(';') if sneaker.image_path else []

        def upload_images():
            paths = filedialog.askopenfilenames(title="选择图片", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if paths:
                image_paths.clear()
                image_paths.extend(paths)

        upload_button = ctk.CTkButton(form, text="上传图片", command=upload_images)
        upload_button.grid(row=len(fields), column=0, columnspan=2, pady=5)

        def save():
            with get_db() as db:
                try:
                    if sneaker:
                        # 更新数据库
                        sneaker.name = entries["名称"].get()
                        sneaker.brand = entries["品牌"].get()
                        sneaker.series = entries["系列"].get()
                        sneaker.purchase_date = entries["购入日期"].get()
                        sneaker.purchase_price = float(entries["购入价格"].get())
                        sneaker.size = float(entries["尺码"].get())
                        sneaker.color = entries["颜色"].get()
                        sneaker.image_path = ';'.join(image_paths)

                        # 加入这句：让数据库知道这个对象被更新
                        db.merge(sneaker)
                        db.commit()
                    else:
                        new_sneaker = {
                            "name": entries["名称"].get(),
                            "brand": entries["品牌"].get(),
                            "series": entries["系列"].get(),
                            "purchase_date": entries["购入日期"].get(),
                            "purchase_price": float(entries["购入价格"].get()),
                            "size": float(entries["尺码"].get()),
                            "color": entries["颜色"].get(),
                            "image_path": ';'.join(image_paths)
                        }
                        SneakerRepository.create(db, new_sneaker)
                        db.commit()

                    self.refresh_sneaker_list()
                    messagebox.showinfo("成功", "保存成功！")
                    form.destroy()
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败：{e}")

        save_button = ctk.CTkButton(form, text="保存", command=save)
        save_button.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

    def create_sneaker_card(self, sneaker):
        card = ctk.CTkFrame(
            self.list_container,
            height=170,
            fg_color="#2d2d44",
            corner_radius=10,
            border_width=1,
            border_color="#3e3e5b"
        )
        card.pack(fill="x", padx=10, pady=5)
        card.bind("<Button-1>", lambda e, s=sneaker, c=card: self.select_sneaker(s, c))
        card.bind("<Enter>", lambda e, c=card: c.configure(fg_color="#3e3e5b"))
        card.bind("<Leave>", lambda e, c=card: c.configure(fg_color="#2d2d44"))

        # 图片容器
        img_frame = ctk.CTkFrame(card, fg_color="transparent", width=150)
        img_frame.pack(side="left", padx=10, pady=10)

        images = sneaker.image_path.split(';') if sneaker.image_path else []
        self.current_image_index[sneaker.id] = 0

        if images and os.path.exists(images[0]):
            try:
                image = Image.open(images[0])
                image = image.resize((120, 120))
                photo = ImageTk.PhotoImage(image)
                img_label = tk.Label(img_frame, image=photo, bg="#2d2d44")
                img_label.image = photo
                img_label.pack()

                if len(images) > 1:
                    next_button = ctk.CTkButton(
                        img_frame, text=">", width=30, height=30, corner_radius=15,
                        fg_color="#3e3e5b", hover_color="#4c4c70", text_color="white",
                        command=lambda s=sneaker, l=img_label: self.show_next_image(s, l)
                    )
                    next_button.pack(pady=5)
            except Exception as e:
                print(f"Error loading image: {e}")
                img_label = tk.Label(img_frame, text="图片加载失败", width=15, height=7, bg="#2d2d44", fg="white")
                img_label.pack()
        else:
            img_label = tk.Label(img_frame, text="无图片", width=15, height=7, bg="#2d2d44", fg="white")
            img_label.pack()

        # 信息区域 - 两列显示
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        days_owned = self.calculate_days(sneaker.purchase_date)

        # 名称行
        name_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            name_frame,
            text=sneaker.name,
            font=("微软雅黑", 16, "bold"),
            text_color="#f0f0f0"
        ).pack(side="left")

        ctk.CTkLabel(
            name_frame,
            text=f"¥{sneaker.purchase_price}",
            font=("微软雅黑", 14),
            text_color="#FFD700"  # 金色显示价格
        ).pack(side="right", padx=10)

        # 信息两列排布
        details = [
            f"品牌: {sneaker.brand}",
            f"系列: {sneaker.series}",
            f"尺码: {sneaker.size}",
            f"颜色: {sneaker.color}",
            f"已拥有: {days_owned}天",
            f"状态: {sneaker.status}"
        ]

        left_column = ctk.CTkFrame(info_frame, fg_color="transparent")
        left_column.pack(side="left", padx=10, fill="y")

        right_column = ctk.CTkFrame(info_frame, fg_color="transparent")
        right_column.pack(side="left", padx=10, fill="y")

        # 拆分到左右列
        for idx, detail in enumerate(details):
            target = left_column if idx % 2 == 0 else right_column
            ctk.CTkLabel(
                target,
                text=detail,
                font=("微软雅黑", 12),
                text_color="#c0c0c0"
            ).pack(anchor="w", pady=2)

    def edit_sneaker(self):
        if self.selected_sneaker:
            self.open_sneaker_form(self.selected_sneaker)
        else:
            messagebox.showwarning("警告", "请先选中一双球鞋")

    def switch_view(self):
        if self.current_view == "list":
            self.current_view = "wall"
            self.show_wall_view()
        else:
            self.current_view = "list"
            self.show_list_view()

    def show_list_view(self):
        if self.active_frame:
            self.active_frame.grid_forget()

        self.listbox_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.active_frame = self.listbox_frame

    def show_wall_view(self):
        if self.active_frame:
            self.active_frame.grid_forget()

        self.wall_canvas.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.wall_scrollbar.grid(row=3, column=0, sticky="nse")
        self.active_frame = self.wall_canvas
        self.render_wall_view()

    def render_wall_view(self):
        for widget in self.wall_container.winfo_children():
            widget.destroy()

        self.wall_container.grid_columnconfigure(0, weight=1)

        if self.wall_background is None:
            try:
                bg_image = Image.new("RGB", (1200, 800), "#1e1e2d")
                self.wall_background = ImageTk.PhotoImage(bg_image)
                self.wall_canvas.create_image(0, 0, image=self.wall_background, anchor="nw")
            except:
                pass

        grid_frame = ctk.CTkFrame(self.wall_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=20)

        columns = 4
        row = 0
        col = 0

        for idx, sneaker in enumerate(self.filtered_sneakers):
            if col == 0:
                row_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
                row_frame.grid(row=row, column=0, sticky="ew", pady=5)
                row += 1

            card = ctk.CTkFrame(
                row_frame,
                width=260,
                height=300,
                fg_color="#2d2d44",
                corner_radius=10,
                border_width=1,
                border_color="#3e3e5b"
            )
            card.grid(row=0, column=col, padx=10, pady=5)
            card.grid_propagate(False)

            card.bind("<Enter>", lambda e, c=card: c.configure(fg_color="#3e3e5b"))
            card.bind("<Leave>", lambda e, c=card: c.configure(fg_color="#2d2d44"))
            card.bind("<Button-1>", lambda e, s=sneaker, c=card: self.select_sneaker(s, c))

            img_frame = ctk.CTkFrame(card, fg_color="transparent", height=180)
            img_frame.pack(fill="x", padx=10, pady=(15, 5))

            if sneaker.image_path:
                image_paths = sneaker.image_path.split(';')
                if image_paths and os.path.exists(image_paths[0]):
                    try:
                        image = Image.open(image_paths[0])
                        image = image.resize((220, 150))
                        photo = ImageTk.PhotoImage(image)
                        img_label = tk.Label(img_frame, image=photo, bg="#2d2d44")
                        img_label.image = photo
                        img_label.pack()
                    except Exception as e:
                        print(f"Error loading image: {e}")
                        tk.Label(img_frame, text="图片加载失败", bg="#2d2d44", fg="white").pack()
                else:
                    tk.Label(img_frame, text="无图片", bg="#2d2d44", fg="white").pack()
            else:
                tk.Label(img_frame, text="无图片", bg="#2d2d44", fg="white").pack()

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(fill="both", expand=True, padx=10, pady=(0, 15))

            name_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            name_frame.pack(fill="x", pady=(0, 5))

            ctk.CTkLabel(
                name_frame,
                text=sneaker.name,
                font=("微软雅黑", 14, "bold"),
                text_color="#f0f0f0"
            ).pack(side="left")

            ctk.CTkLabel(
                name_frame,
                text=f"¥{sneaker.purchase_price}",
                font=("微软雅黑", 13),
                text_color="#FFD700"
            ).pack(side="right")

            ctk.CTkLabel(
                info_frame,
                text=f"{sneaker.brand} | {sneaker.color}",
                font=("微软雅黑", 12),
                text_color="#c0c0c0"
            ).pack(anchor="w")

            col = (col + 1) % columns

    def delete_sneaker(self):
        if self.selected_sneaker:
            confirm = messagebox.askyesno("确认", "确认删除该球鞋吗？")
            if confirm:
                with get_db() as db:
                    SneakerRepository.delete(db, self.selected_sneaker.id)
                    db.commit()
                self.selected_sneaker = None
                self.selected_card = None
                self.refresh_sneaker_list()
                messagebox.showinfo("成功", "删除成功！")
        else:
            messagebox.showwarning("警告", "请先选中一双球鞋")

    def refresh_sneaker_list(self):
        for widget in self.list_container.winfo_children():
            widget.destroy()

        self.selected_sneaker = None
        self.selected_card = None

        with get_db() as db:
            self.sneakers = SneakerRepository.get_all(db)

        keyword = self.search_entry.get().lower()
        min_price = self.min_price_entry.get()
        max_price = self.max_price_entry.get()

        self.filtered_sneakers = []  # 关键：存储筛选结果
        for s in self.sneakers:
            if keyword and keyword not in s.name.lower():
                continue
            if min_price and s.purchase_price < float(min_price):
                continue
            if max_price and s.purchase_price > float(max_price):
                continue
            self.filtered_sneakers.append(s)

        # 更新统计卡
        self.total_label.configure(text=f"总球鞋数: {len(self.filtered_sneakers)}")
        total_value = sum([s.purchase_price for s in self.filtered_sneakers])
        avg_value = total_value / len(self.filtered_sneakers) if self.filtered_sneakers else 0
        self.total_value_label.configure(text=f"总价值: {total_value}元")
        self.average_value_label.configure(text=f"平均价值: {avg_value:.2f}元")

        # 渲染列表 or 鞋墙
        if self.current_view == "list":
            for sneaker in self.filtered_sneakers:
                self.create_sneaker_card(sneaker)
            self.show_list_view()
        else:
            self.show_wall_view()

    def show_next_image(self, sneaker, label):
        images = sneaker.image_path.split(';') if sneaker.image_path else []
        if images:
            self.current_image_index[sneaker.id] = (self.current_image_index[sneaker.id] + 1) % len(images)
            image = Image.open(images[self.current_image_index[sneaker.id]])
            image = image.resize((120, 120))
            photo = ImageTk.PhotoImage(image)
            label.configure(image=photo)
            label.image = photo

    def calculate_days(self, purchase_date_str):
        try:
            purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
            return (datetime.today().date() - purchase_date).days
        except:
            return "-"

    def select_sneaker(self, sneaker, card):
        if self.selected_card and self.selected_card.winfo_exists():
            self.selected_card.configure(border_color="white", border_width=0)
        self.selected_sneaker = sneaker
        self.selected_card = card
        self.selected_card.configure(border_color="#FFD700", border_width=2)

    def edit_sneaker(self):
        if self.selected_sneaker:
            self.open_sneaker_form(self.selected_sneaker)
        else:
            messagebox.showwarning("警告", "请先选中一双球鞋")

    def clear_search(self):
        self.search_entry.delete(0, 'end')
        self.min_price_entry.delete(0, 'end')
        self.max_price_entry.delete(0, 'end')
        self.refresh_sneaker_list()
