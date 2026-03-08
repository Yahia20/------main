import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import re
from config import COLOR_BG, COLOR_HEADER, COLOR_PANEL, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING
from utils.receipt import print_receipt

class CashierPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG)
        self.controller = controller
        self.cart = []
        self.active_session_id = None
        self.selected_product = None
        self.current_results = []

        self.style = ttk.Style()
        if "clam" in self.style.theme_names(): self.style.theme_use('clam')
        self.style.configure("Treeview", background="white", foreground="black", fieldbackground="white", font=("Arial", 11), rowheight=28)

        hdr = tk.Frame(self, bg=COLOR_HEADER, height=70)
        hdr.pack(fill="x")
        
        tk.Button(hdr, text="← خروج", bg="#c0392b", fg="white", font=("Arial",11,"bold"),
                  command=lambda: controller.show_frame("LoginPage")).pack(side="left", padx=15, pady=12)
        
        self.btn_start_day = tk.Button(hdr, text="▶ ابدأ اليوم", bg="#27ae60", fg="white", font=("Arial",12,"bold"), command=self.action_start_day)
        self.btn_start_day.pack(side="left", padx=5)
        
        self.btn_end_day = tk.Button(hdr, text="■ اختم اليوم", bg="#e74c3c", fg="white", font=("Arial",12,"bold"), command=self.action_end_day)
        
        tk.Label(hdr, text="3SSAM POS - نظام مبيعات احترافي", font=("Arial",18,"bold"), bg=COLOR_HEADER, fg="white").pack(side="right", padx=20, pady=12)

        main_container = tk.Frame(self, bg=COLOR_BG)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1) 
        main_container.grid_columnconfigure(1, weight=1) 
        main_container.grid_rowconfigure(0, weight=1)

        left_wrapper = tk.Frame(main_container, bg=COLOR_PANEL)
        left_wrapper.grid(row=0, column=0, sticky="nsew", padx=(0,10))

        canvas = tk.Canvas(left_wrapper, bg=COLOR_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_wrapper, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=COLOR_PANEL)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=550) 
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(self.scrollable_frame, text="السلة الحالية", font=("Arial",14,"bold"), bg=COLOR_PANEL, fg="#333").pack(pady=5)

        cols = ("كود القطعة", "الموديل", "الصنف", "الكمية", "السعر", "الإجمالي")
        self.tree_cart = ttk.Treeview(self.scrollable_frame, columns=cols, show="headings", height=8)
        for c in cols: 
            self.tree_cart.heading(c, text=c)
            self.tree_cart.column(c, anchor="center", width=80)
        self.tree_cart.pack(fill="x", padx=10)

        self.btn_delete_item = tk.Button(self.scrollable_frame, text="🗑️ حذف الصنف المحدد", bg="#e74c3c", fg="white", 
                                         font=("Arial", 10), command=self.remove_item)
        self.btn_delete_item.pack(anchor="e", padx=15, pady=5)

        input_f = tk.LabelFrame(self.scrollable_frame, text="بيانات العميل (إجباري)", bg=COLOR_PANEL, font=("Arial",10,"bold"))
        input_f.pack(fill="x", padx=20, pady=10)

        tk.Label(input_f, text=":رقم الهاتف (11 رقم)", bg=COLOR_PANEL).grid(row=0, column=1, sticky="e", pady=5)
        self.ent_phone = tk.Entry(input_f, width=25, font=("Arial",11)); self.ent_phone.grid(row=0, column=0, pady=5, padx=10)

        tk.Label(input_f, text=":اسم العميل", bg=COLOR_PANEL).grid(row=1, column=1, sticky="e", pady=5)
        self.ent_name = tk.Entry(input_f, width=25, font=("Arial",11)); self.ent_name.grid(row=1, column=0, pady=5, padx=10)

        tools_f = tk.Frame(self.scrollable_frame, bg=COLOR_PANEL)
        tools_f.pack(fill="x", padx=20)

        self.payment_var = tk.StringVar(value="كاش")
        pay_f = tk.Frame(tools_f, bg=COLOR_PANEL); pay_f.pack(pady=5)
        for p in ["كاش", "انستاباي", "فودافون كاش", "فيزا"]:
            tk.Radiobutton(pay_f, text=p, variable=self.payment_var, value=p, bg=COLOR_PANEL).pack(side="left", padx=10)

        self.discount_type = tk.StringVar(value="بدون خصم")
        self.discount_combo = ttk.Combobox(tools_f, textvariable=self.discount_type, state="readonly", width=30,
                                           values=["بدون خصم", "خصم مخصص", "عرض القطعة والتانية هدية", "عرض 2 عليهم 3", "عرض 4 عليهم 7"])
        self.discount_combo.pack(pady=5)
        self.ent_discount = tk.Entry(tools_f, width=30); self.ent_discount.pack()

        self.lbl_total = tk.Label(self.scrollable_frame, text="الإجمالي: 0.00 ج.م", font=("Arial",22,"bold"), fg=COLOR_SUCCESS, bg=COLOR_PANEL)
        self.lbl_total.pack(pady=10)

        self.btn_checkout = tk.Button(self.scrollable_frame, text="دفع وطباعة الفاتورة (Enter)", font=("Arial", 16, "bold"), 
                                      bg=COLOR_HEADER, fg="white", height=2, command=self.checkout)
        self.btn_checkout.pack(fill="x", padx=40, pady=10)

        reprint_f = tk.Frame(self.scrollable_frame, bg="#bdc3c7", pady=10)
        reprint_f.pack(fill="x", padx=40, pady=20)
        tk.Label(reprint_f, text="إعادة طباعة فاتورة قديمة:", bg="#bdc3c7", font=("Arial",9,"bold")).pack()
        self.ent_reprint_id = tk.Entry(reprint_f, width=15, justify="center"); self.ent_reprint_id.pack(pady=5)
        tk.Button(reprint_f, text="طباعة", bg="#34495e", fg="white", command=self.action_reprint).pack()

        right_panel = tk.Frame(main_container, bg=COLOR_PANEL, relief="flat")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10,0))
        
        tk.Label(right_panel, text="البحث عن منتج", font=("Arial",15,"bold"), bg=COLOR_PANEL).pack(pady=15)
        self.search_var = tk.StringVar()
        self.combo_search = ttk.Combobox(right_panel, textvariable=self.search_var, font=("Arial",14), width=45)
        self.combo_search.pack(pady=5, padx=20)
        self.combo_search.bind("<KeyRelease>", self.on_search_key)
        self.combo_search.bind("<<ComboboxSelected>>", self.on_select_item)

        ops_f = tk.Frame(right_panel, bg=COLOR_PANEL)
        ops_f.pack(pady=15)
        tk.Button(ops_f, text="📦 مرتجع / استبدال شامل", bg="#f39c12", fg="white", font=("Arial",14,"bold"), 
                  padx=30, pady=15, command=self.open_refund_exchange_window).pack()

        tk.Label(right_panel, text="الكمية:", font=("Arial",12), bg=COLOR_PANEL).pack()
        self.ent_qty = tk.Entry(right_panel, font=("Arial",16), width=8, justify="center"); self.ent_qty.insert(0, "1")
        self.ent_qty.pack(pady=5)

        tk.Button(right_panel, text="إضافة للسلة", font=("Arial",14,"bold"), bg=COLOR_HEADER, fg="white", width=25, command=self.add_selected_item).pack(pady=15)

        self.lbl_item_details = tk.Label(right_panel, text="", font=("Arial",12, "bold"), bg=COLOR_PANEL, fg="#1a237e", justify="center")
        self.lbl_item_details.pack(pady=10)

        self.lbl_cash_drawer = tk.Label(right_panel, text="الخزنة الآن: 0.00 ج.م", font=("Arial",18,"bold"), bg="#2c3e50", fg="#f1c40f", pady=10)
        self.lbl_cash_drawer.pack(side="bottom", fill="x")

    def validate_customer(self):
        phone = self.ent_phone.get().strip()
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("بيان ناقص", "يجب إدخال اسم العميل")
            return False
        if not re.match(r"^\d{11}$", phone):
            messagebox.showwarning("خطأ في الهاتف", "يجب إدخال رقم هاتف مكون من 11 رقم")
            return False
        return True

    def refresh_data(self):
        active = self.controller.db.get_active_session()
        self.active_session_id = active
        self.enable_sales_ui(bool(active))
        self.update_cash_display()

    def update_cash_display(self):
        total = self.controller.db.get_session_total_sales(self.active_session_id)
        self.lbl_cash_drawer.config(text=f"الخزنة الآن: {total:,.2f} ج.م")

    def enable_sales_ui(self, enable=True):
        state = "normal" if enable else "disabled"
        self.btn_checkout.config(state=state)
        self.combo_search.config(state=state)
        if enable:
            self.btn_start_day.pack_forget(); self.btn_end_day.pack(side="left", padx=5)
        else:
            self.btn_end_day.pack_forget(); self.btn_start_day.pack(side="left", padx=5)

    def action_start_day(self):
        self.active_session_id = self.controller.db.start_new_day()
        messagebox.showinfo("تم", "بدأ يوم جديد - بالتوفيق!")
        self.refresh_data()

    def action_end_day(self):
        total = self.controller.db.get_session_total_sales(self.active_session_id)
        if messagebox.askyesno("قفل اليوم", f"إجمالي الخزنة المتوقع: {total:,.2f} ج.م\nتأكيد إغلاق الجلسة؟"):
            self.controller.db.end_current_day()
            self.controller.show_frame("LoginPage")

    def on_search_key(self, event=None):
        if event and event.keysym in ('Up', 'Down', 'Return', 'Left', 'Right'): return
        term = self.search_var.get().strip()
        
        if not term or " | كود:" in term: return

        results = self.controller.db.search_products(term)
        self.current_results = results
        self.combo_search['values'] = [f"{n} | {s} | {p}ج | كود: {i} | موديل: {mc}" for i,n,s,p,q,c,mc in results]
        if results and event and event.keysym != 'BackSpace': 
            self.combo_search.event_generate("<Down>")

    def on_select_item(self, event=None):
        val = self.search_var.get()
        if "كود: " in val:
            try:
                pid = val.split("كود: ")[1].split(" |")[0].strip()
                res = self.controller.db.get_product_by_id(pid)
                
                if res:
                    mapped_res = (res[0], res[1], res[4], res[5], res[8], res[2], res[10])
                    self.selected_product = mapped_res
                    self.lbl_item_details.config(text=f"الاسم: {mapped_res[1]} | مقاس: {mapped_res[2]} | لون: {mapped_res[5]}\nمتبقي: {mapped_res[4]} قطعة | كود الموديل: {mapped_res[6]}")
            except Exception as e:
                print("Selection Error:", e)

    def add_selected_item(self, qty_override=None):
        if not self.selected_product: return
        try:
            qty = qty_override or int(self.ent_qty.get())
            p = self.selected_product
            self.cart.append({"id": p[0], "name": p[1], "qty": qty, "price": p[3], "total": qty * p[3], "model_code": p[6], "size": p[2]})
            self.update_cart_display()
        except: messagebox.showerror("خطأ", "الكمية غير صحيحة")

    def remove_item(self):
        sel = self.tree_cart.selection()
        if sel:
            idx = self.tree_cart.index(sel[0])
            self.cart.pop(idx); self.update_cart_display()

    def update_cart_display(self):
        for i in self.tree_cart.get_children(): self.tree_cart.delete(i)
        gross = sum(i["total"] for i in self.cart)
        net, disc = self.calculate_net_total(gross)
        for i in self.cart:
            self.tree_cart.insert("", "end", values=(i["id"], i["model_code"], i["name"], i["qty"], i["price"], i["total"]))
        self.lbl_total.config(text=f"الإجمالي: {net:,.2f} ج.م")

    def calculate_net_total(self, gross):
        dtype = self.discount_type.get()
        if dtype == "بدون خصم": return gross, 0.0
        if dtype == "خصم مخصص":
            try:
                v = self.ent_discount.get().strip()
                d = gross * (float(v[:-1])/100) if v.endswith('%') else float(v)
                return gross - d, d
            except: return gross, 0.0
        ps = []
        for i in self.cart: ps.extend([i['price']] * i['qty'])
        ps.sort(reverse=True)
        r, p = {"عرض القطعة والتانية هدية":(2,1), "عرض 2 عليهم 3":(5,3), "عرض 4 عليهم 7":(11,7)}.get(dtype, (0,0))
        if r > 0 and len(ps) == r:
            net = sum(ps[:p]); return net, gross - net
        return gross, 0.0

    def checkout(self):
        if not self.cart: return
        if not self.validate_customer(): return
        
        dtype = self.discount_type.get()
        total_qty = sum(i['qty'] for i in self.cart)

        if dtype == "عرض القطعة والتانية هدية" and total_qty != 2:
            messagebox.showerror("خطأ في العرض", "عرض 'القطعة والتانية هدية' يتطلب وجود قطعتين بالضبط في السلة (ادفع 1 وخذ 1 هدية).")
            return
        elif dtype == "عرض 2 عليهم 3" and total_qty != 5:
            messagebox.showerror("خطأ في العرض", "عرض '2 عليهم 3' يتطلب وجود 5 قطع بالضبط في السلة.")
            return
        elif dtype == "عرض 4 عليهم 7" and total_qty != 11:
            messagebox.showerror("خطأ في العرض", "عرض '4 عليهم 7' يتطلب وجود 11 قطعة بالضبط في السلة.")
            return

        gross = sum(i['total'] for i in self.cart)
        final_total, disc = self.calculate_net_total(gross)
        
        bid, dt = self.controller.db.save_transaction(
            self.cart, final_total, self.payment_var.get(), "بيع",
            self.ent_phone.get(), self.ent_name.get(), self.active_session_id,
            discount_type=self.discount_type.get(), discount_amount=disc
        )
        
        print_receipt(self, bid, dt, final_total, self.payment_var.get(), "بيع", discount=disc, discount_type=self.discount_type.get())
        messagebox.showinfo("تم", "تمت العملية بنجاح")
        self.cart.clear(); self.update_cart_display(); self.update_cash_display()

    def action_reprint(self):
        bid = self.ent_reprint_id.get().strip()
        if not bid: return
        bill = self.controller.db.get_bill_by_id(bid)
        if bill:
            items = self.controller.db.get_bill_items(bid)
            temp_cart = []
            
            for i in items:
                qty = i[2]
                name = i[1]
                if qty < 0:
                    name = f"(مرتجع) {name}"
                    
                temp_cart.append({
                    "id": i[0], 
                    "name": name, 
                    "qty": qty, 
                    "price": i[3], 
                    "total": qty * i[3], 
                    "model_code": i[4] if len(i) > 4 else "---"
                })
            
            old_cart = self.cart
            old_name = self.ent_name.get()
            
            self.cart = temp_cart
            self.ent_name.delete(0, tk.END)
            if len(bill) > 6 and bill[6]:
                self.ent_name.insert(0, bill[6])
                
            discount_val = bill[8] if len(bill) > 8 else 0
            discount_type_val = bill[7] if len(bill) > 7 else "بدون خصم"
            
            print_receipt(self, bill[0], bill[1], bill[2], bill[3], bill[4], discount=discount_val, discount_type=discount_type_val)
            
            self.cart = old_cart
            self.ent_name.delete(0, tk.END)
            self.ent_name.insert(0, old_name)
            self.update_cart_display()
            
        else: 
            messagebox.showerror("خطأ", "رقم فاتورة غير موجود")

    # =========================================================================
    # نافذة المرتجع والاستبدال (الذكية الشاملة للعروض)
    # =========================================================================
    def open_refund_exchange_window(self):
        win = tk.Toplevel(self)
        win.title("نظام المرتجعات والاستبدال الشامل والمستقل")
        win.geometry("1250x800")
        win.configure(bg="#ecf0f1")
        win.grab_set()
        
        win.old_cart = []
        win.new_cart = []
        win.target_bill = None
        win.target_discount_type = "بدون خصم"
        win.cust_phone = ""
        win.cust_name = ""
        win.final_net = 0

        top_f = tk.Frame(win, bg="#34495e", pady=15)
        top_f.pack(fill="x")
        tk.Label(top_f, text="إدارة المرتجعات والاستبدال", font=("Arial", 16, "bold"), bg="#34495e", fg="white").pack(side="right", padx=20)
        
        search_f = tk.Frame(top_f, bg="#34495e")
        search_f.pack(side="left", padx=20)
        tk.Label(search_f, text=":رقم الفاتورة القديمة", font=("Arial", 12), bg="#34495e", fg="white").pack(side="right", padx=5)
        ent_bid = tk.Entry(search_f, font=("Arial",14), width=12)
        ent_bid.pack(side="right", padx=5)

        lbl_bill_info = tk.Label(win, text="يرجى إدخال رقم الفاتورة للبدء", font=("Arial", 12, "bold"), bg="#ecf0f1", fg="#2980b9", justify="center")
        lbl_bill_info.pack(pady=10)

        work_f = tk.Frame(win, bg="#ecf0f1")
        work_f.pack(fill="both", expand=True, padx=20, pady=10)
        work_f.grid_columnconfigure(0, weight=1)
        work_f.grid_columnconfigure(1, weight=1)

        right_panel = tk.LabelFrame(work_f, text="القطع القابلة للاسترجاع", font=("Arial", 12, "bold"), bg="white")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=10)
        
        tree_old = ttk.Treeview(right_panel, columns=("كود", "اسم", "المتبقي للاسترجاع", "سعر", "الكمية المرتجعة"), show="headings", height=8)
        for c in ("كود", "اسم", "المتبقي للاسترجاع", "سعر", "الكمية المرتجعة"): tree_old.heading(c, text=c)
        tree_old.pack(fill="both", expand=True, padx=10, pady=10)

        def add_to_return():
            sel = tree_old.selection()
            if not sel: return
            item = tree_old.item(sel[0])['values']
            max_qty = int(item[2])
            
            qty = simpledialog.askinteger("كمية المرتجع", f"الكمية المراد إرجاعها (بحد أقصى {max_qty}):", maxvalue=max_qty, minvalue=1, parent=win)
            if not qty: return
            
            tree_old.set(sel[0], column="الكمية المرتجعة", value=qty)
            
            existing = next((x for x in win.old_cart if x['id'] == str(item[0])), None)
            if existing: existing['qty'] = qty; existing['total'] = qty * float(item[3])
            else: win.old_cart.append({"id": str(item[0]), "name": item[1], "qty": qty, "price": float(item[3]), "total": qty * float(item[3])})
            update_totals()

        tk.Button(right_panel, text="تحديد كمرتجع ⬇", bg="#e74c3c", fg="white", font=("Arial", 11, "bold"), command=add_to_return).pack(pady=10)

        left_panel = tk.LabelFrame(work_f, text="القطع البديلة (الجديدة للعميل)", font=("Arial", 12, "bold"), bg="white")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=10)

        search_new_f = tk.Frame(left_panel, bg="white")
        search_new_f.pack(fill="x", padx=10, pady=10)
        tk.Label(search_new_f, text="بحث منتج:", bg="white").pack(side="right")
        ex_search_var = tk.StringVar()
        combo_new = ttk.Combobox(search_new_f, textvariable=ex_search_var, width=30)
        combo_new.pack(side="right", padx=10)
        
        ex_results = []
        def on_ex_search(event):
            term = ex_search_var.get().strip()
            res = self.controller.db.search_products(term)
            ex_results.clear()
            ex_results.extend(res)
            combo_new['values'] = [f"{n} | {p}ج | كود: {i}" for i,n,s,p,q,c,mc in res]
            if res: combo_new.event_generate("<Down>")

        combo_new.bind("<KeyRelease>", on_ex_search)

        tree_new = ttk.Treeview(left_panel, columns=("كود", "اسم", "كمية", "سعر", "الإجمالي"), show="headings", height=6)
        for c in ("كود", "اسم", "كمية", "سعر", "الإجمالي"): tree_new.heading(c, text=c)
        tree_new.pack(fill="both", expand=True, padx=10, pady=10)

        def add_to_new():
            if win.target_discount_type == "خصم مخصص":
                messagebox.showerror("مرفوض", "لا يمكن استبدال منتجات فاتورة تحتوي على 'خصم مخصص'. يمكنك فقط إرجاع الفاتورة بالكامل.", parent=win)
                return

            idx = combo_new.current()
            if idx < 0 or idx >= len(ex_results): return
            p = ex_results[idx]
            qty = simpledialog.askinteger("الكمية", "أدخل الكمية المطلوبة:", minvalue=1, initialvalue=1, parent=win)
            if not qty: return
            
            item_total = qty * float(p[3])
            win.new_cart.append({"id": str(p[0]), "name": p[1], "qty": qty, "price": float(p[3]), "total": item_total})
            tree_new.insert("", "end", values=(p[0], p[1], qty, p[3], item_total))
            update_totals()

        tk.Button(search_new_f, text="أضف للبدائل ➕", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), command=add_to_new).pack(side="left")

        bottom_f = tk.Frame(win, bg="#ecf0f1", pady=20)
        bottom_f.pack(fill="x")

        lbl_total_old = tk.Label(bottom_f, text="إجمالي المرتجع: 0.00 ج.م", font=("Arial", 14, "bold"), fg="#c0392b", bg="#ecf0f1", width=35)
        lbl_total_old.pack(side="right", padx=10)
        
        lbl_total_new = tk.Label(bottom_f, text="إجمالي الجديد: 0.00 ج.م", font=("Arial", 14, "bold"), fg="#27ae60", bg="#ecf0f1", width=35)
        lbl_total_new.pack(side="left", padx=10)

        lbl_net = tk.Label(bottom_f, text="الصافي: 0.00 ج.م", font=("Arial", 18, "bold"), bg="#f39c12", fg="white", padx=20, pady=10)
        lbl_net.pack(side="bottom", pady=20)

        # دالة حساب الصافي المتقدمة للعروض والخصومات
        def update_totals():
            if not win.target_bill: return
            orig_net = float(win.target_bill[2])
            
            all_orig_items = self.controller.db.get_returnable_items(win.target_bill[0])
            total_orig_qty = sum(x[2] for x in all_orig_items)
            returned_qty = sum(x['qty'] for x in win.old_cart)

            if win.target_discount_type == "خصم مخصص":
                if returned_qty == total_orig_qty and total_orig_qty > 0:
                    lbl_total_old.config(text=f"إرجاع الفاتورة بالكامل: {orig_net:,.2f} ج.م")
                    lbl_total_new.config(text="-- لا يوجد استبدال --")
                    lbl_net.config(text=f"المطلوب رده للعميل: {orig_net:,.2f} ج.م", bg="#27ae60")
                    win.final_net = -orig_net
                else:
                    lbl_total_old.config(text="* يجب تحديد كافة القطع للإرجاع الكامل *")
                    lbl_total_new.config(text="-- لا يوجد استبدال --")
                    lbl_net.config(text="المرتجع الجزئي للخصم المخصص غير مسموح", bg="#e74c3c")
                    win.final_net = None
                    
            elif win.target_discount_type in ["عرض القطعة والتانية هدية", "عرض 2 عليهم 3", "عرض 4 عليهم 7"]:
                if not win.new_cart and not win.old_cart:
                    lbl_total_old.config(text="إجمالي المرتجع: 0.00 ج.م")
                    lbl_total_new.config(text="إجمالي الجديد: 0.00 ج.م")
                    lbl_net.config(text="خالص (لا يوجد فرق مالي)", bg="#34495e")
                    win.final_net = 0
                    return
                
                # حالة الإرجاع فقط بدون تبديل
                if not win.new_cart and win.old_cart:
                    if returned_qty == total_orig_qty and total_orig_qty > 0:
                        lbl_total_old.config(text=f"قيمة إرجاع العرض بالكامل: {orig_net:,.2f} ج.م")
                        lbl_net.config(text=f"المطلوب رده للعميل: {orig_net:,.2f} ج.م", bg="#27ae60")
                        win.final_net = -orig_net
                    else:
                        lbl_total_old.config(text="* يجب إرجاع كافة قطع العرض *")
                        lbl_net.config(text="لا يمكن إرجاع أجزاء من العرض بدون استبدال", bg="#e74c3c")
                        win.final_net = None
                
                # حالة الاستبدال داخل العرض (حساب السلة الافتراضية)
                else:
                    returned_dict = {x['id']: x['qty'] for x in win.old_cart}
                    v_prices = []
                    for it in all_orig_items:
                        rem_q = it[2] - returned_dict.get(str(it[0]), 0)
                        v_prices.extend([it[3]] * rem_q)
                    for x in win.new_cart:
                        v_prices.extend([x['price']] * x['qty'])
                        
                    req_qty = {"عرض القطعة والتانية هدية":2, "عرض 2 عليهم 3":5, "عرض 4 عليهم 7":11}.get(win.target_discount_type, 0)
                    pay_qty = {"عرض القطعة والتانية هدية":1, "عرض 2 عليهم 3":3, "عرض 4 عليهم 7":7}.get(win.target_discount_type, 0)
                    
                    if len(v_prices) == req_qty:
                        v_prices.sort(reverse=True)
                        new_net = sum(v_prices[:pay_qty])
                        diff = new_net - orig_net
                        
                        lbl_total_old.config(text=f"المدفوع مسبقاً للعرض: {orig_net:,.2f} ج.م")
                        lbl_total_new.config(text=f"قيمة السلة الجديدة: {new_net:,.2f} ج.م")
                        
                        win.final_net = diff
                        if diff > 0:
                            lbl_net.config(text=f"المطلوب من العميل دفعه فارق: {diff:,.2f} ج.م", bg="#e74c3c")
                        elif diff < 0:
                            lbl_net.config(text=f"المطلوب رده للعميل: {abs(diff):,.2f} ج.م", bg="#27ae60")
                        else:
                            lbl_net.config(text="خالص (لا يوجد فرق مالي في الاستبدال)", bg="#34495e")
                    else:
                        lbl_total_old.config(text="---")
                        lbl_total_new.config(text="---")
                        lbl_net.config(text=f"إجمالي القطع المتبقية+الجديدة لا يكمل العرض (مطلوب {req_qty})", bg="#e74c3c")
                        win.final_net = None
            else:
                # عمليات عادية بدون عروض
                t_old = sum(x['total'] for x in win.old_cart)
                t_new = sum(x['total'] for x in win.new_cart)
                net = t_new - t_old
                win.final_net = net
                
                lbl_total_old.config(text=f"إجمالي المرتجع: {t_old:,.2f} ج.م")
                lbl_total_new.config(text=f"إجمالي الجديد: {t_new:,.2f} ج.م")
                
                if net > 0:
                    lbl_net.config(text=f"المطلوب من العميل دفعه: {net:,.2f} ج.م", bg="#e74c3c")
                elif net < 0:
                    lbl_net.config(text=f"المطلوب رده للعميل: {abs(net):,.2f} ج.م", bg="#27ae60")
                else:
                    lbl_net.config(text="خالص (لا يوجد فرق مالي)", bg="#34495e")

        def search_old_bill(event=None):
            bid = ent_bid.get().strip()
            bill = self.controller.db.get_bill_by_id(bid)
            if not bill: 
                messagebox.showerror("خطأ", "رقم الفاتورة غير صحيح", parent=win)
                return
            
            bill_date = datetime.strptime(bill[1], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - bill_date).days > 30:
                messagebox.showerror("مرفوض", "عذراً، لقد مر أكثر من 30 يوماً على هذه الفاتورة. لا يمكن إرجاعها أو استبدالها.", parent=win)
                return
            
            items = self.controller.db.get_returnable_items(bid)
            if not items:
                messagebox.showinfo("معلومة", "هذه الفاتورة تم إرجاع جميع منتجاتها مسبقاً ولا يوجد بها قطع قابلة للاسترجاع.", parent=win)
                return

            win.target_bill = bill
            win.cust_phone = bill[5]
            win.cust_name = bill[6]
            win.target_discount_type = bill[7] if len(bill) > 7 else "بدون خصم"
            
            info_text = f"الفاتورة #{bill[0]} | العميل: {win.cust_name} ({win.cust_phone}) | السداد: {bill[3]}\nحالة العروض: {win.target_discount_type}"
            
            if win.target_discount_type == "خصم مخصص":
                lbl_bill_info.config(text=info_text + "\n(تنبيه: مرتجع كامل فقط - لا يمكن الاستبدال)", fg="red")
            elif win.target_discount_type != "بدون خصم":
                lbl_bill_info.config(text=info_text + "\n(تنبيه: سيتم حساب فارق الاستبدال بناءً على شروط العرض الأصلي)", fg="#f39c12")
            else:
                lbl_bill_info.config(text=info_text, fg="#2980b9")
            
            for i in tree_old.get_children(): tree_old.delete(i)
            for i in tree_new.get_children(): tree_new.delete(i)
            win.old_cart.clear()
            win.new_cart.clear()
            update_totals()
            
            for it in items:
                tree_old.insert("", "end", values=(it[0], it[1], it[2], it[3], 0))

        tk.Button(search_f, text="بحث", bg="#f1c40f", font=("Arial", 11, "bold"), command=search_old_bill).pack(side="right")
        ent_bid.bind("<Return>", search_old_bill)

        def finalize_exchange():
            if not win.old_cart and not win.new_cart:
                messagebox.showwarning("تنبيه", "يجب تحديد مرتجعات أو بدائل لإتمام العملية", parent=win)
                return
                
            if win.final_net is None:
                messagebox.showerror("خطأ", "يوجد خطأ في مطابقة شروط العرض أو الخصم. راجع الرسالة التحذيرية بالأسفل.", parent=win)
                return
                
            pay_method = self.payment_var.get()
            
            if messagebox.askyesno("تأكيد", "هل أنت متأكد من تنفيذ هذه العملية؟", parent=win):
                bid, dt = self.controller.db.process_exchange(
                    win.old_cart, win.new_cart, win.final_net, pay_method, win.cust_phone, win.cust_name, self.active_session_id, 
                    original_bill_id=win.target_bill[0], discount_type=win.target_discount_type
                )
                
                temp_cart = []
                for item in win.old_cart:
                    temp_cart.append({
                        "id": item["id"],
                        "name": f"(مرتجع) {item['name']}",
                        "qty": -item['qty'],
                        "price": item['price'],
                        "total": -(item['qty'] * item['price'])
                    })
                for item in win.new_cart:
                    temp_cart.append({
                        "id": item["id"],
                        "name": item['name'],
                        "qty": item['qty'],
                        "price": item['price'],
                        "total": item['qty'] * item['price']
                    })
                
                old_cart = self.cart
                old_name = self.ent_name.get()
                
                self.cart = temp_cart
                self.ent_name.delete(0, tk.END)
                if win.cust_name: self.ent_name.insert(0, win.cust_name)
                
                tr_type = "مرتجع" if not win.new_cart else "تبديل"
                
                print_receipt(self, bid, dt, win.final_net, pay_method, tr_type, discount=0, discount_type=win.target_discount_type)
                
                self.cart = old_cart
                self.ent_name.delete(0, tk.END)
                self.ent_name.insert(0, old_name)
                
                messagebox.showinfo("نجاح", f"تم تنفيذ العملية بنجاح وتسجيلها برقم {bid} وتم طباعة الفاتورة.", parent=win)
                self.update_cash_display()
                win.destroy()

        tk.Button(win, text="✔️ تأكيد العملية النهائية للمرتجع/البدل والطباعة", font=("Arial", 16, "bold"), bg="#2980b9", fg="white", width=40, height=2, command=finalize_exchange).pack(side="bottom", pady=20)