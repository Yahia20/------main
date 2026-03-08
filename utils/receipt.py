"""
ملف مسؤول عن توليد وطباعة الفاتورة الحرارية (80mm) 
وتمت إضافة اختيار الطابعة الافتراضية تلقائياً
"""

import os
import tempfile
from tkinter import messagebox
from config import LOGO_FILENAME
import win32print

def set_default_printer(printer_name="XP-80C"):
    """دالة لضبط الطابعة الافتراضية"""
    try:
        printers = [p[2] for p in win32print.EnumPrinters(2)]
        if printer_name in printers:
            win32print.SetDefaultPrinter(printer_name)
            return True
        return False
    except:
        return False

def print_receipt(self, bid, date, total, method, tr_type, discount=0, discount_type="بدون خصم", original=None):
    set_default_printer("XP-80C")
    
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        from PIL import Image, ImageDraw, ImageFont, ImageWin
        import win32print
        import win32ui
    except ImportError:
        messagebox.showerror(
            "نقص مكتبات",
            "المكتبات المطلوبة للطباعة غير مثبتة.\n\n"
            "افتح الطرفية واكتب:\n"
            "pip install pillow pywin32 arabic-reshaper python-bidi"
        )
        return

    def ar(text):
        return get_display(arabic_reshaper.reshape(str(text)))

    img_w = 576
    curr_y = 10
    img = Image.new('RGB', (img_w, 2500), color='white')
    draw = ImageDraw.Draw(img)

    try:
        font_xs   = ImageFont.truetype("arial.ttf",   18)
        font_sm   = ImageFont.truetype("arial.ttf",   22)
        font_reg  = ImageFont.truetype("arial.ttf",   26)
        font_bd   = ImageFont.truetype("arialbd.ttf", 32)
        font_title = ImageFont.truetype("arialbd.ttf", 45)

        if os.path.exists(LOGO_FILENAME):
            try:
                logo = Image.open(LOGO_FILENAME).convert("RGBA")
                logo.thumbnail((220, 220))
                img.paste(logo, (int((img_w - 220) / 2), curr_y), logo)
                curr_y += 230
            except Exception as logo_err:
                print("خطأ في تحميل اللوجو:", logo_err)

        draw.text((img_w / 2, curr_y), ar("3SSAM MEN'S WEAR"), fill='black', font=font_title, anchor="mm")
        curr_y += 55
        draw.text((img_w / 2, curr_y), ar("الفيوم - لطف الله"), fill='black', font=font_reg, anchor="mm")
        curr_y += 45

        draw.line([(10, curr_y), (img_w - 10, curr_y)], fill='black', width=3)
        curr_y += 20

        dt_parts = str(date).split(' ')
        d_str = dt_parts[0]
        t_str = dt_parts[1] if len(dt_parts) > 1 else ""

        draw.text((img_w - 15, curr_y), ar(f"رقم الفاتورة: {bid}"), fill='black', font=font_reg, anchor="rm")
        draw.text((15, curr_y), ar(f"التاريخ: {d_str}"), fill='black', font=font_reg, anchor="lm")
        curr_y += 35

        draw.text((img_w - 15, curr_y), ar(f"نوع العملية: {tr_type}"), fill='black', font=font_bd, anchor="rm")
        draw.text((15, curr_y), ar(f"الوقت: {t_str}"), fill='black', font=font_reg, anchor="lm")
        curr_y += 45

        # التعديل: إظهار نوع العرض إن وجد في הפاتورة
        if discount_type != "بدون خصم":
            draw.text((img_w / 2, curr_y), ar(f"شامل عرض: {discount_type}"), fill='black', font=font_bd, anchor="mm")
            curr_y += 40

        row_h = 45
        draw.rectangle([(10, curr_y), (img_w - 10, curr_y + row_h)], outline='black', width=2)
        draw.text((430, curr_y + 22), ar("اسم المنتج"), fill='black', font=font_bd, anchor="mm")
        draw.text((220, curr_y + 22), ar("الكمية"),    fill='black', font=font_bd, anchor="mm")
        draw.text((95,  curr_y + 22), ar("الإجمالي"),  fill='black', font=font_bd, anchor="mm")

        draw.line([(280, curr_y), (280, curr_y + row_h)], fill='black', width=2)
        draw.line([(160, curr_y), (160, curr_y + row_h)], fill='black', width=2)
        curr_y += row_h

        for item in getattr(self, 'cart', []):
            draw.rectangle([(10, curr_y), (img_w - 10, curr_y + row_h)], outline='black', width=1)
            prod_name = ar(item.get('name', '')[:22])
            qty_str   = ar(str(item.get('qty', 1)))
            total_str = ar(f"{item.get('total', 0):g}")

            draw.text((img_w - 20, curr_y + 22), prod_name,  fill='black', font=font_reg, anchor="rm")
            draw.text((220,       curr_y + 22), qty_str,     fill='black', font=font_reg, anchor="mm")
            draw.text((95,        curr_y + 22), total_str,   fill='black', font=font_reg, anchor="mm")

            draw.line([(280, curr_y), (280, curr_y + row_h)], fill='black', width=1)
            draw.line([(160, curr_y), (160, curr_y + row_h)], fill='black', width=1)
            curr_y += row_h

        curr_y += 30
        cname = "عميل نقدي"
        if hasattr(self, 'ent_name'):
            cname = self.ent_name.get().strip() or "عميل نقدي"

        draw.text((img_w - 15, curr_y), ar(f"اسم العميل: {cname}"), fill='black', font=font_bd, anchor="rm")
        curr_y += 55

        draw.text((img_w - 15, curr_y), ar(f"طريقة الدفع: {method}"), fill='black', font=font_reg, anchor="rm")
        draw.text((img_w / 2 + 20, curr_y), "|", fill='black', font=font_reg, anchor="mm")
        draw.text((15, curr_y), ar(f"الإجمالي: {abs(total):g} EGP"), fill='black', font=font_bd, anchor="lm")
        curr_y += 45

        if discount > 0:
            draw.text((15, curr_y), ar(f"قيمة الخصم: {discount:g} EGP"), fill='black', font=font_sm, anchor="lm")
            curr_y += 35

        draw.line([(10, curr_y), (img_w - 10, curr_y)], fill='black', width=2)
        curr_y += 25

        policy = "سياسة الاستبدال والاسترجاع خلال 30 يوم بشرط سلامة المنتج."
        draw.text((img_w / 2, curr_y), ar(policy), fill='black', font=font_sm, anchor="mm")
        curr_y += 40

        dev_text = "System Developed By : Mohamed magdy 01093272709"
        draw.text((img_w / 2, curr_y), dev_text, fill='black', font=font_xs, anchor="mm")
        curr_y += 60

        final_img = img.crop((0, 0, img_w, curr_y)).convert("RGB")
        temp_dir = tempfile.gettempdir()
        tmp_img = os.path.join(temp_dir, "receipt_print.bmp")
        final_img.save(tmp_img)

        try:
            printer_name = win32print.GetDefaultPrinter()
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)

            bmp = Image.open(tmp_img)
            printer_width = int(hDC.GetDeviceCaps(8)) 
            printer_height = int(bmp.size[1] * (printer_width / bmp.size[0]))

            hDC.StartDoc("Receipt")
            hDC.StartPage()
            dib = ImageWin.Dib(bmp)
            dib.draw(hDC.GetHandleOutput(), (0, 0, printer_width, printer_height))
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
        except Exception as print_err:
            messagebox.showerror("خطأ في الطابعة", f"{print_err}\n\nاسم الطابعة الحالي: {win32print.GetDefaultPrinter()}")

        try:
            os.remove(tmp_img)
        except:
            pass

    except Exception as e:
        messagebox.showerror("خطأ في تصميم الفاتورة", f"{str(e)}")
        try:
            os.remove(tmp_img)
        except:
            pass