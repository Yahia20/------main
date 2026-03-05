import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING

class ManagerPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG)
        self.controller = controller
        
        tk.Button(self, text="تسجيل خروج", bg="#c0392b", fg="white", font=("Arial",12,"bold"),
                  command=lambda: controller.show_frame("LoginPage")).pack(anchor="ne", padx=20, pady=10)
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.tab_report = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_report, text="التقارير والتحليل")

        report_canvas = tk.Canvas(self.tab_report, bg=COLOR_PANEL, highlightthickness=0)
        report_scrollbar = ttk.Scrollbar(self.tab_report, orient="vertical", command=report_canvas.yview)
        self.scrollable_report = tk.Frame(report_canvas, bg=COLOR_PANEL)
        
        self.scrollable_report.bind("<Configure>", lambda e: report_canvas.configure(scrollregion=report_canvas.bbox("all")))
        report_canvas.create_window((0, 0), window=self.scrollable_report, anchor="nw", width=1200)
        report_canvas.configure(yscrollcommand=report_scrollbar.set)
        
        report_canvas.pack(side="left", fill="both", expand=True)
        report_scrollbar.pack(side="right", fill="y")

 # --- الإطار الأول (سطر الفلاتر) ---
        frm_filter_inputs = tk.Frame(self.scrollable_report, bg=COLOR_PANEL)
        frm_filter_inputs.pack(fill="x", pady=(15, 5), padx=20)
        
        # --- الإطار الثاني (سطر الأزرار تحته مباشرة) ---
        frm_filter_buttons = tk.Frame(self.scrollable_report, bg=COLOR_PANEL)
        frm_filter_buttons.pack(fill="x", pady=(0, 15), padx=20)
        
        def trigger_update(event=None):
            self.show_report()

        tk.Label(frm_filter_inputs, text="من:", bg=COLOR_PANEL).pack(side="left", padx=(0,2))
        self.ent_from = tk.Entry(frm_filter_inputs, width=11)
        self.ent_from.pack(side="left", padx=2)
        self.ent_from.bind("<Return>", trigger_update)
        
        tk.Label(frm_filter_inputs, text="إلى:", bg=COLOR_PANEL).pack(side="left", padx=(10,2))
        self.ent_to = tk.Entry(frm_filter_inputs, width=11)
        self.ent_to.pack(side="left", padx=2)
        self.ent_to.bind("<Return>", trigger_update)
        
        tk.Label(frm_filter_inputs, text="فلتر منتج:", bg=COLOR_PANEL).pack(side="left", padx=(10,2))
        self.product_combo = ttk.Combobox(frm_filter_inputs, width=15)
        self.product_combo.pack(side="left", padx=2)
        self.product_combo.bind("<<ComboboxSelected>>", trigger_update)
        
        tk.Label(frm_filter_inputs, text="موديل:", bg=COLOR_PANEL).pack(side="left", padx=(10,2))
        self.model_combo = ttk.Combobox(frm_filter_inputs, width=10)
        self.model_combo.pack(side="left", padx=2)
        self.model_combo.bind("<<ComboboxSelected>>", trigger_update)
        
        tk.Label(frm_filter_inputs, text="العملية:", bg=COLOR_PANEL).pack(side="left", padx=(10,2))
        self.trans_filter = ttk.Combobox(frm_filter_inputs, values=["الكل","بيع","مرتجع","تبديل"], width=8)
        self.trans_filter.pack(side="left", padx=2)
        self.trans_filter.bind("<<ComboboxSelected>>", trigger_update)
        
        tk.Label(frm_filter_inputs, text="الدفع:", bg=COLOR_PANEL).pack(side="left", padx=(10,2))
        self.pay_filter = ttk.Combobox(frm_filter_inputs, values=["الكل","كاش","انستاباي","فودافون كاش","فيزا"], width=10)
        self.pay_filter.pack(side="left", padx=2)
        self.pay_filter.bind("<<ComboboxSelected>>", trigger_update)
        
        tk.Label(frm_filter_inputs, text="هاتف:", bg=COLOR_PANEL).pack(side="left", padx=(10,2))
        self.ent_phone_filter = tk.Entry(frm_filter_inputs, width=12)
        self.ent_phone_filter.pack(side="left", padx=2)
        self.ent_phone_filter.bind("<Return>", trigger_update)
        
        # --- وضع الأزرار في السطر الثاني لتكون ظاهرة دائماً ---
        tk.Button(frm_filter_buttons, text="تحديث التقرير", bg=COLOR_ACCENT, fg="white", font=("Arial",11,"bold"), width=15, command=self.show_report).pack(side="left", padx=15)
        tk.Button(frm_filter_buttons, text="تصدير إكسيل (مبسط)", font=("Arial",11), command=self.export_report).pack(side="left", padx=10)
        tk.Button(frm_filter_buttons, text="تصدير حركات مفصلة (Excel)", bg="#27ae60", fg="white", font=("Arial",11,"bold"), command=self.open_detailed_export_window).pack(side="left", padx=10)       
        frm_cost = tk.Frame(self.scrollable_report, bg=COLOR_PANEL)
        frm_cost.pack(fill="x", pady=10, padx=20)
        tk.Label(frm_cost, text="مصروفات ثابتة أخرى:", bg=COLOR_PANEL, font=("Arial",11,"bold")).pack(anchor="w")
        
        tk.Label(frm_cost, text="إيجار:", bg=COLOR_PANEL).pack(side="left", padx=5)
        self.ent_rent = tk.Entry(frm_cost, width=10)
        self.ent_rent.pack(side="left", padx=5)
        self.ent_rent.bind("<KeyRelease>", trigger_update)
        
        tk.Label(frm_cost, text="رواتب:", bg=COLOR_PANEL).pack(side="left", padx=5)
        self.ent_salaries = tk.Entry(frm_cost, width=10)
        self.ent_salaries.pack(side="left", padx=5)
        self.ent_salaries.bind("<KeyRelease>", trigger_update)
        
        tk.Label(frm_cost, text="أخرى:", bg=COLOR_PANEL).pack(side="left", padx=5)
        self.ent_other_cost = tk.Entry(frm_cost, width=10)
        self.ent_other_cost.pack(side="left", padx=5)
        self.ent_other_cost.bind("<KeyRelease>", trigger_update)
        
        self.lbl_stats = tk.Label(self.scrollable_report, text="جاري التحميل...", font=("Arial",13), bg=COLOR_PANEL, justify="left")
        self.lbl_stats.pack(pady=15, anchor="w", padx=30)
        
        self.frm_graph = tk.Frame(self.scrollable_report, bg=COLOR_PANEL)
        self.frm_graph.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tab_stock = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_stock, text="حالة المخزون (الكل)")
        
        search_frame_stock = tk.Frame(self.tab_stock, bg=COLOR_PANEL)
        search_frame_stock.pack(fill="x", padx=20, pady=10)
        tk.Label(search_frame_stock, text="بحث بكود القطعة / الموديل / الاسم:", font=("Arial", 11, "bold"), bg=COLOR_PANEL).pack(side="right", padx=10)
        self.ent_search_stock = tk.Entry(search_frame_stock, font=("Arial", 12), width=30)
        self.ent_search_stock.pack(side="right")
        self.ent_search_stock.bind("<KeyRelease>", self.load_all_stock)

        cols = ("الكود", "الصنف", "الكمية", "السعر", "التكلفة", "المورد", "الحد الأدنى", "موديل")
        self.tree_low = ttk.Treeview(self.tab_stock, columns=cols, show="headings")
        for c in cols: self.tree_low.heading(c, text=c)
        self.tree_low.column("الكود", width=90, anchor="center")
        self.tree_low.column("الكمية", width=100, anchor="center")
        self.tree_low.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tree_low.bind("<Double-1>", self.show_barcode_window)
        
        btnf = tk.Frame(self.tab_stock, bg=COLOR_PANEL)
        btnf.pack(fill="x", padx=20, pady=8)
        tk.Button(btnf, text="+ إضافة منتج جديد", bg=COLOR_SUCCESS, fg="white", font=("Arial",10,"bold"),
                  command=self.open_add_product_window).pack(side="left", padx=5)
        tk.Button(btnf, text="تعديل المنتج", bg=COLOR_ACCENT, fg=COLOR_BG,
                  command=self.open_edit_product).pack(side="left", padx=5)
        tk.Button(btnf, text="حذف المنتج", bg=COLOR_WARNING, fg="white",
                  command=self.delete_product).pack(side="left", padx=5)
        tk.Button(btnf, text="حذف موديل كامل", bg=COLOR_WARNING, fg="white",
                  command=self.delete_whole_model).pack(side="left", padx=5)
                  
        self.tab_critical = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_critical, text="ناقص جداً (1–2 قطعة)")

        search_frame_crit = tk.Frame(self.tab_critical, bg=COLOR_PANEL)
        search_frame_crit.pack(fill="x", padx=20, pady=10)
        tk.Label(search_frame_crit, text="بحث بكود القطعة / الموديل / الاسم:", font=("Arial", 11, "bold"), bg=COLOR_PANEL).pack(side="right", padx=10)
        self.ent_search_crit = tk.Entry(search_frame_crit, font=("Arial", 12), width=30)
        self.ent_search_crit.pack(side="right")
        self.ent_search_crit.bind("<KeyRelease>", self.load_critical_low_stock)

        cols_crit = ("الكود", "الصنف", "الكمية", "المورد", "الحد", "موديل")
        self.tree_critical = ttk.Treeview(self.tab_critical, columns=cols_crit, show="headings")
        for c in cols_crit: self.tree_critical.heading(c, text=c)
        self.tree_critical.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_log = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_log, text="سجل الفواتير")
        cols_log = ("رقم", "التاريخ", "الإجمالي", "الدفع", "النوع")
        self.tree_log = ttk.Treeview(self.tab_log, columns=cols_log, show="headings")
        for c in cols_log: self.tree_log.heading(c, text=c)
        self.tree_log.column("رقم", width=80, anchor="center")
        self.tree_log.pack(fill="both", expand=True, padx=20, pady=20)
        self.tree_log.bind("<Double-1>", self.show_invoice_details)

        self.tab_suppliers = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_suppliers, text="إدارة الموردين")
        cols_sup = ("id", "اسم المورد", "اسم الشحنة", "المدفوع", "الآجل", "الإجمالي")
        self.tree_sup = ttk.Treeview(self.tab_suppliers, columns=cols_sup, show="headings")
        for c in cols_sup: self.tree_sup.heading(c, text=c)
        self.tree_sup.pack(fill="both", expand=True, padx=20, pady=10)
        
        btn_sup = tk.Frame(self.tab_suppliers, bg=COLOR_PANEL)
        btn_sup.pack(fill="x", padx=20, pady=8)
        tk.Button(btn_sup, text="إضافة شحنة جديدة", bg=COLOR_ACCENT, fg=COLOR_BG,
                  command=self.open_add_supplier).pack(side="left", padx=5)
        tk.Button(btn_sup, text="تعديل", bg=COLOR_ACCENT, fg=COLOR_BG,
                  command=self.edit_supplier).pack(side="left", padx=5)
        tk.Button(btn_sup, text="حذف", bg=COLOR_WARNING, fg="white",
                  command=self.delete_supplier).pack(side="left", padx=5)
                  
        self.tab_days = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_days, text="سجل الأيام المغلقة")
        cols_days = ("الجلسة", "البداية", "النهاية", "عدد الفواتير", "المبيعات")
        self.tree_days = ttk.Treeview(self.tab_days, columns=cols_days, show="headings")
        for c in cols_days: self.tree_days.heading(c, text=c)
        self.tree_days.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree_days.bind("<Double-1>", self.show_day_details)
        tk.Button(self.tab_days, text="تحديث", command=self.load_closed_days).pack(pady=5)

        self.tab_customers = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_customers, text="ملفات العملاء")
        
        cols_cust = ("الهاتف", "الاسم", "إجمالي المشتريات", "آخر زيارة", "آخر صنف")
        self.tree_customers = ttk.Treeview(self.tab_customers, columns=cols_cust, show="headings")
        for c in cols_cust: self.tree_customers.heading(c, text=c)
        self.tree_customers.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tree_customers.bind("<Double-1>", self.show_customer_history)
        tk.Button(self.tab_customers, text="تحديث البيانات", command=self.load_customers_data).pack(pady=5)

    def show_barcode_window(self, event):
        sel = self.tree_low.selection()
        if not sel: return
        product_id = self.tree_low.item(sel[0])['values'][0]
        product_name = self.tree_low.item(sel[0])['values'][1]

        try:
            import barcode
            from barcode.writer import ImageWriter
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showerror("نقص في المكتبات", "يرجى فتح الطرفية وتثبيت المكتبات أولاً:\n\npip install python-barcode pillow")
            return

        win = tk.Toplevel(self)
        win.title(f"باركود المنتج: {product_id}")
        win.geometry("400x350")
        win.configure(bg="white")
        win.grab_set()

        try:
            code128 = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            barcode_obj = code128(str(product_id), writer=writer)
            
            import tempfile, os
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"barcode_{product_id}")
            barcode_obj.save(temp_file)
            img_path = f"{temp_file}.png"

            img = Image.open(img_path)
            img = img.resize((280, 140))
            photo = ImageTk.PhotoImage(img)

            tk.Label(win, text=f"الصنف: {product_name}", font=("Arial", 16, "bold"), bg="white").pack(pady=(20, 5))
            lbl_img = tk.Label(win, image=photo, bg="white")
            lbl_img.image = photo 
            lbl_img.pack()
            
            def print_barcode():
                try:
                    import win32print, win32ui
                    from PIL import ImageWin
                    printer_name = win32print.GetDefaultPrinter()
                    hDC = win32ui.CreateDC()
                    hDC.CreatePrinterDC(printer_name)
                    
                    bmp = Image.open(img_path)
                    printer_width = int(hDC.GetDeviceCaps(8))
                    printer_height = int(bmp.size[1] * (printer_width / bmp.size[0]))
                    
                    hDC.StartDoc("Barcode Print")
                    hDC.StartPage()
                    dib = ImageWin.Dib(bmp)
                    dib.draw(hDC.GetHandleOutput(), (0, 0, printer_width, printer_height))
                    hDC.EndPage()
                    hDC.EndDoc()
                    hDC.DeleteDC()
                    messagebox.showinfo("تم", "تم إرسال الباركود للطابعة", parent=win)
                except Exception as e:
                    messagebox.showerror("خطأ في الطباعة", str(e), parent=win)

            tk.Button(win, text="🖨️ طباعة الباركود", font=("Arial", 14, "bold"), bg="#2980b9", fg="white", command=print_barcode).pack(pady=20)

        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء توليد الباركود:\n{e}")

    def show_invoice_details(self, event):
        sel = self.tree_log.selection()
        if not sel: return
        bill_id = self.tree_log.item(sel[0])['values'][0]
        
        bill = self.controller.db.get_bill_by_id(bill_id)
        if not bill: return
        
        items = self.controller.db.get_bill_items(bill_id)
        
        win = tk.Toplevel(self)
        win.title(f"تفاصيل الفاتورة رقم {bill[0]}")
        win.geometry("800x600")
        win.configure(bg=COLOR_PANEL)
        
        info_text = f"رقم الفاتورة: {bill[0]} | التاريخ: {bill[1]}\n"
        info_text += f"طريقة الدفع: {bill[3]} | نوع العملية: {bill[4]}\n"
        
        cust_phone = bill[5] if bill[5] else 'غير مسجل'
        cust_name = bill[6] if bill[6] else 'غير مسجل'
        info_text += f"رقم هاتف العميل: {cust_phone}\nاسم العميل: {cust_name}\n"
        
        if bill[8] > 0:
            info_text += f"الخصم: {bill[7]} (بقيمة {bill[8]:,.2f} ج.م)\n"
        else:
            info_text += "الخصم: لا يوجد\n"
        
        tk.Label(win, text=info_text, font=("Arial", 12, "bold"), bg=COLOR_PANEL, justify="right").pack(pady=15)
        
        tree = ttk.Treeview(win, columns=("كود القطعة", "الموديل", "الصنف", "الكمية", "السعر", "الإجمالي"), show="headings")
        for c in ("كود القطعة", "الموديل", "الصنف", "الكمية", "السعر", "الإجمالي"): 
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        for item in items:
            total_item = item[2] * item[3]
            tree.insert("", "end", values=(item[0], item[4], item[1], item[2], item[3], total_item))
            
        tk.Label(win, text=f"إجمالي الفاتورة (بعد الخصم): {bill[2]:,.2f} ج.م", font=("Arial", 14, "bold"), bg=COLOR_PANEL, fg="red").pack(pady=10)

    def load_customers_data(self):
        for i in self.tree_customers.get_children(): self.tree_customers.delete(i)
        for row in self.controller.db.get_all_customers_report():
            self.tree_customers.insert("", "end", values=row)

    def show_customer_history(self, event):
        sel = self.tree_customers.selection()
        if not sel: return
        
        raw_phone = str(self.tree_customers.item(sel[0])['values'][0])
        phone = raw_phone.zfill(11) if len(raw_phone) == 10 else raw_phone
        cust_name = self.tree_customers.item(sel[0])['values'][1]
        
        transactions = self.controller.db.get_customer_transactions(phone)
        total_purchases = len(transactions)
        
        win = tk.Toplevel(self)
        win.title(f"الملف الشامل للعميل: {cust_name} - {phone}")
        win.geometry("1050x600")
        win.configure(bg=COLOR_PANEL)
        
        header = tk.Frame(win, bg="#34495e", pady=15)
        header.pack(fill="x")
        tk.Label(header, text=f"العميل: {cust_name}", font=("Arial",16,"bold"), bg="#34495e", fg="white").pack(side="right", padx=20)
        tk.Label(header, text=f"عدد العمليات: {total_purchases}", font=("Arial",15,"bold"), bg="#34495e", fg="#f1c40f").pack(side="left", padx=20)
        
        tree_frame = tk.Frame(win, bg=COLOR_PANEL)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        cols = ("التاريخ / الموديل والصنف", "المبلغ / السعر", "الدفع / الكمية", "النوع / الخصم")
        tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings", height=15)
        
        tree.heading("#0", text="رقم الفاتورة / الكود")
        tree.column("#0", width=180, anchor="w")
        
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=170, anchor="center")
            
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        for tr in transactions:
            bill_id, date, total, pay_method, t_type = tr
            full_bill = self.controller.db.get_bill_by_id(bill_id)
            discount_info = ""
            if full_bill and full_bill[8] > 0:
                discount_info = f" (خصم: {full_bill[8]:,.2f}ج)"
                
            parent = tree.insert("", "end", text=f"📄 فاتورة رقم {bill_id}", 
                                 values=(date, f"{total:,.2f} ج.م", pay_method, t_type + discount_info), tags=('invoice',))
            
            items = self.controller.db.get_bill_items(bill_id)
            for it in items:
                tree.insert(parent, "end", text=f"   🏷️ كود: {it[0]}", 
                            values=(f"موديل [{it[4]}] {it[1]}", f"{it[3]:,.2f} ج.م", f"الكمية: {it[2]}", ""))
                
        tree.tag_configure('invoice', background='#dff9fb', font=('Arial', 11, 'bold'))

    def refresh_data(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.ent_from.delete(0, tk.END); self.ent_from.insert(0, today)
        self.ent_to.delete(0, tk.END); self.ent_to.insert(0, today)
        self.load_product_filter()
        self.load_model_filter()
        self.trans_filter.set("الكل")
        self.pay_filter.set("الكل")
        self.show_report()
        self.load_all_stock()
        self.load_critical_low_stock()
        self.load_sales_log()
        self.load_suppliers()
        self.load_closed_days()
        self.load_customers_data()

    def load_product_filter(self):
        prods = self.controller.db.get_all_product_names()
        values = ["الكل"] + [f"{pid} - {name}" for pid, name in prods]
        self.product_combo['values'] = values
        self.product_combo.set("الكل")

    def load_model_filter(self):
        models = self.controller.db.get_unique_model_codes()
        values = ["الكل"] + models
        self.model_combo['values'] = values
        self.model_combo.set("الكل")

    def show_report(self):
        fr = self.ent_from.get().strip()
        to = self.ent_to.get().strip()
        phone = self.ent_phone_filter.get().strip()
        
        if (fr and len(fr) < 10) or (to and len(to) < 10): return

        selected_prod = self.product_combo.get() or "الكل"
        prod_id = selected_prod.split(" - ")[0] if " - " in selected_prod and selected_prod != "الكل" else None
        
        model_f = self.model_combo.get() or "الكل"
        trans_f = self.trans_filter.get() or "الكل"
        pay_f = self.pay_filter.get() or "الكل"
        
        if not fr and not to:
            today = datetime.now().strftime("%Y-%m-%d")
            fr = to = today
        elif not to: to = fr
        elif not fr: fr = to
        
        data = self.controller.db.get_sales_report(fr, to, prod_id, phone, model_f, trans_f, pay_f)
        profit = self.controller.db.get_total_profit(fr, to, prod_id, phone, model_f)
        var_cost = self.controller.db.get_variable_cost(fr, to, model_f)
        
        sales = sum(r[1] for r in data if r[3] == "بيع")
        returns = sum(abs(r[1]) for r in data if r[3] == "مرتجع")
        exchange = sum(abs(r[1]) for r in data if r[3] == "تبديل")
        
        try:
            rent = float(self.ent_rent.get() or 0)
            sal = float(self.ent_salaries.get() or 0)
            oth = float(self.ent_other_cost.get() or 0)
            fixed = rent + sal + oth
        except:
            fixed = 0.0
            
        net_profit = profit - fixed
        contribution = sales - var_cost
        break_even = fixed / (contribution / sales) if sales > 0 and contribution > 0 else 0.0
        
        customer_info = ""
        if phone:
            cust_name = self.controller.db.get_customer_name(phone)
            customer_info = f"\nاسم العميل: {cust_name} (الهاتف: {phone})\n"
            
        pay_dict = {}
        trend_dict = {}
        for r in data:
            if r[3] == "بيع":
                m = r[2]
                pay_dict[m] = pay_dict.get(m, 0) + r[1]
                day = r[0][:10]
                trend_dict[day] = trend_dict.get(day, 0) + r[1]
            
        stats = f"الفترة: {fr} → {to}{customer_info}\n\n"
        stats += f"إجمالي المبيعات      : {sales:>12,.2f} ج.م\n"
        stats += f"إجمالي المرتجعات     : {returns:>12,.2f} ج.م\n"
        stats += f"إجمالي التبديلات     : {exchange:>12,.2f} ج.م\n"
        stats += f"الربح الإجمالي       : {profit:>12,.2f} ج.م\n"
        stats += f"التكلفة المتغيرة     : {var_cost:>12,.2f} ج.م\n"
        stats += f"المصروفات الثابتة   : {fixed:>12,.2f} ج.م\n"
        stats += f"الربح الصافي         : {net_profit:>12,.2f} ج.م\n"
        stats += f"نقطة التعادل (Break Even): {break_even:>12,.2f} ج.م\n"
        
        self.lbl_stats.config(text=stats)
        for w in self.frm_graph.winfo_children(): w.destroy()
        
        if not data:
            tk.Label(self.frm_graph, text="No data available for this period / filter.", font=("Arial", 14), bg=COLOR_PANEL, fg="red").pack(pady=50)
            return

        fig, axs = plt.subplots(3, 2, figsize=(14, 15))
        fig.patch.set_facecolor(COLOR_PANEL)
        
        if pay_dict:
            labels_map = {"كاش": "Cash", "فيزا": "Visa", "انستاباي": "Instapay", "فودافون كاش": "Vodafone"}
            eng_labels = [labels_map.get(k, k) for k in pay_dict.keys()]
            axs[0, 0].bar(eng_labels, pay_dict.values(), color=["#3A4032","#D4AF37","#8e44ad","#2980b9"])
            axs[0, 0].set_title("Sales by Payment Method", fontweight='bold')
            axs[0, 0].set_ylabel("Amount (EGP)")
            axs[0, 0].grid(True, axis='y', alpha=0.3)
        else:
            axs[0, 0].axis('off')
            
        categories = ['Revenue', 'Variable Cost', 'Fixed Cost', 'Net Profit']
        values = [sales, var_cost, fixed, net_profit]
        colors = ['#27ae60', '#e67e22', '#c0392b', '#2980b9']
        axs[0, 1].barh(categories, values, color=colors)
        axs[0, 1].set_title("Break Even Analysis", fontweight='bold')
        axs[0, 1].grid(True, axis='x', alpha=0.3)
        
        if trend_dict:
            sorted_days = sorted(trend_dict.keys())
            trend_vals = [trend_dict[d] for d in sorted_days]
            axs[1, 0].plot(sorted_days, trend_vals, marker='o', linestyle='-', color='#2980b9', linewidth=2)
            axs[1, 0].set_title("Daily Sales Trend", fontweight='bold')
            axs[1, 0].tick_params(axis='x', rotation=45)
            axs[1, 0].grid(True, alpha=0.3)
        else:
            axs[1, 0].axis('off')

        sales_count = len([r for r in data if r[3] == "بيع"])
        returns_count = len([r for r in data if r[3] == "مرتجع"])
        exchange_count = len([r for r in data if r[3] == "تبديل"])

        trans_types = {"Sales": sales_count, "Returns": returns_count, "Exchanges": exchange_count}
        trans_types = {k: v for k, v in trans_types.items() if v > 0}
        
        if trans_types:
            axs[1, 1].pie(trans_types.values(), labels=trans_types.keys(), autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c', '#f39c12'], startangle=140)
            axs[1, 1].set_title("Transactions Breakdown (By Count)", fontweight='bold')
        else:
            axs[1, 1].axis('off')

        top_models = self.get_top_selling_models(5)
        if top_models:
            m_names = [str(m[0] or m[1])[:10] for m in top_models]
            m_qty = [m[2] for m in top_models]
            axs[2, 0].bar(m_names, m_qty, color='#9b59b6')
            axs[2, 0].set_title("Top 5 Selling Models", fontweight='bold')
            axs[2, 0].set_ylabel("Quantity Sold")
        else:
            axs[2, 0].axis('off')

        top_cust = self.get_top_customers(5)
        if top_cust:
            c_names = [str(c[0] or c[1])[:15] for c in top_cust]
            c_spent = [c[2] for c in top_cust]
            axs[2, 1].bar(c_names, c_spent, color='#34495e')
            axs[2, 1].set_title("Top 5 Customers", fontweight='bold')
            axs[2, 1].set_ylabel("Total Spent (EGP)")
            axs[2, 1].tick_params(axis='x', rotation=15)
        else:
            axs[2, 1].axis('off')

        fig.tight_layout(pad=3.0)
        canvas = FigureCanvasTkAgg(fig, master=self.frm_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_report(self):
        fr = self.ent_from.get().strip()
        to = self.ent_to.get().strip()
        phone = self.ent_phone_filter.get().strip()
        selected_prod = self.product_combo.get()
        prod_id = selected_prod.split(" - ")[0] if " - " in selected_prod and selected_prod != "الكل" else None
        model_f = self.model_combo.get()
        trans_f = self.trans_filter.get()
        pay_f = self.pay_filter.get()
        
        data = self.controller.db.get_sales_report(fr, to, prod_id, phone, model_f, trans_f if trans_f != "الكل" else None, pay_f if pay_f != "الكل" else None)
        if not data:
            messagebox.showinfo("لا بيانات", "لا توجد فواتير لتصديرها")
            return
            
        file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")])
        if file:
            self.controller.db.export_report_to_excel(data, file)
            messagebox.showinfo("تم", "تم حفظ التقرير بصيغة إكسيل")

    # --- التعديل المذهل: نافذة خيارات التصدير المفصل للمدير ---
    def open_detailed_export_window(self):
        win = tk.Toplevel(self)
        win.title("خيارات التصدير المفصل")
        win.geometry("500x350")
        win.configure(bg=COLOR_PANEL)
        win.grab_set()

        tk.Label(win, text="اختر طريقة فلترة التقرير المفصل:", font=("Arial", 14, "bold"), bg=COLOR_PANEL).pack(pady=15)

        var_choice = tk.StringVar(value="date")

        tk.Radiobutton(win, text="حسب الفترة الزمنية (من - إلى المحددة بالخلفية)", variable=var_choice, value="date", font=("Arial", 12), bg=COLOR_PANEL).pack(anchor="e", padx=30, pady=5)
        
        frame_sess = tk.Frame(win, bg=COLOR_PANEL)
        frame_sess.pack(fill="x", padx=40, pady=5)
        tk.Radiobutton(frame_sess, text="حسب رقم جلسة محدد:", variable=var_choice, value="session_id", font=("Arial", 12), bg=COLOR_PANEL).pack(side="right")
        ent_sess = tk.Entry(frame_sess, font=("Arial", 12), width=10, justify="center")
        ent_sess.pack(side="right", padx=10)

        frame_n = tk.Frame(win, bg=COLOR_PANEL)
        frame_n.pack(fill="x", padx=40, pady=5)
        tk.Radiobutton(frame_n, text="لآخر عدد من الجلسات المغلقة:", variable=var_choice, value="last_n", font=("Arial", 12), bg=COLOR_PANEL).pack(side="right")
        ent_n = tk.Entry(frame_n, font=("Arial", 12), width=10, justify="center")
        ent_n.pack(side="right", padx=10)

        def do_export():
            choice = var_choice.get()
            data = []
            report_name = "Detailed_Report"
            
            if choice == "date":
                fr = self.ent_from.get().strip()
                to = self.ent_to.get().strip()
                if not fr or not to:
                    messagebox.showwarning("تنبيه", "يرجى تحديد فترة زمنية في الخلفية أولاً", parent=win)
                    return
                data = self.controller.db.get_detailed_transactions_report(fr, to)
                report_name += f"_{fr}_to_{to}"
                
            elif choice == "session_id":
                sid = ent_sess.get().strip()
                if not sid.isdigit(): 
                    return messagebox.showwarning("خطأ", "يرجى إدخال رقم جلسة صحيح", parent=win)
                data = self.controller.db.get_detailed_transactions_by_session(int(sid))
                report_name += f"_Session_{sid}"
                
            elif choice == "last_n":
                n = ent_n.get().strip()
                if not n.isdigit(): 
                    return messagebox.showwarning("خطأ", "يرجى إدخال عدد صحيح (مثال: 5)", parent=win)
                data = self.controller.db.get_detailed_transactions_last_n_sessions(int(n))
                report_name += f"_Last_{n}_Sessions"

            if not data:
                messagebox.showinfo("لا بيانات", "لا توجد حركات مطابقة للبحث", parent=win)
                return

            file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")], initialfile=f"{report_name}.xlsx")
            if not file: return

            try:
                import pandas as pd
                cols = ["رقم الفاتورة", "التاريخ", "رقم الجلسة", "نوع العملية", "طريقة الدفع",
                        "هاتف العميل", "اسم العميل", "إجمالي الفاتورة", "نوع الخصم", "قيمة الخصم",
                        "كود المنتج", "اسم المنتج", "الكمية", "سعر القطعة", "كود الموديل"]
                df = pd.DataFrame(data, columns=cols)
                df.to_excel(file, index=False)
                messagebox.showinfo("نجاح", "تم تصدير التقرير المفصل بنجاح!", parent=win)
                win.destroy()
            except ImportError:
                messagebox.showerror("نقص مكتبات", "لتشغيل التصدير للإكسيل يرجى كتابة الأمر التالي في الطرفية:\npip install pandas openpyxl", parent=win)

        tk.Button(win, text="📥 استخراج التقرير (Export)", bg="#27ae60", fg="white", font=("Arial", 14, "bold"), command=do_export).pack(pady=25)
    # -------------------------------------------------------------

    def load_all_stock(self, *args):
        search_term = ""
        if hasattr(self, 'ent_search_stock'):
            search_term = self.ent_search_stock.get().strip()
            
        for i in self.tree_low.get_children(): self.tree_low.delete(i)
        rows = self.controller.db.get_all_stock(search_term)
        for r in rows:
            self.tree_low.insert("", "end", values=r)

    def load_critical_low_stock(self, *args):
        search_term = ""
        if hasattr(self, 'ent_search_crit'):
            search_term = self.ent_search_crit.get().strip()
            
        for i in self.tree_critical.get_children(): self.tree_critical.delete(i)
        rows = self.controller.db.get_critical_low_stock(search_term)
        for r in rows: 
            self.tree_critical.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], r[5]), tags=('critical',))
        self.tree_critical.tag_configure('critical', foreground='red', font=('Arial', 10, 'bold'))

    def load_sales_log(self):
        for i in self.tree_log.get_children(): self.tree_log.delete(i)
        self.controller.db.cursor.execute("""
            SELECT bill_id, date, total, payment_method, transaction_type
            FROM sales ORDER BY bill_id DESC LIMIT 200
        """)
        for row in self.controller.db.cursor.fetchall():
            self.tree_log.insert("", "end", values=row)

    def load_suppliers(self):
        for i in self.tree_sup.get_children(): self.tree_sup.delete(i)
        rows = self.controller.db.get_all_suppliers()
        for r in rows:
            total = r[5] if r[5] else r[3] + r[4]
            self.tree_sup.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], total))

    def load_closed_days(self):
        for i in self.tree_days.get_children(): self.tree_days.delete(i)
        for row in self.controller.db.get_closed_days():
            self.tree_days.insert("", "end", values=row)

    def show_day_details(self, event=None):
        sel = self.tree_days.selection()
        if not sel: return
        sess_id = self.tree_days.item(sel[0])['values'][0]
        bills = self.controller.db.get_bills_by_session(sess_id)
        
        win = tk.Toplevel(self)
        win.title(f"تفاصيل اليوم - جلسة {sess_id}")
        win.geometry("850x550")
        
        tk.Label(win, text=f"فواتير الجلسة رقم {sess_id} (إجمالي {len(bills)} فاتورة)", font=("Arial",14,"bold")).pack(pady=10)
        
        tree = ttk.Treeview(win, columns=("رقم الفاتورة (الكود)", "التاريخ", "الإجمالي", "النوع", "طريقة الدفع"), show="headings")
        for c in ("رقم الفاتورة (الكود)", "التاريخ", "الإجمالي", "النوع", "طريقة الدفع"): 
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        total_cash = 0
        for b in bills:
            full_bill = self.controller.db.get_bill_by_id(b[0])
            pay_method = full_bill[3] if full_bill else "غير معروف"
            tree.insert("", "end", values=(b[0], b[1], b[2], b[3], pay_method))
            if b[3] == "بيع": total_cash += b[2]
            elif b[3] == "مرتجع": total_cash -= abs(b[2])
            
        tk.Label(win, text=f"صافي إيرادات الجلسة: {total_cash:,.2f} ج.م", font=("Arial", 14, "bold"), fg="green").pack(pady=10)

    def open_add_supplier(self):
        win = tk.Toplevel(self)
        win.title("إضافة شحنة جديدة")
        win.geometry("500x300")
        win.configure(bg=COLOR_BG)
        win.grab_set()
        fields = ["اسم المورد", "اسم الشحنة", "المدفوع (ج.م)", "الآجل (ج.م)"]
        entries = {}
        for i, lab in enumerate(fields):
            tk.Label(win, text=lab + ":", bg=COLOR_BG, fg="white").pack(pady=8)
            ent = tk.Entry(win, width=40)
            ent.pack()
            entries[lab] = ent
        def save():
            try:
                name = entries["اسم المورد"].get().strip()
                order_name = entries["اسم الشحنة"].get().strip()
                paid = float(entries["المدفوع (ج.م)"].get() or 0)
                debt = float(entries["الآجل (ج.م)"].get() or 0)
                self.controller.db.add_supplier_shipment(name, order_name, paid, debt)
                messagebox.showinfo("تم", "تم إضافة الشحنة")
                win.destroy()
                self.load_suppliers()
            except Exception as e:
                messagebox.showerror("خطأ", str(e))
        tk.Button(win, text="حفظ الشحنة", bg=COLOR_ACCENT, fg=COLOR_BG, command=save).pack(pady=20)

    def edit_supplier(self):
        sel = self.tree_sup.selection()
        if not sel: return
        sid = self.tree_sup.item(sel[0])['values'][0]
        messagebox.showinfo("تعديل", "يمكن تعديل الصف من خلال قاعدة البيانات مباشرة أو توسيع النظام")

    def delete_supplier(self):
        sel = self.tree_sup.selection()
        if not sel: return
        sid = self.tree_sup.item(sel[0])['values'][0]
        if messagebox.askyesno("حذف", f"حذف الشحنة رقم {sid}؟"):
            self.controller.db.delete_supplier(sid)
            self.load_suppliers()

    def open_add_product_window(self, product=None):
        win = tk.Toplevel(self)
        win.title("إضافة موديل جديد (مع قطع متعددة)")
        win.geometry("900x750")
        win.configure(bg=COLOR_BG)
        win.grab_set()
        
        upper = tk.LabelFrame(win, text="بيانات الموديل (مشتركة لكل القطع)", bg=COLOR_BG, fg=COLOR_ACCENT, font=("Arial",12,"bold"))
        upper.pack(fill="x", padx=20, pady=10)
        model_fields = [
            ("اسم المنتج", tk.Entry), ("كود الموديل", tk.Entry), ("النوع", tk.Entry),
            ("سعر البيع (للموديل كله)", tk.Entry), ("سعر التكلفة (للموديل كله)", tk.Entry), ("اسم المورد", tk.Entry)
        ]
        model_entries = {}
        for i, (lab, wtype) in enumerate(model_fields):
            f = tk.Frame(upper, bg=COLOR_BG)
            f.pack(fill="x", padx=30, pady=6)
            tk.Label(f, text=lab + ":", bg=COLOR_BG, fg="white", font=("Arial",11)).pack(side="left")
            ent = wtype(f, width=35, font=("Arial",11))
            ent.pack(side="right")
            model_entries[lab] = ent
            
        lower = tk.LabelFrame(win, text="القطع / الألوان / المقاسات (يمكن إضافة عدة صفوف)", bg=COLOR_BG, fg=COLOR_ACCENT, font=("Arial",12,"bold"))
        lower.pack(fill="both", expand=True, padx=20, pady=10)
        
        var_f = tk.Frame(lower, bg=COLOR_BG)
        var_f.pack(fill="x", padx=10, pady=5)
        
        cols_var = ("كود المنتج (7 حروف)", "اللون", "المقاس", "الكمية")
        var_entries = {}
        for lab in cols_var:
            tk.Label(var_f, text=lab + ":", bg=COLOR_BG, fg="white").pack(side="left", padx=5)
            ent = tk.Entry(var_f, width=15)
            ent.pack(side="left", padx=5)
            var_entries[lab] = ent
            
        added_variants = []
        tree_var = ttk.Treeview(lower, columns=cols_var, show="headings", height=8)
        
        def add_variant_row():
            try:
                pid = var_entries["كود المنتج (7 حروف)"].get().strip().upper()
                if len(pid) != 7: raise ValueError("كود 7 حروف فقط")
                color = var_entries["اللون"].get().strip()
                size = var_entries["المقاس"].get().strip().upper()
                qty = int(var_entries["الكمية"].get())
                tree_var.insert("", "end", values=(pid, color, size, qty))
                added_variants.append((pid, color, size, qty))
                for e in var_entries.values(): e.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("خطأ", str(e))
                
        tk.Button(var_f, text="إضافة القطعة", bg=COLOR_ACCENT, fg=COLOR_BG, font=("Arial", 10, "bold"), command=add_variant_row).pack(side="left", padx=15)
        
        for c in cols_var: tree_var.heading(c, text=c)
        tree_var.pack(fill="both", expand=True, padx=10, pady=10)
        
        def finish_model():
            try:
                name = model_entries["اسم المنتج"].get().strip()
                model_code = model_entries["كود الموديل"].get().strip()
                typ = model_entries["النوع"].get().strip()
                price = float(model_entries["سعر البيع (للموديل كله)"].get())
                cost = float(model_entries["سعر التكلفة (للموديل كله)"].get())
                supplier = model_entries["اسم المورد"].get().strip()
                
                if not added_variants:
                    messagebox.showwarning("ناقص", "أضف على الأقل قطعة واحدة")
                    return
                for pid, color, size, qty in added_variants:
                    values = (pid, name, color, typ, size, price, cost, supplier, qty, 3, model_code)
                    success = self.controller.db.add_new_product(values)
                    if not success:
                        messagebox.showerror("فشل", f"فشل إضافة {pid}")
                        return
                messagebox.showinfo("تم", f"تم إضافة الموديل {model_code} بنجاح مع {len(added_variants)} قطعة")
                win.destroy()
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("خطأ", str(e))
                
        tk.Button(lower, text="تم - حفظ كل القطع للموديل", font=("Arial",13,"bold"), bg=COLOR_SUCCESS, fg="white", width=30, command=finish_model).pack(pady=10)

    def open_edit_product(self):
        sel = self.tree_low.selection()
        if not sel: return
        pid = self.tree_low.item(sel[0])['values'][0]
        full = self.controller.db.get_product_by_id(pid)
        
        if full:
            win = tk.Toplevel(self)
            win.title("تعديل منتج")
            win.geometry("520x680")
            win.configure(bg=COLOR_BG)
            win.grab_set()
            tk.Label(win, text="تعديل المنتج", font=("Arial",16,"bold"), bg=COLOR_BG, fg=COLOR_ACCENT).pack(pady=15)
            
            fields = [
                ("كود المنتج (7 أحرف بالضبط)", tk.Entry), ("اسم المنتج", tk.Entry),
                ("اللون", tk.Entry), ("النوع", tk.Entry), ("المقاس (حتى 3 حروف)", tk.Entry),
                ("السعر (جنيه)", tk.Entry), ("سعر التكلفة (جنيه)", tk.Entry),
                ("اسم المورد", tk.Entry), ("الكمية", tk.Entry),
            ]
            entries = {}
            for label_text, widget_type in fields:
                frame = tk.Frame(win, bg=COLOR_BG)
                frame.pack(fill="x", padx=30, pady=8)
                tk.Label(frame, text=label_text + ":", font=("Arial",11), bg=COLOR_BG, fg="white").pack(side="left")
                ent = widget_type(frame, font=("Arial",12), width=30)
                ent.pack(side="right")
                entries[label_text] = ent
                
            entries["كود المنتج (7 أحرف بالضبط)"].insert(0, full[0])
            entries["كود المنتج (7 أحرف بالضبط)"].config(state="readonly")
            entries["اسم المنتج"].insert(0, full[1])
            entries["اللون"].insert(0, full[2])
            entries["النوع"].insert(0, full[3])
            entries["المقاس (حتى 3 حروف)"].insert(0, full[4])
            entries["السعر (جنيه)"].insert(0, full[5])
            entries["سعر التكلفة (جنيه)"].insert(0, full[6])
            entries["اسم المورد"].insert(0, full[7])
            entries["الكمية"].insert(0, full[8])
            
            def save_product():
                try:
                    name = entries["اسم المنتج"].get().strip()
                    color = entries["اللون"].get().strip()
                    typ = entries["النوع"].get().strip()
                    size = entries["المقاس (حتى 3 حروف)"].get().strip().upper()
                    price = float(entries["السعر (جنيه)"].get().strip())
                    cost_price = float(entries["سعر التكلفة (جنيه)"].get().strip())
                    supplier = entries["اسم المورد"].get().strip()
                    qty = int(entries["الكمية"].get().strip())
                    model_code = full[10] if len(full) > 10 else ""
                    
                    values = (name, color, typ, size, price, cost_price, supplier, qty, 3, model_code)
                    if self.controller.db.update_product(full[0], values):
                        messagebox.showinfo("تم", "تم التعديل بنجاح")
                        win.destroy()
                        self.refresh_data()
                except Exception as e: 
                    messagebox.showerror("خطأ", str(e))
                    
            tk.Button(win, text="حفظ التعديل", font=("Arial",13,"bold"), bg=COLOR_ACCENT, fg=COLOR_BG, width=25, height=2,
                      command=save_product).pack(pady=30)

    def delete_product(self):
        sel = self.tree_low.selection()
        if not sel: return
        pid = self.tree_low.item(sel[0])['values'][0]
        if messagebox.askyesno("حذف", f"حذف المنتج {pid}؟"):
            if self.controller.db.delete_product(pid):
                messagebox.showinfo("تم", "تم الحذف")
                self.load_all_stock()

    def delete_whole_model(self):
        model_code = simpledialog.askstring("حذف موديل", "أدخل كود الموديل المراد حذفه كاملاً:")
        if model_code and messagebox.askyesno("تأكيد", f"حذف كل قطع الموديل {model_code}؟"):
            if self.controller.db.delete_model(model_code):
                messagebox.showinfo("تم", "تم حذف الموديل كاملاً")
                self.load_all_stock()

    def get_sales_by_payment_method(self, start_date, end_date):
        self.controller.db.cursor.execute("""
            SELECT payment_method, SUM(total) FROM sales 
            WHERE date BETWEEN ? AND ? GROUP BY payment_method
        """, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        return self.controller.db.cursor.fetchall()

    def get_daily_sales_trend(self, start_date, end_date):
        self.controller.db.cursor.execute("""
            SELECT strftime('%Y-%m-%d', date) as day, SUM(total) FROM sales 
            WHERE date BETWEEN ? AND ? AND transaction_type='بيع'
            GROUP BY day ORDER BY day ASC
        """, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        return self.controller.db.cursor.fetchall()

    def get_top_selling_models(self, limit=10):
        self.controller.db.cursor.execute("""
            SELECT p.model_code, p.name, SUM(si.qty) as total_qty 
            FROM sale_items si JOIN products p ON si.product_id = p.id 
            GROUP BY p.model_code ORDER BY total_qty DESC LIMIT ?
        """, (limit,))
        return self.controller.db.cursor.fetchall()

    def get_top_customers(self, limit=20):
        self.controller.db.cursor.execute("""
            SELECT name, phone, total_spent FROM customers 
            ORDER BY total_spent DESC LIMIT ?
        """, (limit,))
        return self.controller.db.cursor.fetchall()