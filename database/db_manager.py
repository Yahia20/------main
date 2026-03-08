import sqlite3
from datetime import datetime
from tkinter import messagebox
import csv
import os

from config import DB_NAME

try:
    import pandas as pd
except ImportError:
    pd = None

class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.check_and_update_schema()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                             id TEXT PRIMARY KEY CHECK(length(id)=7),
                             name TEXT, color TEXT, type TEXT,
                             size TEXT CHECK(length(size)<=3),
                             price REAL, cost_price REAL DEFAULT 0,
                             supplier TEXT, qty INTEGER, min_limit INTEGER DEFAULT 3,
                             model_code TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             name TEXT, order_name TEXT, qty INTEGER,
                             total_price REAL, debt REAL DEFAULT 0, paid REAL DEFAULT 0)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
                             phone TEXT, name TEXT,
                             last_item TEXT, total_spent REAL DEFAULT 0,
                             last_date TEXT,
                             PRIMARY KEY(phone, name))''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS daily_sessions (
                             session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             start_time TEXT,
                             end_time TEXT,
                             status TEXT DEFAULT 'OPEN')''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
                             bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             date TEXT,
                             total REAL,
                             payment_method TEXT,
                             transaction_type TEXT,
                             customer_phone TEXT,
                             customer_name TEXT,
                             session_id INTEGER,
                             original_bill_id INTEGER DEFAULT NULL,
                             discount_type TEXT DEFAULT 'بدون خصم',
                             discount_amount REAL DEFAULT 0.0)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sale_items (
                             bill_id INTEGER, product_id TEXT,
                             qty INTEGER, price REAL,
                             FOREIGN KEY(bill_id) REFERENCES sales(bill_id))''')
        self.conn.commit()

    def check_and_update_schema(self):
        try:
            self.cursor.execute("PRAGMA table_info(products)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if 'model_code' not in columns:
                self.cursor.execute("ALTER TABLE products ADD COLUMN model_code TEXT")
            
            self.cursor.execute("PRAGMA table_info(sales)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if 'original_bill_id' not in columns:
                self.cursor.execute("ALTER TABLE sales ADD COLUMN original_bill_id INTEGER DEFAULT NULL")
            if 'customer_name' not in columns:
                self.cursor.execute("ALTER TABLE sales ADD COLUMN customer_name TEXT DEFAULT ''")
            if 'discount_type' not in columns:
                self.cursor.execute("ALTER TABLE sales ADD COLUMN discount_type TEXT DEFAULT 'بدون خصم'")
            if 'discount_amount' not in columns:
                self.cursor.execute("ALTER TABLE sales ADD COLUMN discount_amount REAL DEFAULT 0.0")
            
            self.cursor.execute("PRAGMA table_info(suppliers)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if 'paid' not in columns:
                self.cursor.execute("ALTER TABLE suppliers ADD COLUMN paid REAL DEFAULT 0")
                
            self.cursor.execute("PRAGMA table_info(customers)")
            cust_info = self.cursor.fetchall()
            pk_cols = [c[1] for c in cust_info if c[5] > 0]
            if len(pk_cols) == 1 and pk_cols[0] == 'phone':
                self.cursor.execute("CREATE TABLE customers_temp (phone TEXT, name TEXT, last_item TEXT, total_spent REAL DEFAULT 0, last_date TEXT, PRIMARY KEY(phone, name))")
                self.cursor.execute("INSERT OR IGNORE INTO customers_temp SELECT phone, name, last_item, total_spent, last_date FROM customers")
                self.cursor.execute("DROP TABLE customers")
                self.cursor.execute("ALTER TABLE customers_temp RENAME TO customers")

            self.conn.commit()
        except Exception as e:
            print(f"Schema Update Error: {e}")

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

    def get_critical_low_stock(self, search_term=""):
        base_query = """
            SELECT id, name, qty, supplier, min_limit, model_code 
            FROM products 
            WHERE 
              (model_code != '' AND model_code IS NOT NULL AND model_code IN (
                  SELECT model_code FROM products WHERE model_code != '' GROUP BY model_code HAVING SUM(qty) <= 2
              ))
              OR 
              ((model_code = '' OR model_code IS NULL) AND qty <= 2)
        """
        if not search_term:
            self.cursor.execute(base_query + " ORDER BY model_code ASC, qty ASC")
        else:
            t = f"%{search_term}%"
            full_query = base_query + " AND (id LIKE ? OR model_code LIKE ? OR name LIKE ?) ORDER BY model_code ASC, qty ASC"
            self.cursor.execute(full_query, (t, t, t))
        return self.cursor.fetchall()

    def get_product_by_id(self, pid):
        self.cursor.execute("SELECT * FROM products WHERE id = ?", (pid,))
        return self.cursor.fetchone()

    def search_products(self, term):
            term = f"%{term}%"
            self.cursor.execute("""
                SELECT id, name, size, price, qty, color, model_code 
                FROM products 
                WHERE id LIKE ? OR name LIKE ? OR model_code LIKE ?
                ORDER BY name LIMIT 15
            """, (term, term, term))
            return self.cursor.fetchall()

    def get_all_stock(self, search_term=""):
        if not search_term:
            self.cursor.execute("""
                SELECT id, name, qty, price, cost_price, supplier, min_limit, model_code 
                FROM products ORDER BY qty ASC
            """)
        else:
            t = f"%{search_term}%"
            self.cursor.execute("""
                SELECT id, name, qty, price, cost_price, supplier, min_limit, model_code 
                FROM products 
                WHERE id LIKE ? OR model_code LIKE ? OR name LIKE ?
                ORDER BY qty ASC
            """, (t, t, t))
        return self.cursor.fetchall()

    def get_all_product_names(self):
        self.cursor.execute("SELECT id, name FROM products ORDER BY name")
        return self.cursor.fetchall()

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

    def get_customer_name(self, phone):
        self.cursor.execute("SELECT name FROM customers WHERE phone=?", (phone,))
        res = self.cursor.fetchone()
        return res[0] if res else ""

    def save_transaction(self, items, total, method, trans_type, customer_phone="", customer_name="", session_id=None, original_bill_id=None, discount_type="بدون خصم", discount_amount=0.0):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_total = total
        self.cursor.execute("""
            INSERT INTO sales (date, total, payment_method, transaction_type, customer_phone, customer_name, session_id, original_bill_id, discount_type, discount_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, final_total, method, trans_type, customer_phone, customer_name, session_id, original_bill_id, discount_type, discount_amount))
        bill_id = self.cursor.lastrowid
        
        for item in items:
            self.cursor.execute("INSERT INTO sale_items VALUES (?, ?, ?, ?)",
                                (bill_id, item['id'], item['qty'], item['price']))
            qty_change = item['qty']
            if trans_type == "بيع":
                self.cursor.execute("UPDATE products SET qty = qty - ? WHERE id = ?", (qty_change, item['id']))
            elif trans_type == "مرتجع":
                self.cursor.execute("UPDATE products SET qty = qty + ? WHERE id = ?", (qty_change, item['id']))
        
        if customer_phone and customer_name:
            self.cursor.execute("SELECT * FROM customers WHERE phone=? AND name=?", (customer_phone, customer_name))
            if self.cursor.fetchone():
                self.cursor.execute("""
                    UPDATE customers SET total_spent = total_spent + ?, last_date = ?, last_item = ?
                    WHERE phone = ? AND name = ?
                """, (final_total, date_str, items[0]['name'], customer_phone, customer_name))
            else:
                self.cursor.execute("""
                    INSERT INTO customers (phone, name, last_item, total_spent, last_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (customer_phone, customer_name, items[0]['name'], final_total, date_str))
        self.conn.commit()
        return bill_id, date_str

    # التعديل هنا: تمرير discount_amount بشكل كامل لتدعم الميزة مستقبلاً
    def process_exchange(self, old_items, new_items, net_total, method, phone, name, session_id, original_bill_id=None, discount_type="بدون خصم", discount_amount=0.0):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        t_type = "مرتجع" if not new_items else "تبديل"
        
        self.cursor.execute("""
            INSERT INTO sales (date, total, payment_method, transaction_type, customer_phone, customer_name, session_id, original_bill_id, discount_type, discount_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, net_total, method, t_type, phone, name, session_id, original_bill_id, discount_type, discount_amount))
        bill_id = self.cursor.lastrowid
        
        for item in old_items:
            self.cursor.execute("INSERT INTO sale_items VALUES (?, ?, ?, ?)", (bill_id, item['id'], -item['qty'], item['price']))
            self.cursor.execute("UPDATE products SET qty = qty + ? WHERE id = ?", (item['qty'], item['id']))
            
        for item in new_items:
            self.cursor.execute("INSERT INTO sale_items VALUES (?, ?, ?, ?)", (bill_id, item['id'], item['qty'], item['price']))
            self.cursor.execute("UPDATE products SET qty = qty - ? WHERE id = ?", (item['qty'], item['id']))
            
        if phone and name:
            self.cursor.execute("SELECT * FROM customers WHERE phone=? AND name=?", (phone, name))
            if self.cursor.fetchone():
                self.cursor.execute("UPDATE customers SET total_spent = total_spent + ?, last_date = ? WHERE phone=? AND name=?", (net_total, date_str, phone, name))
            else:
                self.cursor.execute("INSERT INTO customers (phone, name, total_spent, last_date) VALUES (?, ?, ?, ?)", (phone, name, net_total, date_str))
                
        self.conn.commit()
        return bill_id, date_str

    def get_returnable_items(self, bill_id):
        self.cursor.execute("""
            SELECT si.product_id, p.name, si.qty, si.price, p.model_code
            FROM sale_items si 
            JOIN products p ON si.product_id = p.id 
            WHERE si.bill_id = ? AND si.qty > 0
        """, (bill_id,))
        original_items = self.cursor.fetchall()

        self.cursor.execute("""
            SELECT si.product_id, SUM(ABS(si.qty))
            FROM sale_items si
            JOIN sales s ON si.bill_id = s.bill_id
            WHERE s.original_bill_id = ? AND si.qty < 0
            GROUP BY si.product_id
        """, (bill_id,))
        returned_items = dict(self.cursor.fetchall())

        returnable_list = []
        for item in original_items:
            pid, name, original_qty, price, model_code = item
            already_returned_qty = returned_items.get(pid, 0)
            remaining_qty = original_qty - already_returned_qty
            if remaining_qty > 0:
                returnable_list.append((pid, name, remaining_qty, price, model_code))
        return returnable_list

    def get_bill_by_id(self, bill_id):
        self.cursor.execute("""
            SELECT bill_id, date, total, payment_method, transaction_type, 
                   customer_phone, customer_name, discount_type, discount_amount
            FROM sales WHERE bill_id=?
        """, (bill_id,))
        return self.cursor.fetchone()

    def get_bill_items(self, bill_id):
        self.cursor.execute("""
            SELECT si.product_id, p.name, si.qty, si.price, p.model_code
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

    def get_closed_days(self):
        # التعديل هنا: جعلنا السيستم يجمع (كل الفواتير) لمعرفة صافي الدرج بدلاً من جمع البيع فقط
        self.cursor.execute("""
            SELECT ds.session_id, ds.start_time, ds.end_time, 
                   COUNT(s.bill_id) as num_bills, 
                   COALESCE(SUM(s.total), 0) as sales
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

    def get_sales_report(self, start_date=None, end_date=None, product_filter=None, phone_filter=None, model_filter=None, trans_filter=None, pay_filter=None):
        query = "SELECT s.bill_id, s.date, s.total, s.payment_method, s.transaction_type, s.customer_phone FROM sales s"
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

    def get_bill_items_with_cost(self, bill_id):
        self.cursor.execute("""
            SELECT si.qty, p.cost_price 
            FROM sale_items si 
            JOIN products p ON si.product_id = p.id 
            WHERE si.bill_id = ?
        """, (bill_id,))
        return self.cursor.fetchall()

    def get_inventory_total_cost(self):
        self.cursor.execute("SELECT SUM(qty * cost_price) FROM products")
        res = self.cursor.fetchone()
        return res[0] if res and res[0] else 0.0

    def get_all_detailed_transactions(self):
        query = """
            SELECT s.bill_id, s.date, s.session_id, s.transaction_type, s.payment_method,
                   s.customer_phone, s.customer_name, s.total, s.discount_type, s.discount_amount,
                   si.product_id, p.name as product_name, si.qty, si.price, p.model_code
            FROM sales s
            JOIN sale_items si ON s.bill_id = si.bill_id
            LEFT JOIN products p ON si.product_id = p.id
            ORDER BY s.date DESC, s.bill_id DESC
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_detailed_transactions_report(self, start_date, end_date):
        query = """
            SELECT s.bill_id, s.date, s.session_id, s.transaction_type, s.payment_method,
                   s.customer_phone, s.customer_name, s.total, s.discount_type, s.discount_amount,
                   si.product_id, p.name as product_name, si.qty, si.price, p.model_code
            FROM sales s
            JOIN sale_items si ON s.bill_id = si.bill_id
            LEFT JOIN products p ON si.product_id = p.id
            WHERE s.date >= ? AND s.date <= ?
            ORDER BY s.date DESC, s.bill_id DESC
        """
        self.cursor.execute(query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        return self.cursor.fetchall()

    def get_detailed_transactions_by_session(self, session_id):
        query = """
            SELECT s.bill_id, s.date, s.session_id, s.transaction_type, s.payment_method,
                   s.customer_phone, s.customer_name, s.total, s.discount_type, s.discount_amount,
                   si.product_id, p.name as product_name, si.qty, si.price, p.model_code
            FROM sales s
            JOIN sale_items si ON s.bill_id = si.bill_id
            LEFT JOIN products p ON si.product_id = p.id
            WHERE s.session_id = ?
            ORDER BY s.date DESC, s.bill_id DESC
        """
        self.cursor.execute(query, (session_id,))
        return self.cursor.fetchall()

    def get_detailed_transactions_last_n_sessions(self, n):
        self.cursor.execute("SELECT session_id FROM daily_sessions WHERE status='CLOSED' ORDER BY session_id DESC LIMIT ?", (n,))
        sessions = [row[0] for row in self.cursor.fetchall()]
        if not sessions: return []

        placeholders = ','.join('?' * len(sessions))
        query = f"""
            SELECT s.bill_id, s.date, s.session_id, s.transaction_type, s.payment_method,
                   s.customer_phone, s.customer_name, s.total, s.discount_type, s.discount_amount,
                   si.product_id, p.name as product_name, si.qty, si.price, p.model_code
            FROM sales s
            JOIN sale_items si ON s.bill_id = si.bill_id
            LEFT JOIN products p ON si.product_id = p.id
            WHERE s.session_id IN ({placeholders})
            ORDER BY s.date DESC, s.bill_id DESC
        """
        self.cursor.execute(query, sessions)
        return self.cursor.fetchall()

    def get_unique_model_codes(self):
        self.cursor.execute("SELECT DISTINCT model_code FROM products WHERE model_code IS NOT NULL ORDER BY model_code")
        return [row[0] for row in self.cursor.fetchall() if row[0]]

    def get_session_total_sales(self, session_id):
        if not session_id: return 0.0
        self.cursor.execute("SELECT SUM(total) FROM sales WHERE session_id=?", (session_id,))
        res = self.cursor.fetchone()
        return res[0] if res and res[0] else 0.0

    def get_all_customers_report(self):
        self.cursor.execute("SELECT phone, name, total_spent, last_date, last_item FROM customers ORDER BY total_spent DESC")
        return self.cursor.fetchall()

    def get_customer_transactions(self, phone):
        self.cursor.execute("""
            SELECT bill_id, date, total, payment_method, transaction_type 
            FROM sales WHERE customer_phone=? ORDER BY date DESC
        """, (phone,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()