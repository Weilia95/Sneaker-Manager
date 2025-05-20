
# sneaker_manager/main.py
from app.ui import SneakerApp
from app.database import init_db  # ✅ 导入初始化函数
import customtkinter as ctk

if __name__ == "__main__":
    init_db()  # ✅ 在程序启动前初始化数据库
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = SneakerApp()
    app.mainloop()

