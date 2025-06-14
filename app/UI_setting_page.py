import customtkinter as ctk
from tkinter import messagebox

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1e1e2d") # 深色背景

        # ── 第一行：标题栏 ───────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            header,
            text="设置",
            font=("微软雅黑", 20, "bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=10)


        #title_label = ctk.CTkLabel(self, text="设置页面", font=("微软雅黑", 24, "bold"), text_color="white")
        #title_label.pack(pady=30)

        # ── 其余设置内容 ────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        theme_label = ctk.CTkLabel(body, text="主题设置", font=("微软雅黑", 16), text_color="white")
        theme_label.pack(pady=10)

        theme_switch = ctk.CTkSwitch(body, text="切换暗色模式", command=self.toggle_theme)
        theme_switch.pack(pady=10)

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
