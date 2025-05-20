# 👟 Sneaker Manager 球鞋使用管理程序

一个使用 Python 开发的桌面应用程序，帮助用户记录、管理和可视化球鞋的使用情况。项目采用现代化界面库 `customtkinter`，并支持图像上传、数据库存储与未来的使用统计图表功能。
updated on 2025/5/21

---

## 🚀 功能特性

✅ 已实现功能：

- 新增球鞋信息（品牌、系列、名称、图片等）
- 上传球鞋图片，直观展示每一双球鞋
- 使用 SQLite 数据库存储球鞋信息
- 现代化美观界面：基于 `customtkinter`

🛠️ 计划中功能：

- 编辑 / 删除球鞋信息
- 添加使用记录（日期、场地、活动等）
- 数据可视化：用 pyecharts 绘制使用频率、品牌统计等图表
- 切换为 SQLAlchemy 管理数据库，提升扩展性
- 多字段筛选 / 搜索功能
- 数据导出为 Excel / CSV

---

## 🖼️ 项目截图

👉 *To be uploaded LOL*

---

## ⚙️ 技术栈

- **语言**：Python 3.x
- **GUI**：customtkinter
- **图像处理**：Pillow
- **数据库**：SQLite（未来将支持 SQLAlchemy）
- **图表**：pyecharts（开发中）

---

## 💻 安装与运行方式

```bash
# 克隆项目
git clone https://github.com/你的用户名/Sneaker-Manager.git
cd Sneaker-Manager

# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
python main.py

---

