# app/UI_rating_page.py

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from app.database import get_db
from app.repositories.sneaker_repository import SneakerRepository
from app.services.rating_service import calculate_total_score
from app.models import Sneaker, Rating
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload
from app.models import Rating, Sneaker
from app.database import get_db

class RatingPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d")

        # 顶部标题
        ctk.CTkLabel(self, text="球鞋评分", font=("微软雅黑", 22, "bold"), text_color="white") \
            .pack(anchor="w", padx=20, pady=(20, 5))

        # 上半区：评分列表与排序
        top_frame = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        top_frame.pack(fill="x", padx=20, pady=(0,10), ipady=5)
        ctk.CTkLabel(top_frame, text="评分列表", font=("微软雅黑", 16, "bold"), text_color="white") \
            .pack(side="left", padx=10)

        self.sort_var = ctk.StringVar(value="默认排序")
        sort_options = [
            "默认排序", "总分从高到低", "总分从低到高",
            "缓震从高到低", "抓地从高到低", "抗扭从高到低", "耐磨从高到低",
            "包裹从高到低", "防侧翻从高到低", "重量从高到低", "舒适性从高到低"
        ]
        ctk.CTkOptionMenu(
            top_frame,
            values=sort_options,
            variable=self.sort_var,
            command=self.on_sort_change,
            fg_color="#3e3e5b",
            button_color="#3e3e5b",
            text_color="white",
            dropdown_fg_color="#2d2d44",
            dropdown_text_color="white"
        ).pack(side="right", padx=10)

        # 列表容器
        self.list_container = ctk.CTkScrollableFrame(
            self, fg_color="#2d2d44", corner_radius=10, height=260
        )
        self.list_container.pack(fill="x", padx=20, pady=(0,20))

        # 初始化数据
        self.sneakers = []
        self.selected_sneaker = None
        self.selected_frame = None
        self.load_sneakers()

        # 下半区：评分明细
        ctk.CTkLabel(self, text="评分明细", font=("微软雅黑", 16, "bold"), text_color="white") \
            .pack(anchor="w", padx=20, pady=(0,5))

        self.detail_frame = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        self.detail_frame.pack(fill="both", expand=True, padx=20, pady=(0,20))

        # 左：雷达图 60%
        self.radar_container = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        self.radar_container.place(relx=0, rely=0, relwidth=0.6, relheight=1)
        # 右：文字详情 40%
        self.text_container = ctk.CTkScrollableFrame(
            self.detail_frame, fg_color="transparent", corner_radius=0
        )
        self.text_container.place(relx=0.6, rely=0, relwidth=0.4, relheight=1)

    def load_sneakers(self):
        """从 DB 拉取所有鞋、渲染列表"""
        with get_db() as db:
            self.sneakers = SneakerRepository.get_all(db)
        # 清掉之前的选择
        self.selected_sneaker = None
        self.selected_frame = None
        self.render_list()
        # —— 安全清空明细区域 —— #
        if hasattr(self, 'radar_container'):
            for w in self.radar_container.winfo_children():
                w.destroy()
        if hasattr(self, 'text_container'):
            for w in self.text_container.winfo_children():
                w.destroy()

    def render_list(self):
        """上半区：评分列表"""
        for w in self.list_container.winfo_children():
            w.destroy()

        for sn in self.sneakers:
            frame = ctk.CTkFrame(
                self.list_container,
                fg_color="#2d2d44", corner_radius=8,
                border_width=2, border_color="#2d2d44"
            )
            frame.pack(fill="x", pady=4, padx=10)
            frame.bind("<Button-1>", lambda e, s=sn, f=frame: self.on_select(s, f))

            # 左侧文字
            total = calculate_total_score(sn.ratings)
            txt = f"{sn.brand} - {sn.name}    总分：{total:.1f}" if total is not None else "暂无评分"
            ctk.CTkLabel(frame, text=txt, font=("微软雅黑", 14), text_color="white")\
                .pack(side="left", padx=10, pady=10)

            # “评分”按钮
            ctk.CTkButton(
                frame, text="评分", width=80,
                command=lambda s=sn: self.open_rating_window(s)
            ).pack(side="right", padx=5, pady=5)
            # “重置分数”按钮
            ctk.CTkButton(
                frame, text="重置分数", width=100,
                command=lambda s=sn: self.reset_scores(s)
            ).pack(side="right", padx=5, pady=5)

        # 如果有已选中的，重新高亮
        if self.selected_sneaker:
            for sn_obj, f_obj in zip(self.sneakers, self.list_container.winfo_children()):
                if sn_obj.id == self.selected_sneaker.id:
                    self.highlight_frame(f_obj)
                    break

    def on_sort_change(self, choice):
        """根据下拉重新给 self.sneakers 排序并刷新"""
        # 先取消选择
        self.selected_sneaker = None
        self.selected_frame = None

        # 排序逻辑
        if choice == "总分从高到低":
            self.sneakers.sort(key=lambda s: calculate_total_score(s.ratings) or 0, reverse=True)
        elif choice == "总分从低到高":
            self.sneakers.sort(key=lambda s: calculate_total_score(s.ratings) or 0, reverse=False)
        else:
            # 针对各维度
            field_map = {
                "缓震": "cushion", "抓地": "traction", "抗扭": "torsion", "耐磨": "durability",
                "包裹": "wrap", "防侧翻": "anti_roll", "重量": "weight", "舒适性": "comfort"
            }
            for label, field in field_map.items():
                if choice.startswith(label):
                    rev = "高" in choice
                    self.sneakers.sort(
                        key=lambda s: getattr(s.ratings[-1], field) if s.ratings else 0,
                        reverse=rev
                    )
                    break
        self.render_list()

    def on_select(self, sneaker, frame):
        """列表项点击：高亮 & 渲染明细"""
        self.selected_sneaker = sneaker
        self.highlight_frame(frame)
        self.render_detail(sneaker)

    def highlight_frame(self, frame):
        """把之前的取消高亮，新框设置黄色"""
        if self.selected_frame and self.selected_frame.winfo_exists():
            self.selected_frame.configure(border_color="#2d2d44")
        frame.configure(border_color="#DDB92B")
        self.selected_frame = frame

    def render_detail(self, sneaker):
        # 先用新 Session 彻底拉一遍
        with get_db() as db:
            sn = (
                db.query(Sneaker)
                .options(joinedload(Sneaker.ratings))
                .filter(Sneaker.id == sneaker.id)
                .first()
            )
        # 接下来都用 ’sn‘ 而不是原来的 ’sneaker‘
        records = sn.ratings
        """在下半区根据选中鞋渲染雷达图 + 文本"""
        for w in self.radar_container.winfo_children(): w.destroy()
        for w in self.text_container.winfo_children(): w.destroy()

        # 如果没评分
        if not sneaker.ratings:
            ctk.CTkLabel(self.text_container, text="暂无评分记录",
                         font=("微软雅黑", 14), text_color="white") \
               .pack(pady=20)
            return

        latest = sneaker.ratings[-1]

        # —— 雷达图 —— #
        labels = ["缓震","抓地","抗扭","耐磨","包裹","防侧翻","重量","舒适"]
        values = [
            latest.cushion, latest.traction, latest.torsion, latest.durability,
            latest.wrap, latest.anti_roll, latest.weight, latest.comfort
        ]
        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
        vals = values + values[:1]
        angs = angles + angles[:1]

        fig = Figure(figsize=(4,3), dpi=100)
        ax = fig.add_subplot(111, polar=True)
        ax.plot(angs, vals, 'o-', linewidth=2, color='gold')
        ax.fill(angs, vals, alpha=0.25, color='gold')
        ax.set_thetagrids(np.degrees(angles), labels, fontproperties="SimHei")
        ax.set_ylim(0,10)
        ax.grid(color='gray', linestyle='--', linewidth=0.5)

        canvas = FigureCanvasTkAgg(fig, master=self.radar_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # —— 文本描述 —— #
        def add_txt(k, v):
            text = f"{k}：{v or '无'}"
            ctk.CTkLabel(self.text_container, text=text,
                         font=("微软雅黑", 14), text_color="white", anchor="w")\
               .pack(fill="x", padx=10, pady=2)

        # 8 个量化
        add_txt("缓震", f"{latest.cushion}/10")
        add_txt("抓地", f"{latest.traction}/10")
        add_txt("抗扭", f"{latest.torsion}/10")
        add_txt("耐磨", f"{latest.durability}/10")
        add_txt("包裹", f"{latest.wrap}/10")
        add_txt("防侧翻", f"{latest.anti_roll}/10")
        add_txt("重量", f"{latest.weight}/10")
        add_txt("舒适性", f"{latest.comfort}/10")

        # 4 个定性
        add_txt("鞋楦",       latest.width)
        add_txt("内长",       latest.inner_length)
        add_txt("鞋垫",       latest.insole)
        add_txt("鞋仓深度", latest.depth)

    def reset_scores(self, sneaker):
        """一键将该鞋所有评分字段重置为默认 5 分"""
        with get_db() as db:
            SneakerRepository.add_rating(
                db,
                sneaker.id,
                cushion=5, traction=5, torsion=5, durability=5,
                wrap=5, anti_roll=5, weight=5, comfort=5,
                width=sneaker.ratings[-1].width   if sneaker.ratings else "",
                inner_length=sneaker.ratings[-1].inner_length if sneaker.ratings else "",
                insole=sneaker.ratings[-1].insole  if sneaker.ratings else "",
                depth=sneaker.ratings[-1].depth   if sneaker.ratings else ""
            )
        # 重新拉 DB 并刷新列表、明细
        self.load_sneakers()
        # 取最新实例
        with get_db() as db:
            fresh = db.query(Sneaker).filter(Sneaker.id==sneaker.id).first()
        self.selected_sneaker = fresh
        self.render_detail(fresh)

    def open_rating_window(self, sneaker: Sneaker):
        popup = ctk.CTkToplevel(self)
        popup.title(f"评分：{sneaker.brand} - {sneaker.name}")
        popup.geometry("1000x700")
        popup.resizable(False, False)

        # 拉最新记录
        with get_db() as db:
            sn_db = (
                db.query(Sneaker)
                .options(joinedload(Sneaker.ratings))
                .filter(Sneaker.id == sneaker.id)
                .first()
            )
            latest = sn_db.ratings[-1] if sn_db.ratings else None

        # 滚动容器
        canvas = tk.Canvas(popup, bg="#1e1e2d", highlightthickness=0)
        vsb = tk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        container = ctk.CTkFrame(canvas, fg_color="transparent")
        container.bind("<Configure>",
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # —— 8 个滑杆 —— #
        self.slider_vars = {}
        dims = [
            ("缓震", "cushion"), ("抓地", "traction"), ("抗扭", "torsion"), ("耐磨", "durability"),
            ("包裹", "wrap"), ("防侧翻", "anti_roll"), ("重量", "weight"), ("舒适性", "comfort")
        ]
        for cn, field in dims:
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=cn, width=60, text_color="white").pack(side="left")

            var = tk.IntVar(value=getattr(latest, field) if latest else 5)
            slider = ctk.CTkSlider(
                f, from_=1, to=10, number_of_steps=9,
                variable=var, width=200
            )
            slider.pack(side="left", padx=(10,5))

            val_lbl = ctk.CTkLabel(f, text=f"{var.get()}/10",
                                   text_color="white", width=50)
            val_lbl.pack(side="left", padx=(5,0))
            var.trace_add("write",
                          lambda *a, v=var, l=val_lbl: l.configure(text=f"{v.get()}/10"))
            self.slider_vars[field] = var

        # —— 4 个定性 —— #
        mults = [
            ("鞋楦 (可多选)", "width", ["非常窄","窄","稍窄","适中","稍宽","宽","非常宽"]),
            ("鞋垫 (可多选)", "insole",["薄","厚","弹","软","重","轻","足弓支撑强","足弓支撑弱"])
        ]
        self.multi_vars = {}
        for label, attr, opts in mults:
            ctk.CTkLabel(container, text=label,
                         text_color="white", anchor="w")\
               .pack(fill="x", padx=20, pady=(10,0))
            frm = ctk.CTkFrame(container, fg_color="transparent")
            frm.pack(fill="x", padx=20)
            lst = []
            current = getattr(latest, attr).split(";") if (latest and getattr(latest, attr)) else []
            for opt in opts:
                var = tk.BooleanVar(value=(opt in current))
                ctk.CTkCheckBox(frm, text=opt, variable=var,
                                text_color="white").pack(side="left", padx=5, pady=5)
                lst.append((opt, var))
            self.multi_vars[attr] = lst

        singles = [
            ("内长 (单选)", "inner_length", ["偏短","适中","偏长"]),
            ("鞋仓深度 (单选)", "depth",
             ["适合高脚背","适合中等脚背","适合低脚背"])
        ]
        self.single_vars = {}
        for label, attr, opts in singles:
            ctk.CTkLabel(container, text=label,
                         text_color="white", anchor="w")\
               .pack(fill="x", padx=20, pady=(10,0))
            var = tk.StringVar(value=getattr(latest, attr) if latest else "")
            om = ctk.CTkOptionMenu(
                container, values=opts, variable=var,
                fg_color="#3e3e5b", button_color="#3e3e5b",
                text_color="white",
                dropdown_fg_color="#2d2d44",
                dropdown_text_color="white"
            )
            om.pack(fill="x", padx=20, pady=5)
            self.single_vars[attr] = var

        # —— 提交按钮 —— #
        def submit():
            # --- 1. 各维度取值 --- #
            # 滑杆
            data = {
                'cushion': self.slider_vars['cushion'].get(),
                'traction': self.slider_vars['traction'].get(),
                'torsion': self.slider_vars['torsion'].get(),
                'durability': self.slider_vars['durability'].get(),
                'wrap': self.slider_vars['wrap'].get(),
                'anti_roll': self.slider_vars['anti_roll'].get(),
                'weight': self.slider_vars['weight'].get(),
                'comfort': self.slider_vars['comfort'].get(),
            }
            # 多选：鞋楦、鞋垫
            sel_width = [opt for opt, var in self.multi_vars['width'] if var.get()]
            sel_insole = [opt for opt, var in self.multi_vars['insole'] if var.get()]
            data['width'] = ";".join(sel_width)
            data['insole'] = ";".join(sel_insole)
            # 单选：内长、仓深
            data['inner_length'] = self.single_vars['inner_length'].get()
            data['depth'] = self.single_vars['depth'].get()

            # --- 2. 写库并 reload fresh instance --- #
            with get_db() as db:
                # 新增一条 Rating
                record = Rating(
                    sneaker_id=sneaker.id,
                    **data
                )
                db.add(record)
                db.commit()

                # 重新拉一次 Sneaker + ratings
                fresh = (
                    db.query(Sneaker)
                    .options(joinedload(Sneaker.ratings))
                    .filter(Sneaker.id == sneaker.id)
                    .first()
                )

            # --- 3. 关闭弹窗，刷新下方详情 --- #
            popup.destroy()
            self.render_detail(fresh)

        # 注意：这里的 “提交评分” 按钮，一定要把 command 指向上面这个 submit()
        ctk.CTkButton(container, text="提交评分",
                      fg_color="#FFDF4E", text_color="black",
                      command=submit).pack(pady=20)