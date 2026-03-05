import tkinter as tk
from tkinter import simpledialog, messagebox
import os
from config import COLOR_BG, COLOR_ACCENT, LOGO_FILENAME, ADMIN_PASSWORD

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG)
        self.controller = controller

        center = tk.Frame(self, bg=COLOR_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        if os.path.exists(LOGO_FILENAME):
            try:
                self.logo_img = tk.PhotoImage(file=LOGO_FILENAME)
                tk.Label(center, image=self.logo_img, bg=COLOR_BG).pack(pady=20)
            except:
                tk.Label(center, text="3SSAM", font=("Impact", 48), bg=COLOR_BG, fg="white").pack()
        else:
            tk.Label(center, text="3SSAM", font=("Impact", 48), bg=COLOR_BG, fg="white").pack()

        tk.Label(center, text="3SSAM MEN'S WEAR", font=("Arial", 28, "bold"),
                 bg=COLOR_BG, fg="white").pack(pady=10)
        tk.Label(center, text="نظام إدارة المبيعات والمخزن", font=("Arial", 14),
                 bg=COLOR_BG, fg="#dddddd").pack(pady=5)

        tk.Button(center, text="دخول الكاشير", font=("Arial", 16, "bold"), width=20,
                  bg=COLOR_ACCENT, fg=COLOR_BG,
                  command=lambda: controller.show_frame("CashierPage")).pack(pady=15)

        tk.Button(center, text="دخول المدير", font=("Arial", 16, "bold"), width=20,
                  bg=COLOR_ACCENT, fg=COLOR_BG,
                  command=self.check_password).pack(pady=10)

    def check_password(self):
        pwd = simpledialog.askstring("المدير", "كلمة المرور:", show="*")
        if pwd == ADMIN_PASSWORD:  
            self.controller.show_frame("ManagerPage")
        elif pwd:
            messagebox.showerror("خطأ", "كلمة المرور غير صحيحة")