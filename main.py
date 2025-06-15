from app.database import init_db
import customtkinter as ctk
from app.splash_screen import SplashScreen
from app.ui import SneakerApp

if __name__ == "__main__":
    # 初始化数据库
    init_db()

    # 在任何 CTk 窗口创建之前，先禁用自动 DPI 识别
    ctk.deactivate_automatic_dpi_awareness()

    # （可选）锁定为 100% 缩放，防止你自己设置 widget/window_scaling 也被 DPI 打断
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    # 初始化主题
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # 创建主程序，但先不显示
    app = SneakerApp()
    app.withdraw()  # 隐藏主窗口

    # 显示 splash，关闭后显示主程序
    splash = SplashScreen(app, image_path="app/assets/splash_image.png", display_time=1995)
    splash.show()

    # 启动主循环
    app.mainloop()
