import customtkinter as ctk

class SettingsPage:
    def __init__(self, root):
        self.root = root
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # 分割为左右两部分
        self.left_frame = ctk.CTkFrame(self.main_frame, width=100)
        self.left_frame.pack(side="left", fill="y")

        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # 初始化右边的内容
        self.init_right_content()

    def init_right_content(self):
        # 上部：版权声明和程序开发修复日志板块
        top_frame = ctk.CTkFrame(self.right_frame)
        top_frame.pack(side="top", fill="both", expand=True, pady=15, padx=100)

        # 金额单位设置下拉框
        currency_label = ctk.CTkLabel(top_frame, text="选择金额单位:")
        currency_label.pack(pady=10, padx=10)

        currency_options = ["￥", "$", "€", "£"]
        self.currency_var = ctk.StringVar(value=currency_options[0])  # 默认值

        currency_menu = ctk.CTkOptionMenu(top_frame, variable=self.currency_var, values=currency_options)
        currency_menu.pack(pady=10, padx=10)

        # 添加一个保存按钮（如果需要）
        save_button = ctk.CTkButton(top_frame, text="保存设置", command=self.save_settings)
        save_button.pack(pady=10, padx=10)

        # 下部：设置具体内容区域
        bottom_frame = ctk.CTkFrame(self.right_frame)
        bottom_frame.pack(side="bottom", fill="both", expand=True, pady=20, padx=100)

        copyright_label = ctk.CTkLabel(bottom_frame,
                                       text="\n\n© 2023-2025 CJ as a individual software designer. \nAll rights reserved.")
        copyright_label.pack(pady=10, padx=10)

        changelog_label = ctk.CTkLabel(bottom_frame, text="程序更新日志:\n- v0.2 初始版本发布\n- v0.3 current version")
        changelog_label.pack(pady=10, padx=10)

    def save_settings(self):
        selected_currency = self.currency_var.get()
        print(f"已选择金额单位: {selected_currency}")
        # 这里可以添加保存到配置文件或数据库的逻辑