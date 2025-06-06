
import customtkinter as ctk
from tkinter import messagebox
from .repositories.sneaker_repository import SneakerRepository

from .database import get_db
from .rating_service import calculate_total_score, sort_by_total_score_desc, sort_by_total_score_asc, sort_by_dimension
from .models import Sneaker


class RatingPage:
    def __init__(self, root):
        self.root = root
        self.page_frame = ctk.CTkFrame(self.root)
        self.page_frame.pack(fill="both", expand=True)
        self.parent_frame = self.page_frame  # 确保 refresh 能正确引用

        # 排序选项
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
            self.page_frame,
            values=sort_options,
            variable=self.sort_var,
            command=self.on_sort_change
        )
        self.sort_menu.pack(pady=10, anchor="w")

        # 初始化加载数据
        self.sneakers = []
        self.load_sneaker_rating_ui(self.page_frame)

    def load_sneaker_rating_ui(self, parent_frame,sneakers=None):
        if sneakers is None:
            with get_db() as db_session:
                self.sneakers = SneakerRepository.get_all(db_session)

        for sneaker in self.sneakers:
            frame = ctk.CTkFrame(parent_frame)
            frame.pack(fill="x", pady=5, padx=10)

            total_score = calculate_total_score(sneaker.ratings)
            score_text = f"总分: {total_score:.0f}" if total_score is not None else "暂无评分"

            label = ctk.CTkLabel(frame, text=f"{sneaker.brand} - {sneaker.name} | {score_text}")
            label.pack(side="left", padx=5)

            button = ctk.CTkButton(frame, text="评分", width=60, command=lambda s=sneaker: self.open_rating_window(s))
            button.pack(side="right", padx=5)

    def on_sort_change(self, choice):
        if choice == "默认排序":
            with get_db() as db_session:
                self.sneakers = SneakerRepository.get_all(db_session)
        elif choice == "总分从高到低":
            self.sneakers = sort_by_total_score_desc(self.sneakers)
        elif choice == "总分从低到高":
            self.sneakers = sort_by_total_score_asc(self.sneakers)
        elif choice == "缓震从高到低":
            self.sneakers = sort_by_dimension(self.sneakers, 'cushion', reverse=True)
        elif choice == "抓地从高到低":
            self.sneakers = sort_by_dimension(self.sneakers, 'traction', reverse=True)
        elif choice == "抗扭从高到低":
            self.sneakers = sort_by_dimension(self.sneakers, 'torsion', reverse=True)
        elif choice == "耐磨从高到低":
            self.sneakers = sort_by_dimension(self.sneakers, 'durability', reverse=True)

        self.refresh()

    def open_rating_window(self, sneaker):
        popup = ctk.CTkToplevel(self.root)
        popup.title(f"评分：{sneaker.name}")
        popup.geometry("500x580")
        popup.minsize(500, 580)
        popup.maxsize(500, 580)
        popup.resizable(False, False)

        main_frame = ctk.CTkFrame(popup)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        label = ctk.CTkLabel(main_frame, text=f"{sneaker.brand} - {sneaker.name}", font=("Arial", 16))
        label.pack(pady=10)

        sliders = {}
        slider_labels = {
            "缓震": "cushion",
            "抓地": "traction",
            "抗扭": "torsion",
            "耐磨": "durability"
        }

        from sqlalchemy.orm import joinedload
        with get_db() as db_session:
            sneaker_in_db = db_session.query(Sneaker).options(joinedload(Sneaker.ratings)) \
                .filter(Sneaker.id == sneaker.id).first()
            ratings = sneaker_in_db.ratings
            latest_rating = ratings[-1] if ratings else None

        for cn_label, field in slider_labels.items():
            sub_frame = ctk.CTkFrame(main_frame)
            sub_frame.pack(fill="x", pady=5)

            lbl = ctk.CTkLabel(sub_frame, text=cn_label, width=60)
            lbl.pack(side="left", padx=5)

            slider = ctk.CTkSlider(sub_frame, from_=1, to=100, orientation="horizontal")
            value = getattr(latest_rating, field) if latest_rating else 50
            slider.set(value)

            rating_label = ctk.CTkLabel(sub_frame, text=f"{int(value)}/100", width=40)
            rating_label.pack(side="left", padx=5)

            def make_update_func(label_):
                return lambda val: label_.configure(text=f"{int(val)}/100")

            slider.configure(command=make_update_func(rating_label))
            slider.pack(side="left", expand=True, fill="x")
            sliders[cn_label] = slider

        def submit_rating():
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
        """刷新评分页面"""
        for widget in self.parent_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget != self.sort_menu._canvas.master:
                widget.destroy()

        self.sort_menu.pack(pady=10, anchor="w")
        self.load_sneaker_rating_ui(self.parent_frame,self.sneakers)




