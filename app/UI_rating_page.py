# app/UI_rating_page.py
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from app.repositories.sneaker_repository import SneakerRepository
from app.database import get_db
from app.services.rating_service import calculate_total_score, sort_by_total_score_desc, sort_by_total_score_asc, sort_by_dimension
from app.models import Sneaker

class RatingPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # 标题
        self.header = ctk.CTkLabel(self, text="评分库", font=("微软雅黑", 20, "bold"), anchor="w")
        self.header.pack(fill="x", pady=(10,0), padx=10)

        # 排序菜单
        self.sort_var = ctk.StringVar(value="默认排序")
        sort_options = [
            "默认排序",
            "总分从高到低",
            "总分从低到高",
            "缓震从高到低",
            "抓地从高到低",
            "抗扭从高到低",
            "耐磨从高到低",
            "包裹从高到低",
            "防侧翻从高到低",
            "重量从高到低",
            "舒适性从高到低"
        ]
        self.sort_menu = ctk.CTkOptionMenu(
            self,
            values=sort_options,
            variable=self.sort_var,
            command=self.on_sort_change
        )
        self.sort_menu.pack(pady=10, padx=10, anchor="w")

        # 主内容区
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.sneakers = []
        self.load_sneaker_rating_ui(self.content_frame)

    def load_sneaker_rating_ui(self, parent_frame, sneakers=None):
        # 清空旧内容
        for w in parent_frame.winfo_children():
            w.destroy()

        if sneakers is None:
            with get_db() as db:
                self.sneakers = SneakerRepository.get_all(db)

        for sneaker in self.sneakers:
            frame = ctk.CTkFrame(parent_frame, corner_radius=10, fg_color="#2d2d44")
            frame.pack(fill="x", pady=5, padx=5)

            total = calculate_total_score(sneaker.ratings)
            score_text = f"{total:.1f}" if total is not None else "N/A"

            lbl = ctk.CTkLabel(frame, text=f"{sneaker.brand} – {sneaker.name}    总分：{score_text}", font=("微软雅黑", 14, "bold"))
            lbl.pack(side="left", padx=10, pady=10)

            btn = ctk.CTkButton(frame, text="评分", width=80, command=lambda s=sneaker: self.open_rating_window(s))
            btn.pack(side="right", padx=10, pady=10)

    def on_sort_change(self, choice):
        # 根据 sort_var 重新排序 self.sneakers
        if choice == "默认排序":
            with get_db() as db:
                self.sneakers = SneakerRepository.get_all(db)
        elif choice == "总分从高到低":
            self.sneakers.sort(key=lambda s: calculate_total_score(s.ratings) or 0, reverse=True)
        elif choice == "总分从低到高":
            self.sneakers.sort(key=lambda s: calculate_total_score(s.ratings) or 0)
        else:
            # 具体维度排序
            mapping = {
                "缓震从高到低": ("cushion", True),
                "抓地从高到低": ("traction", True),
                "抗扭从高到低": ("torsion", True),
                "耐磨从高到低": ("durability", True),
                "包裹从高到低": ("wrap", True),
                "防侧翻从高到低": ("anti_roll", True),
                "重量从高到低": ("weight", True),
                "舒适性从高到低": ("comfort", True),
            }
            if choice in mapping:
                field, rev = mapping[choice]
                self.sneakers.sort(key=lambda s: getattr(s.ratings[-1], field) if s.ratings else 0, reverse=rev)

        self.load_sneaker_rating_ui(self.content_frame, self.sneakers)

    def open_rating_window(self, sneaker):
        popup = ctk.CTkToplevel(self)
        popup.title(f"评分：{sneaker.name}")
        popup.geometry("600x750")
        popup.resizable(False, False)

        # 1. 取最新一条评分
        from sqlalchemy.orm import joinedload
        with get_db() as db:
            sn = db.query(Sneaker) \
                .options(joinedload(Sneaker.ratings)) \
                .filter(Sneaker.id == sneaker.id) \
                .first()
        latest = sn.ratings[-1] if sn and sn.ratings else None

        main = ctk.CTkFrame(popup)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # 2. 滑条字段：1-10 分制
        slider_cfg = {
            'cushion': ("缓震", latest.cushion if latest else 5),
            'traction': ("抓地", latest.traction if latest else 5),
            'torsion': ("抗扭", latest.torsion if latest else 5),
            'durability': ("耐磨", latest.durability if latest else 5),
            'wrap': ("包裹", latest.wrap if latest else 5),
            'anti_roll': ("防侧翻", latest.anti_roll if latest else 5),
            'weight': ("重量", latest.weight if latest else 5),
            'comfort': ("舒适性", latest.comfort if latest else 5),
        }
        sliders = {}
        row = 0
        for field, (label_text, init_val) in slider_cfg.items():
            ctk.CTkLabel(main, text=label_text, width=80).grid(row=row, column=0, pady=5, sticky="w")
            s = ctk.CTkSlider(main, from_=1, to=10, number_of_steps=9)
            s.set(init_val)
            s.grid(row=row, column=1, sticky="ew", padx=5)
            vlabel = ctk.CTkLabel(main, text=f"{int(init_val)}/10", width=50)
            vlabel.grid(row=row, column=2, padx=5)
            # 滑条联动数值标签
            s.configure(command=lambda v, l=vlabel: l.configure(text=f"{int(v)}/10"))
            sliders[field] = s
            row += 1

        # 3. 单选下拉：内长、鞋仓深度
        inner_opts = ["偏短", "适中", "偏长"]
        depth_opts = ["适合高脚背", "适合中等脚背", "适合低脚背"]
        inner_var = tk.StringVar(value=(latest.inner_length if latest and latest.inner_length else inner_opts[1]))
        depth_var = tk.StringVar(value=(latest.depth if latest and latest.depth else depth_opts[1]))

        ctk.CTkLabel(main, text="内长").grid(row=row, column=0, pady=5, sticky="w")
        ctk.CTkOptionMenu(main, values=inner_opts, variable=inner_var).grid(row=row, column=1, columnspan=2,
                                                                            sticky="ew", padx=5)
        row += 1

        ctk.CTkLabel(main, text="鞋仓深度").grid(row=row, column=0, pady=5, sticky="w")
        ctk.CTkOptionMenu(main, values=depth_opts, variable=depth_var).grid(row=row, column=1, columnspan=2,
                                                                            sticky="ew", padx=5)
        row += 1

        # 4. 多选：鞋楦（width）和鞋垫（insole）
        width_opts = ["非常窄", "窄", "稍窄", "适中", "稍宽", "宽", "非常宽"]
        insole_opts = ["薄", "厚", "弹", "软", "重", "轻", "足弓支撑强", "足弓支撑弱"]
        width_vars = {}
        insole_vars = {}
        saved_w = (latest.width or "").split(",") if latest and latest.width else []
        saved_i = (latest.insole or "").split(",") if latest and latest.insole else []

        ctk.CTkLabel(main, text="鞋楦").grid(row=row, column=0, sticky="nw", pady=5)
        wf = ctk.CTkFrame(main);
        wf.grid(row=row, column=1, columnspan=2, sticky="w")
        for i, opt in enumerate(width_opts):
            width_vars[opt] = tk.BooleanVar(value=(opt in saved_w))
            ctk.CTkCheckBox(wf, text=opt, variable=width_vars[opt]) \
                .grid(row=i // 4, column=i % 4, padx=5, pady=2, sticky="w")
        row += (len(width_opts) // 4 + 1)

        ctk.CTkLabel(main, text="鞋垫").grid(row=row, column=0, sticky="nw", pady=5)
        inf = ctk.CTkFrame(main);
        inf.grid(row=row, column=1, columnspan=2, sticky="w")
        for i, opt in enumerate(insole_opts):
            insole_vars[opt] = tk.BooleanVar(value=(opt in saved_i))
            ctk.CTkCheckBox(inf, text=opt, variable=insole_vars[opt]) \
                .grid(row=i // 4, column=i % 4, padx=5, pady=2, sticky="w")
        row += (len(insole_opts) // 4 + 1)

        # 5. 提交按钮
        def submit():
            w_val = ",".join([o for o, v in width_vars.items() if v.get()])
            i_val = ",".join([o for o, v in insole_vars.items() if v.get()])
            with get_db() as db:
                SneakerRepository.add_rating(
                    db,
                    sneaker.id,
                    cushion=int(sliders['cushion'].get()),
                    traction=int(sliders['traction'].get()),
                    torsion=int(sliders['torsion'].get()),
                    durability=int(sliders['durability'].get()),
                    wrap=int(sliders['wrap'].get()),
                    anti_roll=int(sliders['anti_roll'].get()),
                    weight=int(sliders['weight'].get()),
                    comfort=int(sliders['comfort'].get()),
                    width=w_val,
                    inner_length=inner_var.get(),
                    insole=i_val,
                    depth=depth_var.get()
                )
            popup.destroy()
            messagebox.showinfo("提示", "评分已保存！")
            self.refresh()

        ctk.CTkButton(main, text="提交评分", command=submit) \
            .grid(row=row, column=0, columnspan=3, pady=20)

        popup.grab_set()

    def refresh(self):
        """刷新评分列表：清空旧条目并重绘"""
        for w in self.content_frame.winfo_children():
            w.destroy()
        self.load_sneaker_rating_ui(self.content_frame, self.sneakers)
