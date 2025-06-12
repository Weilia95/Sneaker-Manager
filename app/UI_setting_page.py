import customtkinter as ctk

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#1e1e2d")  # 深色背景

        title_label = ctk.CTkLabel(self, text="设置页面", font=("微软雅黑", 24, "bold"), text_color="white")
        title_label.pack(pady=30)

        theme_label = ctk.CTkLabel(self, text="主题设置", font=("微软雅黑", 16), text_color="white")
        theme_label.pack(pady=10)

        theme_switch = ctk.CTkSwitch(self, text="切换暗色模式", command=self.toggle_theme)
        theme_switch.pack(pady=10)

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
