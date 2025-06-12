# splash_screen.py
import customtkinter as ctk
from PIL import Image

class SplashScreen:
    def __init__(self, app, image_path, display_time=1660):
        self.app = app
        self.image_path = image_path
        self.display_time = display_time

        # 使用 CTkToplevel 不会冲突
        self.splash = ctk.CTkToplevel()
        self.splash.overrideredirect(True)  # 无边框

        # 加载图片
        self.bg_image = ctk.CTkImage(Image.open(self.image_path), size=(977, 783))
        self.bg_label = ctk.CTkLabel(self.splash, image=self.bg_image, text="")
        self.bg_label.pack()

        # 窗口居中显示
        self.splash.update_idletasks()
        width = 600
        height = 400
        x = (self.splash.winfo_screenwidth() - width) // 2
        y = (self.splash.winfo_screenheight() - height) // 2
        self.splash.geometry(f"{width}x{height}+{x}+{y}")

    def show(self):
        self.splash.after(self.display_time, self.close_splash)

    def close_splash(self):
        self.splash.destroy()
        self.app.deiconify()  # 显示主程序窗口
