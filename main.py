
# sneaker_manager/main.py
from app.ui import SneakerApp
from app.database import init_db
import customtkinter as ctk

if __name__ == "__main__":
    init_db()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = SneakerApp()
    app.mainloop()

