# app/UI_setting_page.py

import customtkinter as ctk

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # 整体深色背景
        self.configure(fg_color="#1e1e2d")

        # —— 标题区 ——
        header = ctk.CTkFrame(self, fg_color="#2d2d44", corner_radius=10)
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            header,
            text="设置",
            font=("微软雅黑", 20, "bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=10)

        # —— 正文区 ——
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # 主题切换
        ctk.CTkLabel(
            body,
            text="主题设置",
            font=("微软雅黑", 16),
            text_color="white"
        ).pack(anchor="w", pady=(0, 5))

        self.theme_switch = ctk.CTkSwitch(
            body,
            text="切换深浅模式",
            command=self.toggle_theme
        )
        self.theme_switch.pack(anchor="w", pady=(0, 20))

        # 根据当前主题状态初始化开关
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

    def toggle_theme(self):
        """在 Light / Dark 之间切换，并同步开关状态"""
        new_mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        if new_mode == "Dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()
