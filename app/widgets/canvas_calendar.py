import tkinter as tk
import calendar
from datetime import datetime

class CanvasCalendar(tk.Frame):
    def __init__(self, master, select_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.select_callback = select_callback
        self.current = datetime.today()
        self.cal = calendar.Calendar(firstweekday=0)  # 周日为第一天

        self.header = tk.Label(self, font=("Arial", 14, "bold"))
        self.header.grid(row=0, column=1, columnspan=5)

        self.prev_btn = tk.Button(self, text="<", command=self.prev_month, width=3)
        self.prev_btn.grid(row=0, column=0)
        self.next_btn = tk.Button(self, text=">", command=self.next_month, width=3)
        self.next_btn.grid(row=0, column=6)

        days = ["Su","Mo","Tu","We","Th","Fr","Sa"]
        for i, d in enumerate(days):
            tk.Label(self, text=d, font=("Arial",10,"bold")).grid(row=1, column=i)

        self.cells = []
        for r in range(6):
            row_cells = []
            for c in range(7):
                cell = tk.Canvas(self, width=40, height=30, bg="white", highlightthickness=1, highlightbackground="#ccc")
                cell.grid(row=r+2, column=c, padx=1, pady=1)
                cell.bind("<Button-1>", lambda e, rr=r, cc=c: self.on_cell_click(rr, cc))
                row_cells.append(cell)
            self.cells.append(row_cells)

        self.draw_month()

    def draw_month(self):
        year, month = self.current.year, self.current.month
        self.header.config(text=self.current.strftime("%B %Y"))
        month_days = list(self.cal.itermonthdays(year, month))
        for idx, day in enumerate(month_days):
            r, c = divmod(idx, 7)
            canvas = self.cells[r][c]
            canvas.delete("all")
            if day == 0:
                continue
            canvas.create_text(20,15, text=str(day))
            canvas.day = day
            canvas.year = year
            canvas.month = month

    def on_cell_click(self, row, col):
        canvas = self.cells[row][col]
        day = getattr(canvas, "day", None)
        if not day: return
        date = datetime(self.current.year, self.current.month, day).date()
        if self.select_callback:
            self.select_callback(date)

    def prev_month(self):
        first = self.current.replace(day=1)
        prev_month = first.month - 1 or 12
        prev_year = first.year - (first.month == 1)
        self.current = first.replace(year=prev_year, month=prev_month)
        self.draw_month()

    def next_month(self):
        first = self.current.replace(day=1)
        next_month = first.month + 1 if first.month < 12 else 1
        next_year = first.year + (first.month == 12)
        self.current = first.replace(year=next_year, month=next_month)
        self.draw_month()
