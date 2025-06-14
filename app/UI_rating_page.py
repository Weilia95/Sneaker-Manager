import customtkinter as ctk
from tkinter import messagebox
from app.repositories.sneaker_repository import SneakerRepository
from app.database import get_db
from app.rating_service import calculate_total_score, sort_by_total_score_desc, sort_by_total_score_asc, sort_by_dimension
from app.models import Sneaker

class RatingPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d")

        # ── 第一行：标题栏 ───────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            header,
            text="评分库",
            font=("微软雅黑", 20, "bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=10)

        # ── 排序选单 ───────────────────────────────────────
        # 排序下拉
        self.sort_var = ctk.StringVar(value="默认排序")
        sort_options = [
            "默认排序",
            "总分从高到低",
            "总分从低到高",
            "缓震从高到低",
            "抓地从高到低",
            "抗扭从高到低",
            "耐磨从高到低"
        ]
        self.sort_menu = ctk.CTkOptionMenu(
            self,
            values=sort_options,
            variable=self.sort_var,
            command=self.on_sort_change,
            fg_color="#3e3e5b",
            button_color="#3e3e5b",
            text_color="white",
            dropdown_fg_color="#2d2d44",
            dropdown_text_color="white"
        )
        self.sort_menu.pack(padx=20, anchor="w", pady=(0, 10))

        # 内容区域
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 初始加载
        self.sneakers = []
        self.load_sneaker_rating_ui(self.content_frame)

    def load_sneaker_rating_ui(self, parent_frame, sneakers=None):
        for widget in parent_frame.winfo_children():
            widget.destroy()

        if sneakers is None:
            with get_db() as db_session:
                self.sneakers = SneakerRepository.get_all(db_session)

        for sneaker in self.sneakers:
            card = ctk.CTkFrame(parent_frame, fg_color="#2d2d44", corner_radius=10, border_width=1, border_color="#3e3e5b")
            card.pack(fill="x", pady=5, padx=10)

            total_score = calculate_total_score(sneaker.ratings)
            score_text = f"总分: {total_score:.1f}" if total_score is not None else "暂无评分"

            label = ctk.CTkLabel(card, text=f"{sneaker.brand} - {sneaker.name} | {score_text}", text_color="white", font=("微软雅黑", 16))
            label.pack(side="left", padx=10, pady=10)

            button = ctk.CTkButton(card, text="评分", width=80, fg_color="#3e3e5b", hover_color="#4c4c70", text_color="white", command=lambda s=sneaker: self.open_rating_window(s))
            button.pack(side="right", padx=10)

    def on_sort_change(self, choice):
        # （排序逻辑不变）
        if choice == "默认排序":
            with get_db() as db_session:
                self.sneakers = SneakerRepository.get_all(db_session)
        elif choice == "总分从高到低":
            self.sneakers = sort_by_total_score_desc(self.sneakers)
        elif choice == "总分从低到高":
            self.sneakers = sort_by_total_score_asc(self.sneakers)
        else:
            # 维度排序：使用 1–10 分制下的值
            dimension_map = {
                "缓震从高到低": ("cushion", True),
                "抓地从高到低": ("traction", True),
                "抗扭从高到低": ("torsion", True),
                "耐磨从高到低": ("durability", True)
            }
            field, rev = dimension_map.get(choice, (None, False))
            if field:
                self.sneakers = sort_by_dimension(self.sneakers, field, reverse=rev)

        self.refresh()

    def open_rating_window(self, sneaker):
        popup = ctk.CTkToplevel(self)
        popup.title(f"评分：{sneaker.name}")
        popup.geometry("500x580")
        popup.resizable(False, False)

        main_frame = ctk.CTkFrame(popup)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text=f"{sneaker.brand} - {sneaker.name}", font=("微软雅黑", 16)).pack(pady=10)

        sliders = {}
        # 中文标签到属性名映射
        slider_labels = {
            "缓震": "cushion",
            "抓地": "traction",
            "抗扭": "torsion",
            "耐磨": "durability"
        }

        # 读取历史评分，取最后一次
        from sqlalchemy.orm import joinedload
        with get_db() as db_session:
            sneaker_in_db = db_session.query(Sneaker).options(joinedload(Sneaker.ratings)) \
                .filter(Sneaker.id == sneaker.id).first()
            ratings = sneaker_in_db.ratings
            latest_rating = ratings[-1] if ratings else None

        for cn_label, field in slider_labels.items():
            sub_frame = ctk.CTkFrame(main_frame)
            sub_frame.pack(fill="x", pady=5)

            # 标签
            lbl = ctk.CTkLabel(sub_frame, text=cn_label, width=60)
            lbl.pack(side="left", padx=5)

            # 1–10 分制
            slider = ctk.CTkSlider(sub_frame, from_=1, to=10, number_of_steps=9)
            # 如果已有评分且在 1–10 范围内就展示，否则默认 5
            init_val = getattr(latest_rating, field) if latest_rating else 5
            try:
                init_val = int(init_val)
                if init_val < 1 or init_val > 10:
                    init_val = 5
            except:
                init_val = 5
            slider.set(init_val)

            # 分值显示
            rating_label = ctk.CTkLabel(sub_frame, text=f"{init_val}/10", width=40)
            rating_label.pack(side="left", padx=5)

            # 拖动时更新文本
            def make_update_func(label_):
                return lambda val: label_.configure(text=f"{int(float(val))}/10")
            slider.configure(command=make_update_func(rating_label))
            slider.pack(side="left", expand=True, fill="x")

            sliders[cn_label] = slider

        def submit_rating():
            # 写入 1–10 分
            with get_db() as db_session:
                SneakerRepository.add_rating(
                    db_session,
                    sneaker.id,
                    int(sliders["缓震"].get()),
                    int(sliders["抓地"].get()),
                    int(sliders["抗扭"].get()),
                    int(sliders["耐磨"].get())
                )
            popup.destroy()
            messagebox.showinfo("提示", "评分已提交！")
            self.refresh()

        submit_btn = ctk.CTkButton(main_frame, text="提交评分", command=submit_rating)
        submit_btn.pack(pady=20)

        popup.grab_set()

    def refresh(self):
        """刷新列表，重绘所有条目"""
        # 清空旧 UI
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # 重新加载
        self.load_sneaker_rating_ui(self.content_frame, self.sneakers)
