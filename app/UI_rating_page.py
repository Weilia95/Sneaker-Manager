import customtkinter as ctk
from .repositories.sneaker_repository import SneakerRepository
from .database import get_db
from tkinter import messagebox
from .models import Sneaker

class RatingPage:
    def __init__(self, root):
        self.root = root
        self.page_frame = ctk.CTkFrame(self.root)
        self.page_frame.pack(fill="both", expand=True)
        self.parent_frame = self.page_frame  # 确保 refresh 能正确引用
        self.load_sneaker_rating_ui(self.page_frame)

    def load_sneaker_rating_ui(self, parent_frame):
        with get_db() as db_session:
            sneakers = SneakerRepository.get_all(db_session)

        for sneaker in sneakers:
            frame = ctk.CTkFrame(parent_frame)
            frame.pack(fill="x", pady=5, padx=10)

            label = ctk.CTkLabel(frame, text=f"{sneaker.brand} - {sneaker.name}")
            label.pack(side="left", padx=5)

            button = ctk.CTkButton(frame, text="评分", command=lambda s=sneaker: self.open_rating_window(s))
            button.pack(side="right", padx=5)

    def open_rating_window(self, sneaker):
        popup = ctk.CTkToplevel(self.root)
        popup.title(f"评分：{sneaker.name}")
        popup.geometry("500x580")
        popup.minsize(500, 580)
        popup.maxsize(500, 580)
        popup.resizable(False, False)

        # 添加主容器并带外边距
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

            slider = ctk.CTkSlider(
                sub_frame,
                from_=1,
                to=100,
                orientation="horizontal"
            )
            value = getattr(latest_rating, field) if latest_rating else 50
            slider.set(value)

            rating_label = ctk.CTkLabel(sub_frame, text=f"{int(value)}/100", width=40)
            rating_label.pack(side="left", padx=5)

            def make_update_func(label_):
                return lambda val: label_.configure(text=f"{int(val)}/100")

            slider.configure(command=make_update_func(rating_label))
            slider.pack(side="left", expand=True, fill="x")
            # ⭐️ 关键点：用中文键保存滑块对象到 sliders 字典中
            sliders[cn_label] = slider

        def submit_rating():
            with get_db() as db_session:
                SneakerRepository.add_rating(
                    db_session,
                    sneaker.id,
                    sliders["缓震"].get(),
                    sliders["抓地"].get(),
                    sliders["抗扭"].get(),
                    sliders["耐磨"].get()
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
            widget.destroy()
        self.load_sneaker_rating_ui(self.parent_frame)
