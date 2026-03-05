import tkinter as tk

from config import COLOR_BG
from database.db_manager import DBManager
from ui.login_page import LoginPage
from ui.cashier_page import CashierPage
from ui.manager_page import ManagerPage
from utils.backup import backup_database


class ShopSystem(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("3SSAM MEN'S WEAR - Management System")
        self.state("zoomed")
        self.configure(bg=COLOR_BG)

        self.db = DBManager()
        backup_database()

        container = tk.Frame(self, bg=COLOR_BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.frames["LoginPage"] = LoginPage(container, self)
        self.frames["CashierPage"] = CashierPage(container, self)
        self.frames["ManagerPage"] = ManagerPage(container, self)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "refresh_data"):
            frame.refresh_data()

if __name__ == "__main__":
    app = ShopSystem()
    app.mainloop()