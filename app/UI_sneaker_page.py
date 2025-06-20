# UI_sneaker_page.py
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from app.repositories.sneaker_repository import SneakerRepository
from app.database import get_db
from PIL import Image, ImageTk
import os
from datetime import datetime

# 可选品牌列表
BRAND_OPTIONS = [
    "Nike", "Jordan", "Adidas", "ASICS", "Under Armour", "New Balance", "Puma", "Converse", "Reebok", "FILA", "Mizuno",
    "Onitsuka Tiger", "Saucony", "Kappa", "Umbro", "李宁", "安踏", "匹克", "361度", "特步", "中国乔丹", "SPO", "EQLZ草牌", "准者", "迪卡侬",
    "昂跑", "斯凯奇", "Salomon", "凯乐石", "其他"
]

class SneakerMainPage(ctk.CTkFrame):
    def __init__(self, master, sneaker_service, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d")

        self.active_frame = None
        self.sneaker_service = sneaker_service
        self.sneakers = []
        self.selected_image_paths = []
        self.current_image_index = {}
        self.selected_sneaker = None
        self.selected_card = None
        self.filtered_sneakers = []
        self.current_view = "list"
        self.wall_background = None

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # === 第一行：标题 + 操作按钮 ===
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

        button_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="e", padx=10)

        btn_style = {
            "width": 40, "height": 40, "corner_radius": 20,
            "fg_color": "#3e3e5b", "hover_color": "#4c4c70", "text_color": "white"
        }
        ctk.CTkButton(button_frame, text="⇄切换视图", **btn_style, command=self.switch_view).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="🗑删除", **btn_style, command=self.delete_sneaker).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="✎修改", **btn_style, command=self.edit_sneaker).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="+新增", **btn_style, command=lambda: self.open_sneaker_form()).pack(side="right", padx=5)

        # === 第二行：统计信息 ===
        self.stats_frame = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        stat_style = {"font": ("微软雅黑", 14), "text_color": "#e0e0e0"}
        self.total_label = ctk.CTkLabel(self.stats_frame, text="总球鞋数: 0", **stat_style)
        self.total_value_label = ctk.CTkLabel(self.stats_frame, text="总价值: 0元", **stat_style)
        self.average_value_label = ctk.CTkLabel(self.stats_frame, text="平均价值: 0元", **stat_style)
        self.total_label.pack(side="left", padx=20, pady=10)
        self.total_value_label.pack(side="left", padx=20, pady=10)
        self.average_value_label.pack(side="left", padx=20, pady=10)

        # === 第三行：搜索区域 ===
        self.search_frame = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        self.search_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        entry_style = {
            "fg_color": "#3e3e5b", "border_width": 0,
            "text_color": "white", "placeholder_text_color": "gray"
        }
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="关键词搜索", **entry_style)
        self.min_price_entry = ctk.CTkEntry(self.search_frame, placeholder_text="最低价格", width=100, **entry_style)
        self.max_price_entry = ctk.CTkEntry(self.search_frame, placeholder_text="最高价格", width=100, **entry_style)
        for w in (self.search_entry, self.min_price_entry, self.max_price_entry):
            w.pack(side="left", padx=5, fill="x", expand=(w is self.search_entry))
            w.bind("<Return>", lambda e: self.refresh_sneaker_list())
        small_btn = {"fg_color": "#3e3e5b", "hover_color": "#4c4c70", "text_color": "white", "height": 34}
        ctk.CTkButton(self.search_frame, text="搜索", **small_btn, command=self.refresh_sneaker_list).pack(side="left", padx=5)
        ctk.CTkButton(self.search_frame, text="清除", **small_btn, command=self.clear_search).pack(side="left", padx=5)

        # === 第四行：列表 & 鞋墙容器 ===
        # 列表视图
        self.listbox_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_canvas = tk.Canvas(self.listbox_frame, bg="#1e1e2d", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical", command=self.list_canvas.yview)
        self.list_container = ctk.CTkFrame(self.list_canvas, fg_color="transparent")
        self.list_container.bind("<Configure>", lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")))
        self.list_canvas.create_window((0,0), window=self.list_container, anchor="nw")
        self.list_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.list_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 鞋墙视图
        self.wall_canvas = tk.Canvas(self, bg="#1e1e2d", highlightthickness=0)
        self.wall_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.wall_canvas.yview)
        self.wall_container = ctk.CTkFrame(self.wall_canvas, fg_color="transparent")
        self.wall_container.bind("<Configure>", lambda e: self.wall_canvas.configure(scrollregion=self.wall_canvas.bbox("all")))
        self.wall_canvas.create_window((0,0), window=self.wall_container, anchor="nw")
        self.wall_canvas.configure(yscrollcommand=self.wall_scrollbar.set)

        # 初始加载
        self.refresh_sneaker_list()

    def open_sneaker_form(self, sneaker=None):
        form = ctk.CTkToplevel(self)
        form.title("新增球鞋" if sneaker is None else "修改球鞋")
        form.geometry("400x550")
        form.grab_set()
        form.grid_columnconfigure(1, weight=1)

        # 定义字段
        fields = ["名称", "品牌", "系列", "购入日期", "购入价格", "尺码", "颜色"]
        entries = {}
        var_brand = tk.StringVar(value=(sneaker.brand if sneaker else BRAND_OPTIONS[0]))

        # 依次创建
        for idx, field in enumerate(fields):
            ctk.CTkLabel(form, text=field).grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            if field == "品牌":
                # 下拉选择品牌
                ctk.CTkOptionMenu(form, values=BRAND_OPTIONS, variable=var_brand).grid(row=idx, column=1, sticky="ew", padx=5, pady=5)
            else:
                ent = ctk.CTkEntry(form)
                ent.grid(row=idx, column=1, sticky="ew", padx=5, pady=5)
                # 编辑模式下预填
                if sneaker:
                    val = getattr(sneaker, {
                        "名称":"name","系列":"series","购入日期":"purchase_date",
                        "购入价格":"purchase_price","尺码":"size","颜色":"color"
                    }[field])
                    ent.insert(0, str(val) if val is not None else "")
                entries[field] = ent

        # “使用状态”下拉
        status_var = ctk.StringVar(value=(sneaker.status if sneaker else "使用中"))
        ctk.CTkLabel(form, text="使用状态").grid(row=len(fields), column=0, sticky="w", padx=5, pady=5)
        ctk.CTkOptionMenu(
            form,
            values=["收藏中", "使用中", "修复中", "闲置中", "挂卖中", "已卖出"],
            variable=status_var
        ).grid(row=len(fields), column=1, sticky="ew", padx=5, pady=5)

        # 只有编辑时显示下面五项
        if sneaker:
            extra_start = 8
            # 货号
            item_var = ctk.CTkEntry(form)
            ctk.CTkLabel(form, text="货号").grid(row=len(fields) + 1, column=0, sticky="w", padx=5, pady=5)
            item_var.grid(row=len(fields) + 1, column=1, padx=5, pady=5, sticky="ew")
            item_var.insert(0, sneaker.item_number or "")

            # 新旧
            cond_var = ctk.StringVar(value=sneaker.condition or "全新")
            ctk.CTkLabel(form, text="新旧").grid(row=len(fields) + 2, column=0, sticky="w", padx=5, pady=5)
            ctk.CTkOptionMenu(
                form, values=["全新", "二手"], variable=cond_var
            ).grid(row=len(fields) + 2, column=1, padx=5, pady=5, sticky="ew")

            # 是否有鞋盒
            box_var = ctk.StringVar(value=sneaker.has_box or "是")
            ctk.CTkLabel(form, text="有鞋盒").grid(row=len(fields) + 3, column=0, sticky="w", padx=5, pady=5)
            ctk.CTkOptionMenu(
                form, values=["是", "否"], variable=box_var
            ).grid(row=len(fields) + 3, column=1, padx=5, pady=5, sticky="ew")

            # 是否实战
            act_var = ctk.StringVar(value=sneaker.actual or "是")
            ctk.CTkLabel(form, text="实战鞋").grid(row=len(fields) + 4, column=0, sticky="w", padx=5, pady=5)
            ctk.CTkOptionMenu(
                form, values=["是", "否"], variable=act_var
            ).grid(row=len(fields) + 4, column=1, padx=5, pady=5, sticky="ew")

            # 类型
            type_var = ctk.StringVar(value=sneaker.shoe_type or "篮球鞋")
            types = ["竞速跑鞋", "慢跑鞋", "休闲鞋", "篮球鞋", "足球鞋", "旅游鞋",
                     "篮球文化鞋", "羽毛球鞋", "乒乓球鞋", "越野鞋", "滑板鞋", "五指鞋",
                     "溯溪鞋", "高尔夫球鞋", "拖鞋", "其他"]
            ctk.CTkLabel(form, text="类型").grid(row=len(fields) + 5, column=0, sticky="w", padx=5, pady=5)
            ctk.CTkOptionMenu(
                form, values=types, variable=type_var).grid(row=len(fields) + 5, column=1, padx=5, pady=5, sticky="ew")

            bottom_row = extra_start + 5
        else:
            bottom_row = 8  # 新增模式时，直接在状态下一行放按钮

        # 图片上传按钮
        image_paths = sneaker.image_path.split(";") if sneaker and sneaker.image_path else []
        def upload_images():
            paths = filedialog.askopenfilenames(filetypes=[("Image Files","*.png;*.jpg;*.jpeg")])
            if paths:
                image_paths.clear()
                image_paths.extend(paths)
        ctk.CTkButton(form, text="上传图片", command=upload_images).grid(
            row=len(fields)+1, column=0, columnspan=2, pady=5
        )

        # 保存逻辑
        def save():
            try:
                with get_db() as db:
                    data = {
                        "name": entries["名称"].get().strip(),
                        "brand": var_brand.get(),
                        "series": entries["系列"].get().strip(),
                        "purchase_date": entries["购入日期"].get().strip(),
                        "purchase_price": float(entries["购入价格"].get()),
                        "size": float(entries["尺码"].get()),
                        "color": entries["颜色"].get().strip(),
                        "status": status_var.get(),
                        "image_path": ";".join(image_paths)
                    }
                    if sneaker:
                        # 编辑时写入新增五项
                        data.update({
                            "item_number": item_var.get(),
                            "condition": cond_var.get(),
                            "has_box": box_var.get(),
                            "actual": act_var.get(),
                            "shoe_type": type_var.get()
                        })
                        SneakerRepository.update(db, sneaker.id, data)
                    else:
                        SneakerRepository.create(db, data)
                messagebox.showinfo("成功", "保存成功！")
                form.destroy()
                self.refresh_sneaker_list()
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

        ctk.CTkButton(form, text="保存", command=save).grid(
            row=len(fields)+2, column=0, columnspan=2, pady=15
        )

        # 让第二列可以拉伸
        form.grid_columnconfigure(1, weight=1)

    def create_sneaker_card(self, sneaker):
        # 卡片容器
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

        # 图片区域：改为 grid 布局
        img_frame = ctk.CTkFrame(card, fg_color="transparent", width=150)
        # pack 改为 grid
        img_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nw")
        images = sneaker.image_path.split(';') if sneaker.image_path else []
        self.current_image_index[sneaker.id] = 0
        if images and os.path.exists(images[0]):
            try:
                img = Image.open(images[0]).resize((120, 120))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(img_frame, image=photo, bg="#2d2d44")
                lbl.image = photo
                lbl.pack()
                if len(images) > 1:
                    ctk.CTkButton(
                        img_frame, text=">", width=30, height=30, corner_radius=15,
                        fg_color="#3e3e5b", hover_color="#4c4c70", text_color="white",
                        command=lambda s=sneaker, l=lbl: self.show_next_image(s, l)
                    ).pack(pady=5)
            except Exception as e:
                print("图片加载失败：", e)
        else:
            tk.Label(img_frame, text="无图片", width=15, height=7, bg="#2d2d44", fg="white").pack()

        # 信息区域：单个容器，用 grid
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nw")

        # 第一行：名称（左）+ 价格（右）
        name_lbl = ctk.CTkLabel(
            info_frame,
            text=sneaker.name,
            font=("微软雅黑", 18, "bold"),  # 字体放大加粗
            text_color="#f0f0f0"
        )
        name_lbl.grid(
            row=0, column=0,
            sticky="w",
            padx=(6, 0),  # 向右移一点
            pady=(5, 2)
        )

        price_lbl = ctk.CTkLabel(
            info_frame,
            text=f"¥{sneaker.purchase_price}",
            font=("微软雅黑", 18, "bold"),  # 字体放大加粗
            text_color="#FFD700"
        )
        price_lbl.grid(
            row=0, column=3,
            sticky="e",
            padx=(0, 22),  # 向左移一点
            pady=(5, 2)
        )

        # 配置 4 列平分宽度
        for col in range(4):
            info_frame.grid_columnconfigure(col, weight=1, uniform="col")

        # 后续 11 条属性
        days_owned = self.calculate_days(sneaker.purchase_date)
        attrs = [
            f"品牌: {sneaker.brand}",
            f"系列: {sneaker.series}",
            f"尺码: {sneaker.size}",
            f"颜色: {sneaker.color}",
            f"状态: {sneaker.status}",
            f"新旧: {getattr(sneaker, 'condition', '')}",
            f"鞋盒: {getattr(sneaker, 'has_box', '')}",
            f"实战: {getattr(sneaker, 'actual', '')}",
            f"类型: {getattr(sneaker, 'shoe_type', '')}",
            f"货号: {sneaker.item_number or ''}",
            f"已拥有: {days_owned}天",
        ]
        # 放到 3×4 的网格里，最后一个空位自然留白
        for idx, text in enumerate(attrs):
            r = 1 + idx // 4  # 从第 1 行开始
            c = idx % 4
            lbl = ctk.CTkLabel(info_frame,
                               text=text,
                               font=("微软雅黑", 12),
                               text_color="#c0c0c0")
            lbl.grid(row=r, column=c, sticky="w", padx=5, pady=(2, 0))

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
        # 先把旧的 active_frame 隐藏掉
        if self.active_frame:
            self.active_frame.grid_forget()

        # 把 wall_canvas 和 scrollbar 摆上来
        self.wall_canvas.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.wall_scrollbar.grid(row=3, column=0, sticky="nse")
        self.active_frame = self.wall_canvas

        # 清空掉之前渲染的内容
        for widget in self.wall_container.winfo_children():
            widget.destroy()

        # 如果没有任何筛选后球鞋，直接显示提示
        if not getattr(self, "filtered_sneakers", []):
            no_label = ctk.CTkLabel(
                self.wall_container,
                text="还没有球鞋呢，快去添加一双吧~",
                font=("微软雅黑", 16, "bold"),
                text_color="#c0c0c0"
            )
            no_label.pack(expand=True, pady=40)
        else:
            # 否则正常渲染鞋墙
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
        # 先把列表视图 grid 出来（即使里面是空的也要显示框架）
        self.current_view = "list"
        self.show_list_view()

        # 清空旧内容
        for widget in self.list_container.winfo_children():
            widget.destroy()

        # 读取所有球鞋
        with get_db() as db:
            all_sneakers = SneakerRepository.get_all(db)

        # 如果一双都没有，直接在列表容器中显示提示
        if not all_sneakers:
            no_label = ctk.CTkLabel(
                self.list_container,
                text="还没有球鞋呢，快去添加一双吧~",
                font=("微软雅黑", 16, "bold"),
                text_color="#c0c0c0"
            )
            no_label.pack(expand=True, pady=40)

            # 统计也同步清空/重置
            self.total_label.configure(text="总球鞋数: 0")
            self.total_value_label.configure(text="总价值: 0元")
            self.average_value_label.configure(text="平均价值: 0元")
            return

        # 否则照常过滤、更新统计、渲染卡片
        keyword = self.search_entry.get().lower()
        min_price = self.min_price_entry.get()
        max_price = self.max_price_entry.get()

        self.filtered_sneakers = []
        for s in all_sneakers:
            if keyword and keyword not in s.name.lower():
                continue
            if min_price and s.purchase_price < float(min_price):
                continue
            if max_price and s.purchase_price > float(max_price):
                continue
            self.filtered_sneakers.append(s)

        count = len(self.filtered_sneakers)
        total_value = sum(s.purchase_price for s in self.filtered_sneakers)
        avg_value = total_value / count if count else 0
        self.total_label.configure(text=f"总球鞋数: {count}")
        self.total_value_label.configure(text=f"总价值: {total_value}元")
        self.average_value_label.configure(text=f"平均价值: {avg_value:.2f}元")

        # 渲染列表或鞋墙
        if self.current_view == "list":
            for sneaker in self.filtered_sneakers:
                self.create_sneaker_card(sneaker)
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
