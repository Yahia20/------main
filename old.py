import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import os
import tempfile
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import shutil
# محاولة استيراد pandas للتصدير إلى إكسيل (سهل التثبيت: pip install pandas openpyxl)
try:
    import pandas as pd
except ImportError:
    pd = None
# ────────────────────────────────────────────────
# إعدادات الهوية البصرية
# ────────────────────────────────────────────────
COLOR_BG      = "#3A4032"
COLOR_HEADER  = "#2B3026"
COLOR_ACCENT  = "#D4AF37"
COLOR_TEXT    = "#FFFFFF"
COLOR_PANEL   = "#F5F5F5"
COLOR_WARNING = "#e74c3c"
COLOR_SUCCESS = "#27ae60"
# مسار اللوجو وقاعدة البيانات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_FILENAME = os.path.join(BASE_DIR, "logo.png")
DB_NAME = os.path.join(BASE_DIR, "3ssam_store.db")
# ────────────────────────────────────────────────
# 1. طبقة قاعدة البيانات (مع التحديثات الجديدة)
# ────────────────────────────────────────────────
class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.check_and_update_schema()  # تحديث الجداول القديمة لو وجدت
    def create_tables(self):
        # جدول المنتجات (تم إضافة model_code)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                             id TEXT PRIMARY KEY CHECK(length(id)=7),
                             name TEXT, color TEXT, type TEXT,
                             size TEXT CHECK(length(size)<=3),
                             price REAL, cost_price REAL DEFAULT 0,
                             supplier TEXT, qty INTEGER, min_limit INTEGER DEFAULT 3,
                             model_code TEXT)''')
        # جدول الموردين (تم إضافة paid)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             name TEXT, order_name TEXT, qty INTEGER,
                             total_price REAL, debt REAL DEFAULT 0, paid REAL DEFAULT 0)''')
        # جدول العملاء
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
                             phone TEXT PRIMARY KEY, name TEXT,
                             last_item TEXT, total_spent REAL DEFAULT 0,
                             last_date TEXT)''')
        # جدول الجلسات اليومية
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS daily_sessions (
                             session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             start_time TEXT,
                             end_time TEXT,
                             status TEXT DEFAULT 'OPEN')''')
        # جدول المبيعات (تم إضافة original_bill_id)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
                             bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             date TEXT,
                             total REAL,
                             payment_method TEXT,
                             transaction_type TEXT,
                             customer_phone TEXT,
                             session_id INTEGER,
                             original_bill_id INTEGER DEFAULT NULL)''')
        # جدول عناصر الفاتورة
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sale_items (
                             bill_id INTEGER, product_id TEXT,
                             qty INTEGER, price REAL,
                             FOREIGN KEY(bill_id) REFERENCES sales(bill_id))''')
        self.conn.commit()
    def check_and_update_schema(self):
        """تحديث قاعدة البيانات القديمة لإضافة الأعمدة الجديدة دون فقد البيانات"""
        try:
            self.cursor.execute("PRAGMA table_info(products)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if 'model_code' not in columns:
                self.cursor.execute("ALTER TABLE products ADD COLUMN model_code TEXT")
            
            self.cursor.execute("PRAGMA table_info(sales)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if 'original_bill_id' not in columns:
                self.cursor.execute("ALTER TABLE sales ADD COLUMN original_bill_id INTEGER DEFAULT NULL")
            
            self.cursor.execute("PRAGMA table_info(suppliers)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if 'paid' not in columns:
                self.cursor.execute("ALTER TABLE suppliers ADD COLUMN paid REAL DEFAULT 0")
            
            self.conn.commit()
        except Exception as e:
            print(f"Schema Update Error: {e}")
    # ─── إدارة اليوم (Sessions) ───
    def start_new_day(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("UPDATE daily_sessions SET status='CLOSED', end_time=? WHERE status='OPEN'", (now,))
        self.cursor.execute("INSERT INTO daily_sessions (start_time, status) VALUES (?, 'OPEN')", (now,))
        self.conn.commit()
        return self.cursor.lastrowid
    def end_current_day(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("UPDATE daily_sessions SET status='CLOSED', end_time=? WHERE status='OPEN'", (now,))
        self.conn.commit()
    def get_active_session(self):
        self.cursor.execute("SELECT session_id FROM daily_sessions WHERE status='OPEN' ORDER BY session_id DESC LIMIT 1")
        res = self.cursor.fetchone()
        return res[0] if res else None
    # ─── المنتجات ───
    def add_new_product(self, values):
        try:
            self.cursor.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?)", values)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            if "CHECK constraint failed" in str(e):
                messagebox.showerror("خطأ", "الكود يجب أن يكون 7 أرقام والمقاس لا يزيد عن 3 أحرف")
            else:
                messagebox.showerror("خطأ", "هذا الكود موجود بالفعل")
            return False
    def update_product(self, pid, values):
        try:
            self.cursor.execute("""UPDATE products 
                                 SET name=?, color=?, type=?, size=?, price=?, cost_price=?, 
                                     supplier=?, qty=?, min_limit=?, model_code=? 
                                 WHERE id=?""", (*values, pid))
            self.conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التعديل:\n{e}")
            return False
    def delete_product(self, pid):
        try:
            self.cursor.execute("DELETE FROM products WHERE id=?", (pid,))
            self.conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الحذف:\n{e}")
            return False
    def delete_model(self, model_code):
        try:
            self.cursor.execute("DELETE FROM products WHERE model_code=?", (model_code,))
            self.conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حذف الموديل:\n{e}")
            return False
    def get_critical_low_stock(self):
        self.cursor.execute("SELECT name, qty, supplier, min_limit FROM products WHERE qty IN (1, 2) ORDER BY qty ASC")
        return self.cursor.fetchall()
    def get_product_by_id(self, pid):
        self.cursor.execute("SELECT * FROM products WHERE id = ?", (pid,))
        return self.cursor.fetchone()
    def search_products(self, term):
        term = f"%{term}%"
        self.cursor.execute("""
            SELECT id, name, size, price, qty 
            FROM products 
            WHERE id LIKE ? OR name LIKE ?
            ORDER BY name
            LIMIT 15
        """, (term, term))
        return self.cursor.fetchall()
    def get_all_stock(self):
        self.cursor.execute("""
            SELECT id, name, qty, price, cost_price, supplier, min_limit, model_code 
            FROM products ORDER BY qty ASC
        """)
        return self.cursor.fetchall()
    def get_all_product_names(self):
        self.cursor.execute("SELECT id, name FROM products ORDER BY name")
        return self.cursor.fetchall()
    # ─── الموردين الجديد ───
    def add_supplier_shipment(self, name, order_name, paid, debt):
        total_price = paid + debt
        self.cursor.execute("""
            INSERT INTO suppliers (name, order_name, qty, total_price, debt, paid)
            VALUES (?, ?, 0, ?, ?, ?)
        """, (name, order_name, total_price, debt, paid))
        self.conn.commit()
        return self.cursor.lastrowid
    def get_all_suppliers(self):
        self.cursor.execute("SELECT id, name, order_name, paid, debt, total_price FROM suppliers")
        return self.cursor.fetchall()
    def update_supplier(self, sid, name, order_name, paid, debt):
        total_price = paid + debt
        self.cursor.execute("""
            UPDATE suppliers SET name=?, order_name=?, paid=?, debt=?, total_price=?
            WHERE id=?
        """, (name, order_name, paid, debt, total_price, sid))
        self.conn.commit()
    def delete_supplier(self, sid):
        self.cursor.execute("DELETE FROM suppliers WHERE id=?", (sid,))
        self.conn.commit()
    # ─── المبيعات (معدلة مع original_bill_id) ───
    def save_transaction(self, items, total, method, trans_type, customer_phone="", customer_name="", session_id=None, original_bill_id=None):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_total = total
        self.cursor.execute("""
            INSERT INTO sales (date, total, payment_method, transaction_type, customer_phone, session_id, original_bill_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date_str, final_total, method, trans_type, customer_phone, session_id, original_bill_id))
        bill_id = self.cursor.lastrowid
        for item in items:
            self.cursor.execute("INSERT INTO sale_items VALUES (?, ?, ?, ?)",
                                (bill_id, item['id'], item['qty'], item['price']))
            qty_change = item['qty']
            if trans_type == "بيع":
                self.cursor.execute("UPDATE products SET qty = qty - ? WHERE id = ?", (qty_change, item['id']))
            elif trans_type == "مرتجع":
                self.cursor.execute("UPDATE products SET qty = qty + ? WHERE id = ?", (qty_change, item['id']))
            elif trans_type == "تبديل":
                direction = 1 if item.get('return', False) else -1
                self.cursor.execute("UPDATE products SET qty = qty + ? WHERE id = ?", (direction * qty_change, item['id']))
        if customer_phone:
            self.cursor.execute("SELECT * FROM customers WHERE phone=?", (customer_phone,))
            if self.cursor.fetchone():
                self.cursor.execute("""
                    UPDATE customers SET total_spent = total_spent + ?, last_date = ?, last_item = ?, name = COALESCE(?, name)
                    WHERE phone = ?
                """, (final_total, date_str, items[0]['name'], customer_name, customer_phone))
            else:
                self.cursor.execute("""
                    INSERT INTO customers (phone, name, last_item, total_spent, last_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (customer_phone, customer_name or "عميل جديد", items[0]['name'], final_total, date_str))
        self.conn.commit()
        return bill_id, date_str
    # ─── دوال جديدة للمرتجع والاستبدال ───
    def get_bill_by_id(self, bill_id):
        self.cursor.execute("SELECT * FROM sales WHERE bill_id=?", (bill_id,))
        return self.cursor.fetchone()
    def get_bill_items(self, bill_id):
        self.cursor.execute("""
            SELECT si.product_id, p.name, si.qty, si.price 
            FROM sale_items si 
            JOIN products p ON si.product_id = p.id 
            WHERE si.bill_id = ?
        """, (bill_id,))
        return self.cursor.fetchall()
    def get_customer_bills(self, phone):
        self.cursor.execute("""
            SELECT bill_id, date, total, transaction_type 
            FROM sales WHERE customer_phone=? ORDER BY date DESC
        """, (phone,))
        return self.cursor.fetchall()
    def is_bill_returnable(self, bill_id):
        self.cursor.execute("SELECT date FROM sales WHERE bill_id=?", (bill_id,))
        row = self.cursor.fetchone()
        if not row:
            return False, 0
        try:
            bill_date = datetime.strptime(row[0][:10], "%Y-%m-%d")
            days = (datetime.now() - bill_date).days
            return days <= 30, days
        except:
            return False, 0
    def get_closed_days(self):
        self.cursor.execute("""
            SELECT ds.session_id, ds.start_time, ds.end_time, 
                   COUNT(s.bill_id) as num_bills, 
                   COALESCE(SUM(CASE WHEN s.transaction_type='بيع' THEN s.total ELSE 0 END), 0) as sales
            FROM daily_sessions ds 
            LEFT JOIN sales s ON s.session_id = ds.session_id
            WHERE ds.status = 'CLOSED'
            GROUP BY ds.session_id
            ORDER BY ds.start_time DESC
        """)
        return self.cursor.fetchall()
    def get_bills_by_session(self, session_id):
        self.cursor.execute("""
            SELECT bill_id, date, total, transaction_type 
            FROM sales WHERE session_id=? ORDER BY bill_id
        """, (session_id,))
        return self.cursor.fetchall()
    # ─── التقارير (معدلة + فلاتر جديدة + break even) ───
    def get_sales_report(self, start_date=None, end_date=None, product_filter=None, phone_filter=None, model_filter=None, trans_filter=None, pay_filter=None):
        query = """
            SELECT s.date, s.total, s.payment_method, s.transaction_type, s.customer_phone 
            FROM sales s
        """
        params = []
        conditions = []
        if start_date and end_date:
            conditions.append("s.date >= ? AND s.date <= ?")
            params.extend([f"{start_date} 00:00:00", f"{end_date} 23:59:59"])
        elif start_date:
            conditions.append("s.date LIKE ?")
            params.append(f"{start_date}%")
        if product_filter:
            conditions.append("EXISTS (SELECT 1 FROM sale_items si WHERE si.bill_id = s.bill_id AND si.product_id = ?)")
            params.append(product_filter)
        if model_filter and model_filter != "الكل":
            conditions.append("EXISTS (SELECT 1 FROM sale_items si JOIN products p ON si.product_id = p.id WHERE si.bill_id = s.bill_id AND p.model_code = ?)")
            params.append(model_filter)
        if phone_filter:
            conditions.append("s.customer_phone LIKE ?")
            params.append(f"%{phone_filter}%")
        if trans_filter and trans_filter != "الكل":
            conditions.append("s.transaction_type = ?")
            params.append(trans_filter)
        if pay_filter and pay_filter != "الكل":
            conditions.append("s.payment_method = ?")
            params.append(pay_filter)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY s.date DESC"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    def get_total_profit(self, start_date=None, end_date=None, product_filter=None, phone_filter=None, model_filter=None):
        query = """
            SELECT SUM( (si.price - p.cost_price) * si.qty )
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.bill_id = s.bill_id
            WHERE s.transaction_type = 'بيع'
        """
        params = []
        if start_date and end_date:
            query += " AND s.date >= ? AND s.date <= ?"
            params.extend([f"{start_date} 00:00:00", f"{end_date} 23:59:59"])
        if product_filter:
            query += " AND si.product_id = ?"
            params.append(product_filter)
        if model_filter and model_filter != "الكل":
            query += " AND p.model_code = ?"
            params.append(model_filter)
        if phone_filter:
            query += " AND s.customer_phone LIKE ?"
            params.append(f"%{phone_filter}%")
        self.cursor.execute(query, params)
        res = self.cursor.fetchone()[0]
        return res or 0.0
    def get_variable_cost(self, start_date=None, end_date=None, model_filter=None):
        query = """
            SELECT SUM(p.cost_price * si.qty)
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.bill_id = s.bill_id
            WHERE s.transaction_type = 'بيع'
        """
        params = []
        if start_date and end_date:
            query += " AND s.date >= ? AND s.date <= ?"
            params.extend([f"{start_date} 00:00:00", f"{end_date} 23:59:59"])
        if model_filter and model_filter != "الكل":
            query += " AND p.model_code = ?"
            params.append(model_filter)
        self.cursor.execute(query, params)
        res = self.cursor.fetchone()[0]
        return res or 0.0
    def get_unique_model_codes(self):
        self.cursor.execute("SELECT DISTINCT model_code FROM products WHERE model_code IS NOT NULL ORDER BY model_code")
        return [row[0] for row in self.cursor.fetchall() if row[0]]
    def export_report_to_excel(self, data, filename):
        if pd is not None:
            df = pd.DataFrame(data, columns=['التاريخ', 'الإجمالي', 'طريقة الدفع', 'نوع العملية', 'الهاتف'])
            df.to_excel(filename, index=False)
        else:
            with open(filename.replace('.xlsx', '.csv'), 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['التاريخ', 'الإجمالي', 'طريقة الدفع', 'نوع العملية', 'الهاتف'])
                writer.writerows(data)
    def close(self):
        self.conn.close()
# ────────────────────────────────────────────────
# 2. البرنامج الرئيسي
# ────────────────────────────────────────────────
class ShopSystem(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("3SSAM MEN'S WEAR - Management System")
        self.state("zoomed")
        self.configure(bg=COLOR_BG)
        self.db = DBManager()
        self.backup_database()
        container = tk.Frame(self, bg=COLOR_BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (LoginPage, CashierPage, ManagerPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(LoginPage)
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        if hasattr(frame, "refresh_data"):
            frame.refresh_data()
    def backup_database(self):
        try:
            if os.path.exists(DB_NAME):
                backup_dir = os.path.join(BASE_DIR, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_path = os.path.join(backup_dir, f"3ssam_store_backup_{ts}.db")
                shutil.copy2(DB_NAME, backup_path)
        except:
            pass
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG)
        self.controller = controller
        center = tk.Frame(self, bg=COLOR_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")
        if os.path.exists(LOGO_FILENAME):
            try:
                self.logo_img = tk.PhotoImage(file=LOGO_FILENAME) 
                lbl_logo = tk.Label(center, image=self.logo_img, bg=COLOR_BG)
                lbl_logo.pack(pady=20)
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
                  command=lambda: controller.show_frame(CashierPage)).pack(pady=15)
        tk.Button(center, text="دخول المدير", font=("Arial", 16, "bold"), width=20,
                  bg=COLOR_ACCENT, fg=COLOR_BG,
                  command=self.check_password).pack(pady=10)
    def check_password(self):
        pwd = simpledialog.askstring("المدير", "كلمة المرور:", show="*")
        if pwd == "1234":
            self.controller.show_frame(ManagerPage)
        elif pwd:
            messagebox.showerror("خطأ", "كلمة المرور غير صحيحة")
class CashierPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG)
        self.controller = controller
        self.cart = []
        self.return_results = []
        self.new_results = []
        self.active_session_id = None
        self.variant_list = []  # ليس مستخدم هنا
        # Header
        hdr = tk.Frame(self, bg=COLOR_HEADER, height=70)
        hdr.pack(fill="x")
        self.btn_back = tk.Button(hdr, text="← خروج", bg="#c0392b", fg="white", font=("Arial",12,"bold"),
                  command=lambda: controller.show_frame(LoginPage))
        self.btn_back.pack(side="left", padx=15, pady=12)
        self.btn_start_day = tk.Button(hdr, text="▶ ابدأ اليوم", bg="#27ae60", fg="white", font=("Arial",14,"bold"),
                                      command=self.action_start_day)
        self.btn_start_day.pack(side="left", padx=5)
        self.btn_end_day = tk.Button(hdr, text="■ اختم اليوم", bg="#e74c3c", fg="white", font=("Arial",14,"bold"),
                                   command=self.action_end_day)
        tk.Label(hdr, text="3SSAM POS - فاتورة جديدة", font=("Arial",20,"bold"),
                 bg=COLOR_HEADER, fg="white").pack(side="right", padx=20, pady=12)
        main = tk.Frame(self, bg=COLOR_BG)
        main.pack(fill="both", expand=True, padx=20, pady=15)
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=3)
        main.grid_rowconfigure(0, weight=1)
        # ── اليسار ──
        left = tk.Frame(main, bg=COLOR_PANEL, relief="flat")
        left.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        tk.Label(left, text="السلة الحالية", font=("Arial",14,"bold"), bg=COLOR_PANEL, fg="#333").pack(side="top", pady=10)
        self.btn_checkout = tk.Button(left, text="دفع وطباعة (Enter)", font=("Arial", 16, "bold"),
                                      bg=COLOR_HEADER, fg="#ffffff", height=2,
                                      command=self.checkout, state="disabled")
        self.btn_checkout.pack(side="bottom", fill="x", padx=15, pady=20)
        frm_input = tk.Frame(left, bg=COLOR_PANEL)
        frm_input.pack(side="bottom", fill="x", padx=15, pady=10)
        tk.Label(frm_input, text="رقم الهاتف:", bg=COLOR_PANEL).grid(row=0, column=1, sticky="e", pady=4)
        self.ent_phone = tk.Entry(frm_input, width=22)
        self.ent_phone.grid(row=0, column=0, pady=4)
        tk.Label(frm_input, text="اسم العميل:", bg=COLOR_PANEL).grid(row=1, column=1, sticky="e", pady=4)
        self.ent_name = tk.Entry(frm_input, width=22)
        self.ent_name.grid(row=1, column=0, pady=4)
        tk.Label(frm_input, text="نوع العملية:", bg=COLOR_PANEL, font=("Arial",10,"bold")).grid(row=2, column=0, columnspan=2, pady=(12,4))
        self.trans_var = tk.StringVar(value="بيع")
        trans_f = tk.Frame(frm_input, bg=COLOR_PANEL)
        trans_f.grid(row=3, column=0, columnspan=2, sticky="e")
        for t in ["بيع", "مرتجع", "تبديل"]:
            tk.Radiobutton(trans_f, text=t, variable=self.trans_var, value=t, bg=COLOR_PANEL).pack(side="right", padx=8)
        self.btn_exchange = tk.Button(frm_input, text="تبديل منتج", font=("Arial",12,"bold"),
                                      bg="#f39c12", fg="white", width=20,
                                      command=self.open_exchange_dialog, state="disabled")
        self.btn_exchange.grid(row=4, column=0, columnspan=2, pady=8)
        # طريقة الشراء الجديدة
        tk.Label(frm_input, text="طريقة الشراء:", bg=COLOR_PANEL, font=("Arial",10,"bold")).grid(row=5, column=0, columnspan=2, pady=(8,4))
        self.payment_var = tk.StringVar(value="كاش")
        pay_f = tk.Frame(frm_input, bg=COLOR_PANEL)
        pay_f.grid(row=6, column=0, columnspan=2, sticky="w")
        for p in ["كاش", "انستاباي", "فودافون كاش", "فيزا"]:
            tk.Radiobutton(pay_f, text=p, variable=self.payment_var, value=p, bg=COLOR_PANEL).pack(side="left", padx=8)
        # نوع الخصم الجديد (قائمة)
        tk.Label(frm_input, text="نوع الخصم:", bg=COLOR_PANEL, font=("Arial",10,"bold")).grid(row=7, column=0, columnspan=2, pady=(8,4))
        self.discount_type = tk.StringVar(value="بدون خصم")
        self.discount_combo = ttk.Combobox(frm_input, textvariable=self.discount_type, 
                                           values=["بدون خصم", "خصم مخصص", "عرض القطعة والتانية هدية", 
                                                   "عرض 2 عليهم 3", "عرض 4 عليهم 7"],
                                           state="readonly", width=25)
        self.discount_combo.grid(row=8, column=0, columnspan=2, pady=4)
        self.ent_discount = tk.Entry(frm_input, width=22)  # للخصم المخصص فقط
        self.ent_discount.grid(row=9, column=0, columnspan=2, pady=4)
        self.lbl_total = tk.Label(left, text="الإجمالي: 0.00 ج.م", font=("Arial",22,"bold"),
                                  fg=COLOR_SUCCESS, bg=COLOR_PANEL)
        self.lbl_total.pack(side="bottom", pady=15)
        cols = ("كود", "الصنف", "الكمية", "السعر", "الإجمالي")
        self.tree_cart = ttk.Treeview(left, columns=cols, show="headings", height=12)
        for c in cols: self.tree_cart.heading(c, text=c)
        self.tree_cart.column("كود", width=70, anchor="center")
        self.tree_cart.column("الكمية", width=60, anchor="center")
        self.tree_cart.column("السعر", width=80, anchor="e")
        self.tree_cart.column("الإجمالي", width=100, anchor="e")
        self.tree_cart.pack(side="top", fill="both", expand=True, padx=8, pady=5)
        # ── اليمين ──
        right = tk.Frame(main, bg=COLOR_PANEL, relief="flat")
        right.grid(row=0, column=1, sticky="nsew", padx=(10,0))
        tk.Label(right, text="ابحث / أدخل اسم الصنف أو الكود (أو مسح QR)", font=("Arial",15,"bold"), bg=COLOR_PANEL, fg="#333").pack(pady=12)
        self.search_var = tk.StringVar()
        self.combo_search = ttk.Combobox(right, textvariable=self.search_var, font=("Arial",14), width=35, state="disabled")
        self.combo_search.pack(pady=8, padx=20)
        self.combo_search.bind("<KeyRelease>", self.on_search_key)
        self.combo_search.bind("<<ComboboxSelected>>", self.on_select_item)
        tk.Label(right, text="الكمية", font=("Arial",12), bg=COLOR_PANEL).pack(pady=(10,0))
        self.ent_qty = tk.Entry(right, font=("Arial",16), width=8, justify="center", state="disabled")
        self.ent_qty.insert(0, "1")
        self.ent_qty.pack(pady=6)
        self.btn_add = tk.Button(right, text="إضافة الصنف المختار", font=("Arial",13,"bold"),
                                 bg=COLOR_HEADER, fg="white", width=25,
                                 command=self.add_selected_item, state="disabled")
        self.btn_add.pack(pady=18)
        self.lbl_status = tk.Label(right, text="يجب بدء اليوم أولاً لتفعيل البيع", font=("Arial",12,"bold"),
                                   bg=COLOR_PANEL, fg=COLOR_WARNING, wraplength=380)
        self.lbl_status.pack(pady=10, padx=20)
        self.current_results = []
        
    def refresh_data(self):
        active = self.controller.db.get_active_session()
        if active:
            self.active_session_id = active
            self.enable_sales_ui(True)
        else:
            self.active_session_id = None
            self.enable_sales_ui(False)
    def action_start_day(self):
        self.active_session_id = self.controller.db.start_new_day()
        messagebox.showinfo("بداية اليوم", "تم بدء اليوم بنجاح، يمكنك البيع الآن.")
        self.enable_sales_ui(True)
    def action_end_day(self):
        confirm = messagebox.askyesno("ختم اليوم", "هل أنت متأكد من ختم اليوم؟\nلن يمكنك البيع بعد ذلك إلا ببدء يوم جديد.")
        if confirm:
            sess = self.active_session_id
            day_sales = 0.0
            if sess:
                self.controller.db.cursor.execute("""
                    SELECT COALESCE(SUM(total), 0) FROM sales 
                    WHERE session_id=? AND transaction_type='بيع'
                """, (sess,))
                day_sales = self.controller.db.cursor.fetchone()[0]
            messagebox.showinfo("مبيعات اليوم", f"إجمالي ما باعه اليوم: {day_sales:,.2f} ج.م\nتأكد من الفلوس في الخزنة قبل الخروج!")
            self.controller.db.end_current_day()
            self.active_session_id = None
            messagebox.showinfo("ختم اليوم", "تم إغلاق اليوم بنجاح.")
            self.enable_sales_ui(False)
            self.controller.show_frame(LoginPage)
    def enable_sales_ui(self, enable=True):
        state = "normal" if enable else "disabled"
        bg_btn = COLOR_HEADER if enable else "#95a5a6"
        self.btn_checkout.config(state=state, bg=bg_btn)
        self.btn_exchange.config(state=state, bg="#f39c12" if enable else "#95a5a6")
        self.combo_search.config(state=state)
        self.ent_qty.config(state=state)
        self.btn_add.config(state=state, bg=bg_btn)
        if enable:
            self.btn_start_day.pack_forget()
            self.btn_end_day.pack(side="left", padx=5)
            self.lbl_status.config(text="جاهز للبيع... (QR جاهز للمسح)", fg=COLOR_SUCCESS)
            self.combo_search.focus()
        else:
            self.btn_end_day.pack_forget()
            self.btn_start_day.pack(side="left", padx=5)
            self.lbl_status.config(text="يجب ضغط 'ابدأ اليوم' لتفعيل النظام", fg=COLOR_WARNING)
            self.cart.clear()
            self.update_cart_display()
            self.ent_phone.delete(0, tk.END)
            self.ent_name.delete(0, tk.END)
    # ── دوال البحث (مع دعم QR Code Scanner) ──
    def perform_search(self, term, target_list, target_combo):
        if len(term) < 2:
            target_combo['values'] = []
            target_list.clear()
            return
        results = self.controller.db.search_products(term)
        target_list[:] = results
        display_list = [f"{name} | {size} | {price:,.0f} ج | متبقي: {qty} | {idd}" 
                        for idd, name, size, price, qty in results]
        target_combo['values'] = display_list
        if display_list:
            target_combo.event_generate("<Down>")
    def on_search_key(self, event=None):
        term = self.search_var.get().strip()
        # دعم QR Code Reader (7 أحرف بالضبط → إضافة تلقائية)
        if len(term) == 7:
            prod = self.controller.db.get_product_by_id(term)
            if prod:
                self.selected_product = (prod[0], prod[1], prod[4], prod[5], prod[8])  # id, name, size, price, qty
                self.add_selected_item(qty_override=1)  # qty=1 تلقائي
                self.search_var.set("")
                return
        self.perform_search(term, self.current_results, self.combo_search)
    def on_select_item(self, event=None):
        if not self.current_results: return
        index = self.combo_search.current()
        if index < 0 or index >= len(self.current_results): return
        selected = self.current_results[index]
        self.selected_product = selected
        idd, name, size, price, qty = selected
        self.lbl_status.config(text=f"مختار: {name} ({size}) – {price:,.0f} ج – متبقي {qty}", fg=COLOR_SUCCESS)
    # ── تبديل (محافظ عليه كما هو + ربط بالمنطق الجديد) ──
    def open_exchange_dialog(self):
        self.trans_var.set("تبديل")
        self.handle_return(is_exchange=True)
    # ── معالجة المرتجع والاستبدال (المنطق الجديد كامل) ──
    def handle_return(self, is_exchange=False):
        bill_id_str = simpledialog.askstring("رقم الفاتورة", "أدخل رقم الفاتورة القديمة:")
        if not bill_id_str: return
        try:
            bill_id = int(bill_id_str)
        except:
            messagebox.showerror("خطأ", "رقم غير صحيح")
            return
        bill = self.controller.db.get_bill_by_id(bill_id)
        if not bill:
            messagebox.showerror("غير موجود", "الفاتورة غير موجودة")
            return
        returnable, days = self.controller.db.is_bill_returnable(bill_id)
        if not returnable:
            messagebox.showerror("غير مسموح", f"مرت عليها {days} يوم، لا يمكن الإرجاع بعد 30 يوم")
            return
        phone = bill[5] if len(bill) > 5 else ""
        if not phone:
            phone = simpledialog.askstring("هاتف العميل", "أدخل رقم الهاتف:")
        name = self.controller.db.get_customer_name(phone)
        # نافذة العرض
        win = tk.Toplevel(self)
        win.title("تفاصيل الفاتورة القديمة - " + ("استبدال" if is_exchange else "مرتجع"))
        win.geometry("900x700")
        win.configure(bg=COLOR_BG)
        win.grab_set()
        tk.Label(win, text=f"العميل: {name} | {phone}\nالتاريخ: {bill[1]}\nالإجمالي القديم: {bill[2]:,.2f} ج.م",
                 bg=COLOR_BG, fg="white", font=("Arial", 12, "bold")).pack(pady=10)
        # فواتير العميل السابقة
        tk.Label(win, text="كل فواتير العميل:", bg=COLOR_BG, fg="white").pack(anchor="w", padx=20)
        tree_cust = ttk.Treeview(win, columns=("رقم", "تاريخ", "إجمالي", "نوع"), show="headings", height=4)
        for c in ("رقم", "تاريخ", "إجمالي", "نوع"): tree_cust.heading(c, text=c)
        tree_cust.pack(fill="x", padx=20, pady=5)
        for b in self.controller.db.get_customer_bills(phone):
            tree_cust.insert("", "end", values=b)
        # عناصر الفاتورة
        tk.Label(win, text="عناصر الفاتورة (اضغط للتحديد):", bg=COLOR_BG, fg="white").pack(anchor="w", padx=20)
        items = self.controller.db.get_bill_items(bill_id)
        tree_items = ttk.Treeview(win, columns=("كود", "الاسم", "الكمية", "السعر"), show="headings", height=8)
        for c in ("كود", "الاسم", "الكمية", "السعر"): tree_items.heading(c, text=c)
        tree_items.pack(fill="both", expand=True, padx=20, pady=5)
        for it in items:
            tree_items.insert("", "end", values=it)
        selected_returns = []
        def select_for_return():
            sel = tree_items.selection()
            if not sel: return
            idx = tree_items.index(sel[0])
            item = items[idx]
            qty_max = item[2]
            qty = simpledialog.askinteger("كمية", f"كمية الإرجاع من {item[1]} (max {qty_max}):", minvalue=1, maxvalue=qty_max)
            if qty:
                selected_returns.append({
                    "id": item[0], "name": f"{item[1]} (مرتجع)", "qty": qty,
                    "price": item[3], "total": -qty * item[3], "return": True,
                    "original_bill": bill_id
                })
                messagebox.showinfo("تم", f"تم تحديد {qty} قطعة للإرجاع")
                update_selected()
        tk.Button(win, text="تحديد بند للإرجاع", bg=COLOR_ACCENT, fg="white", command=select_for_return).pack(pady=8)
        tk.Label(win, text="المحدد للإرجاع:", bg=COLOR_BG, fg="white").pack(anchor="w", padx=20)
        tree_sel = ttk.Treeview(win, columns=("كود", "اسم", "كمية", "إجمالي"), show="headings", height=6)
        for c in ("كود", "اسم", "كمية", "إجمالي"): tree_sel.heading(c, text=c)
        tree_sel.pack(fill="both", expand=True, padx=20, pady=5)
        def update_selected():
            for i in tree_sel.get_children(): tree_sel.delete(i)
            for r in selected_returns:
                tree_sel.insert("", "end", values=(r["id"], r["name"], r["qty"], f"{r['total']:,.2f}"))
        def confirm():
            if not selected_returns:
                messagebox.showwarning("ناقص", "يجب تحديد بند واحد على الأقل")
                return
            for r in selected_returns:
                self.cart.append(r)
            self.update_cart_display()
            self.trans_var.set("تبديل" if is_exchange else "مرتجع")
            win.destroy()
            if not is_exchange:
                # تنفيذ المرتجع فوراً بدون طباعة
                self.checkout(return_only=True)
            else:
                messagebox.showinfo("جاهز", "تم إضافة الإرجاع. أضف المنتجات الجديدة ثم اضغط دفع")
        tk.Button(win, text="تأكيد وإنهاء", bg=COLOR_SUCCESS, fg="white", font=("Arial",12,"bold"), command=confirm).pack(pady=15)
    # ── حساب الخصم الجديد (مع العروض) ──
    def calculate_net_total(self, gross):
        disc_type = self.discount_type.get()
        if disc_type == "بدون خصم":
            return gross, 0.0
        elif disc_type == "خصم مخصص":
            disc_str = self.ent_discount.get().strip()
            disc = 0.0
            if disc_str:
                try:
                    if disc_str.endswith('%'):
                        perc = float(disc_str[:-1].strip())
                        if 0 < perc <= 100: disc = gross * perc / 100
                    else:
                        disc = float(disc_str)
                except:
                    disc = 0.0
            return gross - disc, disc
        # العروض
        flat_prices = []
        for item in self.cart:
            flat_prices.extend([item['price']] * item['qty'])
        required = 0
        pay_count = 0
        if disc_type == "عرض القطعة والتانية هدية":
            required = 2
            pay_count = 1
        elif disc_type == "عرض 2 عليهم 3":
            required = 5
            pay_count = 3
        elif disc_type == "عرض 4 عليهم 7":
            required = 11
            pay_count = 7
        if len(flat_prices) != required:
            messagebox.showwarning("العرض", f"يجب أن يكون بالسلة بالضبط {required} قطعة لهذا العرض")
            return gross, 0.0
        flat_prices.sort(reverse=True)
        net = sum(flat_prices[:pay_count])
        return net, gross - net
    def add_selected_item(self, qty_override=None):
        if not hasattr(self, 'selected_product') or not self.selected_product:
            messagebox.showwarning("اختر صنفاً", "يرجى اختيار صنف من القائمة أولاً")
            return
        idd, name, size, price, stock = self.selected_product
        try:
            qty = qty_override if qty_override is not None else int(self.ent_qty.get())
            if qty <= 0: raise ValueError
        except:
            messagebox.showwarning("الكمية", "أدخل كمية صحيحة")
            return
        if qty > stock and self.trans_var.get() != "مرتجع":
            messagebox.showwarning("المخزون", f"المتاح فقط {stock} قطعة")
            return
        item_total = qty * price
        item = {"id": idd, "name": name, "qty": qty, "price": price, "total": item_total}
        self.cart.append(item)
        self.update_cart_display()
        self.lbl_status.config(text=f"تم إضافة: {name} × {qty} = {item_total:,.1f} ج.م", fg=COLOR_SUCCESS)
        self.search_var.set("")
        self.combo_search['values'] = []
        if qty_override is None:
            self.ent_qty.delete(0, tk.END)
            self.ent_qty.insert(0, "1")
            self.ent_qty.focus()
    def update_cart_display(self):
        for i in self.tree_cart.get_children(): self.tree_cart.delete(i)
        gross = sum(item["total"] for item in self.cart)
        net, disc = self.calculate_net_total(gross)
        for item in self.cart:
            self.tree_cart.insert("", "end", values=(
                item["id"], item["name"], item["qty"], f"{item['price']:,.1f}", f"{item['total']:,.1f}"
            ))
        if disc > 0:
            self.lbl_total.config(text=f"الإجمالي النهائي: {net:,.2f} ج.م\n(خصم: {disc:,.2f})", fg=COLOR_SUCCESS)
        else:
            self.lbl_total.config(text=f"الإجمالي: {net:,.2f} ج.م", fg=COLOR_SUCCESS)
    def checkout(self, return_only=False):
        if not self.cart: return
        tr_type = self.trans_var.get()
        gross = sum(item["total"] for item in self.cart)
        if tr_type == "مرتجع": gross = -gross
        final_total, disc = self.calculate_net_total(gross)
        method = self.payment_var.get()
        phone = self.ent_phone.get().strip()
        cname = self.ent_name.get().strip()
        # تحديد original_bill_id إذا وجد
        original_bill = None
        for item in self.cart:
            if item.get("original_bill"):
                original_bill = item["original_bill"]
                break
        bill_id, dt = self.controller.db.save_transaction(
            self.cart, final_total, method, tr_type, phone, cname, self.active_session_id, original_bill
        )
        if not return_only and tr_type != "مرتجع":
            self.print_receipt(bill_id, dt, final_total, method, tr_type, disc, original_bill)
            messagebox.showinfo("تم", f"تم حفظ {tr_type} رقم {bill_id}")
        elif tr_type == "مرتجع":
            messagebox.showinfo("تم", f"تم تسجيل المرتجع رقم {bill_id} (بدون طباعة)")
        self.cart.clear()
        self.update_cart_display()
        self.search_var.set("")
        self.combo_search['values'] = []
        self.ent_discount.delete(0, tk.END)
        self.discount_type.set("بدون خصم")
    def print_receipt(self, bid, date, total, method, tr_type, discount=0, original=None):
        lines = [
            "====================================",
            "          3SSAM MEN'S WEAR          ",
            "     (شعار المحل: logo.png)        ",
            "       Lotfallah - Faiyum           ",
            "====================================",
            f"Bill No : {bid:>6}",
            f"Date    : {date}",
            f"Type    : {tr_type}",
        ]
        if original:
            lines.append(f"مرجع الفاتورة القديمة: {original}")
        lines.append("====================================")
        for it in self.cart:
            sign = " " if it["total"] >= 0 else "-"
            lines.append(f"{it['name'][:30]:<30} × {it['qty']:>2} = {sign}{abs(it['total']):>8.2f}")
        lines.append("====================================")
        if discount != 0: lines.append(f"Discount          : {discount:>10.2f}")
        lines.extend([
            f"TOTAL         : {abs(total):>10.2f} EGP",
            f"PAID BY       : {method}",
            "------------------------------------",
            "سياسة التبديل والاسترجاع:",
            "يمكن التبديل أو الاسترجاع خلال 30 يوم فقط بشرط أن تكون القطعة بحالتها الأصلية",
            "وبدون أي استخدام أو تلف.",
            "------------------------------------",
            "Powered by Mohamed Magdy"
        ])
        text = "\n".join(lines)
        try:
            tmp = tempfile.mktemp(".txt")
            with open(tmp, "w", encoding="utf-8") as f: f.write(text)
            os.startfile(tmp, "print")
            # ملاحظة للطباعة الحرارية:
            # pip install python-escpos
            # من escpos.printer import Usb
            # p = Usb(0x0416, 0x5011)  # غير الـ ID حسب الطابعة
            # p.text(text)
            # p.image(LOGO_FILENAME)   # طباعة اللوجو
            # p.cut()
        except: pass



class ManagerPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG)
        self.controller = controller
        tk.Button(self, text="تسجيل خروج", bg="#c0392b", fg="white", font=("Arial",12,"bold"),
                  command=lambda: controller.show_frame(LoginPage)).pack(anchor="ne", padx=20, pady=10)
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)
        # تبويب 1: التقارير (محسن + break even + export excel)
        self.tab_report = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_report, text="التقارير والتحليل")
        frm_filter = tk.Frame(self.tab_report, bg=COLOR_PANEL)
        frm_filter.pack(fill="x", pady=15, padx=20)
        tk.Label(frm_filter, text="من:", bg=COLOR_PANEL).pack(side="left", padx=(0,5))
        self.ent_from = tk.Entry(frm_filter, width=12)
        self.ent_from.pack(side="left", padx=5)
        tk.Label(frm_filter, text="إلى:", bg=COLOR_PANEL).pack(side="left", padx=(20,5))
        self.ent_to = tk.Entry(frm_filter, width=12)
        self.ent_to.pack(side="left", padx=5)
        tk.Label(frm_filter, text="فلتر منتج:", bg=COLOR_PANEL).pack(side="left", padx=(20,5))
        self.product_combo = ttk.Combobox(frm_filter, width=20)
        self.product_combo.pack(side="left", padx=5)
        tk.Label(frm_filter, text="فلتر موديل:", bg=COLOR_PANEL).pack(side="left", padx=(20,5))
        self.model_combo = ttk.Combobox(frm_filter, width=15)
        self.model_combo.pack(side="left", padx=5)
        tk.Label(frm_filter, text="نوع العملية:", bg=COLOR_PANEL).pack(side="left", padx=(20,5))
        self.trans_filter = ttk.Combobox(frm_filter, values=["الكل","بيع","مرتجع","تبديل"], width=12)
        self.trans_filter.pack(side="left", padx=5)
        tk.Label(frm_filter, text="طريقة الدفع:", bg=COLOR_PANEL).pack(side="left", padx=(20,5))
        self.pay_filter = ttk.Combobox(frm_filter, values=["الكل","كاش","انستاباي","فودافون كاش","فيزا"], width=15)
        self.pay_filter.pack(side="left", padx=5)
        tk.Label(frm_filter, text="هاتف:", bg=COLOR_PANEL).pack(side="left", padx=(20,5))
        self.ent_phone_filter = tk.Entry(frm_filter, width=15)
        self.ent_phone_filter.pack(side="left", padx=5)
        tk.Button(frm_filter, text="عرض التقرير", bg=COLOR_ACCENT, fg="white", command=self.show_report).pack(side="left", padx=15)
        tk.Button(frm_filter, text="تصدير إكسيل", command=self.export_report).pack(side="left", padx=5)
        # مصروفات أخرى + break even
        frm_cost = tk.Frame(self.tab_report, bg=COLOR_PANEL)
        frm_cost.pack(fill="x", pady=10, padx=20)
        tk.Label(frm_cost, text="مصروفات ثابتة أخرى:", bg=COLOR_PANEL, font=("Arial",11,"bold")).pack(anchor="w")
        tk.Label(frm_cost, text="إيجار:", bg=COLOR_PANEL).pack(side="left", padx=5)
        self.ent_rent = tk.Entry(frm_cost, width=10)
        self.ent_rent.pack(side="left", padx=5)
        tk.Label(frm_cost, text="رواتب:", bg=COLOR_PANEL).pack(side="left", padx=5)
        self.ent_salaries = tk.Entry(frm_cost, width=10)
        self.ent_salaries.pack(side="left", padx=5)
        tk.Label(frm_cost, text="أخرى:", bg=COLOR_PANEL).pack(side="left", padx=5)
        self.ent_other_cost = tk.Entry(frm_cost, width=10)
        self.ent_other_cost.pack(side="left", padx=5)
        self.lbl_stats = tk.Label(self.tab_report, text="جاري التحميل...", font=("Arial",13), bg=COLOR_PANEL, justify="left")
        self.lbl_stats.pack(pady=15, anchor="w", padx=30)
        self.frm_graph = tk.Frame(self.tab_report, bg=COLOR_PANEL)
        self.frm_graph.pack(fill="both", expand=True, padx=20, pady=10)
        # تبويب 2: المخزون
        self.tab_stock = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_stock, text="حالة المخزون (الكل)")
        cols = ("الكود", "الصنف", "الكمية", "السعر", "التكلفة", "المورد", "الحد الأدنى", "موديل")
        self.tree_low = ttk.Treeview(self.tab_stock, columns=cols, show="headings")
        for c in cols: self.tree_low.heading(c, text=c)
        self.tree_low.column("الكود", width=90, anchor="center")
        self.tree_low.column("الكمية", width=100, anchor="center")
        self.tree_low.pack(fill="both", expand=True, padx=20, pady=10)
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
        # تبويب 3: نواقص
        self.tab_critical = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_critical, text="ناقص جداً (1–2 قطعة)")
        cols_crit = ("الصنف", "الكمية", "المورد", "الحد")
        self.tree_critical = ttk.Treeview(self.tab_critical, columns=cols_crit, show="headings")
        for c in cols_crit: self.tree_critical.heading(c, text=c)
        self.tree_critical.pack(fill="both", expand=True, padx=20, pady=20)
        # تبويب 4: السجل
        self.tab_log = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_log, text="سجل الفواتير")
        cols_log = ("رقم", "التاريخ", "الإجمالي", "الدفع", "النوع")
        self.tree_log = ttk.Treeview(self.tab_log, columns=cols_log, show="headings")
        for c in cols_log: self.tree_log.heading(c, text=c)
        self.tree_log.column("رقم", width=80, anchor="center")
        self.tree_log.pack(fill="both", expand=True, padx=20, pady=20)
        # تبويب 5: إدارة الموردين (جديد كامل)
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
        # تبويب 6: سجل الأيام المغلقة (جديد)
        self.tab_days = tk.Frame(notebook, bg=COLOR_PANEL)
        notebook.add(self.tab_days, text="سجل الأيام المغلقة")
        cols_days = ("الجلسة", "البداية", "النهاية", "عدد الفواتير", "المبيعات")
        self.tree_days = ttk.Treeview(self.tab_days, columns=cols_days, show="headings")
        for c in cols_days: self.tree_days.heading(c, text=c)
        self.tree_days.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree_days.bind("<Double-1>", self.show_day_details)
        tk.Button(self.tab_days, text="تحديث", command=self.load_closed_days).pack(pady=5)
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
        selected_prod = self.product_combo.get()
        prod_id = selected_prod.split(" - ")[0] if " - " in selected_prod and selected_prod != "الكل" else None
        model_f = self.model_combo.get()
        trans_f = self.trans_filter.get()
        pay_f = self.pay_filter.get()
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
        # مصروفات ثابتة
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
        for r in data:
            m = r[2]
            pay_dict[m] = pay_dict.get(m, 0) + r[1]
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
        if pay_dict:
            fig, ax = plt.subplots(figsize=(7,4))
            labels_map = {"كاش": "Cash", "فيزا": "Visa", "انستاباي": "Instapay", "فودافون كاش": "Vodafone"}
            eng_labels = [labels_map.get(k, k) for k in pay_dict.keys()]
            ax.bar(eng_labels, pay_dict.values(), color=["#3A4032","#D4AF37","#8e44ad","#2980b9"])
            ax.set_title("توزيع المبيعات حسب طريقة الدفع")
            ax.set_ylabel("المبلغ (ج.م)")
            ax.grid(True, axis='y', alpha=0.3)
            canvas = FigureCanvasTkAgg(fig, master=self.frm_graph)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        # رسمة Break Even
        fig2, ax2 = plt.subplots(figsize=(7,3))
        categories = ['الإيرادات', 'التكلفة المتغيرة', 'المصروفات الثابتة', 'الربح الصافي']
        values = [sales, var_cost, fixed, net_profit]
        colors = ['#27ae60', '#e67e22', '#c0392b', '#2980b9']
        ax2.barh(categories, values, color=colors)
        ax2.set_title("تحليل Break Even")
        ax2.grid(True, axis='x', alpha=0.3)
        canvas2 = FigureCanvasTkAgg(fig2, master=self.frm_graph)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True, pady=10)
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
            messagebox.showinfo("لا بيانات", "لا توجد فواتير")
            return
        file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")])
        if file:
            self.controller.db.export_report_to_excel(data, file)
            messagebox.showinfo("تم", "تم حفظ التقرير بصيغة إكسيل")
    def load_all_stock(self):
        for i in self.tree_low.get_children(): self.tree_low.delete(i)
        rows = self.controller.db.get_all_stock()
        for r in rows:
            self.tree_low.insert("", "end", values=r)
    def load_critical_low_stock(self):
        for i in self.tree_critical.get_children(): self.tree_critical.delete(i)
        rows = self.controller.db.get_critical_low_stock()
        for r in rows: self.tree_critical.insert("", "end", values=r, tags=('critical',))
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
        # يمكن توسيعها لاحقاً، حالياً رسالة بسيطة
        messagebox.showinfo("تعديل", "يمكن تعديل الصف من خلال قاعدة البيانات مباشرة أو توسيع النظام")
    def delete_supplier(self):
        sel = self.tree_sup.selection()
        if not sel: return
        sid = self.tree_sup.item(sel[0])['values'][0]
        if messagebox.askyesno("حذف", f"حذف الشحنة رقم {sid}؟"):
            self.controller.db.delete_supplier(sid)
            self.load_suppliers()
    def load_closed_days(self):
        for i in self.tree_days.get_children(): self.tree_days.delete(i)
        rows = self.controller.db.get_closed_days()
        for r in rows:
            self.tree_days.insert("", "end", values=r)
    def show_day_details(self, event=None):
        sel = self.tree_days.selection()
        if not sel: return
        sess_id = self.tree_days.item(sel[0])['values'][0]
        bills = self.controller.db.get_bills_by_session(sess_id)
        win = tk.Toplevel(self)
        win.title(f"تفاصيل اليوم - جلسة {sess_id}")
        win.geometry("800x500")
        tree = ttk.Treeview(win, columns=("رقم", "التاريخ", "الإجمالي", "النوع"), show="headings")
        for c in ("رقم", "التاريخ", "الإجمالي", "النوع"): tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        for b in bills:
            tree.insert("", "end", values=b)
    def open_add_product_window(self, product=None):
        win = tk.Toplevel(self)
        win.title("إضافة موديل جديد (مع قطع متعددة)")
        win.geometry("900x700")
        win.configure(bg=COLOR_BG)
        win.grab_set()
        # النصف العلوي: بيانات الموديل
        upper = tk.LabelFrame(win, text="بيانات الموديل (مشتركة لكل القطع)", bg=COLOR_BG, fg=COLOR_ACCENT, font=("Arial",12,"bold"))
        upper.pack(fill="x", padx=20, pady=15)
        model_fields = [
            ("اسم المنتج", tk.Entry),
            ("كود الموديل", tk.Entry),
            ("النوع", tk.Entry),
            ("سعر البيع (للموديل كله)", tk.Entry),
            ("سعر التكلفة (للموديل كله)", tk.Entry),
            ("اسم المورد", tk.Entry)
        ]
        model_entries = {}
        for i, (lab, wtype) in enumerate(model_fields):
            f = tk.Frame(upper, bg=COLOR_BG)
            f.pack(fill="x", padx=30, pady=8)
            tk.Label(f, text=lab + ":", bg=COLOR_BG, fg="white", font=("Arial",11)).pack(side="left")
            ent = wtype(f, width=35, font=("Arial",11))
            ent.pack(side="right")
            model_entries[lab] = ent
        # النصف السفلي: إضافة قطع (لون - مقاس - كمية - كود 7 حروف)
        lower = tk.LabelFrame(win, text="القطع / الألوان / المقاسات (يمكن إضافة عدة صفوف)", bg=COLOR_BG, fg=COLOR_ACCENT, font=("Arial",12,"bold"))
        lower.pack(fill="both", expand=True, padx=20, pady=15)
        # tree للقطع المضافة
        cols_var = ("كود المنتج (7 حروف)", "اللون", "المقاس", "الكمية")
        tree_var = ttk.Treeview(lower, columns=cols_var, show="headings", height=10)
        for c in cols_var: tree_var.heading(c, text=c)
        tree_var.pack(fill="both", expand=True, padx=10, pady=10)
        # فورم إضافة قطعة
        var_f = tk.Frame(lower, bg=COLOR_BG)
        var_f.pack(fill="x", padx=10, pady=10)
        var_entries = {}
        for lab in cols_var:
            tk.Label(var_f, text=lab + ":", bg=COLOR_BG, fg="white").pack(side="left", padx=5)
            ent = tk.Entry(var_f, width=18)
            ent.pack(side="left", padx=5)
            var_entries[lab] = ent
        added_variants = []
        def add_variant_row():
            try:
                pid = var_entries["كود المنتج (7 حروف)"].get().strip().upper()
                if len(pid) != 7: raise ValueError("كود 7 حروف فقط")
                color = var_entries["اللون"].get().strip()
                size = var_entries["المقاس"].get().strip().upper()
                qty = int(var_entries["الكمية"].get())
                tree_var.insert("", "end", values=(pid, color, size, qty))
                added_variants.append((pid, color, size, qty))
                # تفريغ
                for e in var_entries.values(): e.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("خطأ", str(e))
        tk.Button(var_f, text="إضافة قطعة لهذا الموديل", bg=COLOR_ACCENT, fg=COLOR_BG, command=add_variant_row).pack(side="left", padx=20)
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
        tk.Button(lower, text="تم - حفظ كل القطع", font=("Arial",13,"bold"), bg=COLOR_SUCCESS, fg="white", command=finish_model).pack(pady=15)
    def open_edit_product(self):
        sel = self.tree_low.selection()
        if not sel: return
        pid = self.tree_low.item(sel[0])['values'][0]
        full = self.controller.db.get_product_by_id(pid)
        if full:
            # استخدام الواجهة القديمة للتعديل الفردي (محافظ عليها)
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
                except Exception as e: messagebox.showerror("خطأ", str(e))
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



if __name__ == "__main__":
    app = ShopSystem()
    app.mainloop()