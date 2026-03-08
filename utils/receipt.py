# """
# ملف مسؤول عن توليد وطباعة الفاتورة الحرارية (80mm) 
# وتمت إضافة اختيار الطابعة الافتراضية تلقائياً
# """

# import os
# import tempfile
# from tkinter import messagebox
# from config import LOGO_FILENAME
# import win32print

# def set_default_printer(printer_name="XP-80C"):
#     """دالة لضبط الطابعة الافتراضية"""
#     try:
#         printers = [p[2] for p in win32print.EnumPrinters(2)]
#         if printer_name in printers:
#             win32print.SetDefaultPrinter(printer_name)
#             return True
#         return False
#     except:
#         return False

# def print_receipt(self, bid, date, total, method, tr_type, discount=0, discount_type="بدون خصم", original=None):
#     # محاولة تعيين الطابعة الحرارية كافتراضية قبل الطباعة
#     set_default_printer("XP-80C")
    
#     try:
#         import arabic_reshaper
#         from bidi.algorithm import get_display
#         from PIL import Image, ImageDraw, ImageFont, ImageWin
#         import win32print
#         import win32ui
#     except ImportError:
#         messagebox.showerror(
#             "نقص مكتبات",
#             "المكتبات المطلوبة للطباعة غير مثبتة.\n\n"
#             "افتح الطرفية واكتب:\n"
#             "pip install pillow pywin32 arabic-reshaper python-bidi"
#         )
#         return

#     def ar(text):
#         return get_display(arabic_reshaper.reshape(str(text)))

#     img_w = 576
#     curr_y = 20 # ترك مسافة علوية صغيرة في بداية الورقة
#     img = Image.new('RGB', (img_w, 3500), color='white') # زيادة أقصى طول لتجنب أي قطع
#     draw = ImageDraw.Draw(img)

#     try:
#         font_xs   = ImageFont.truetype("arial.ttf",   18)
#         font_sm   = ImageFont.truetype("arial.ttf",   22)
#         font_reg  = ImageFont.truetype("arial.ttf",   26)
#         font_bd   = ImageFont.truetype("arialbd.ttf", 32)
#         font_title = ImageFont.truetype("arialbd.ttf", 45)

#         # --- حل مشكلة تداخل اللوجو ---
#         if os.path.exists(LOGO_FILENAME):
#             try:
#                 logo = Image.open(LOGO_FILENAME).convert("RGBA")
#                 logo.thumbnail((200, 200)) # تصغير اللوجو قليلاً ليتناسب بشكل أفضل
#                 logo_w, logo_h = logo.size # قراءة الأبعاد الحقيقية بعد التصغير
#                 img.paste(logo, (int((img_w - logo_w) / 2), int(curr_y)), logo)
#                 curr_y += logo_h + 40 # إضافة ارتفاع اللوجو + 40 بكسل مسافة أمان تحته
#             except Exception as logo_err:
#                 print("خطأ في تحميل اللوجو:", logo_err)

#         draw.text((img_w / 2, curr_y), ar("3SSAM MEN'S WEAR"), fill='black', font=font_title, anchor="mm")
#         curr_y += 60 # زيادة المسافة
        
#         draw.text((img_w / 2, curr_y), ar("الفيوم - لطف الله"), fill='black', font=font_reg, anchor="mm")
#         curr_y += 50

#         draw.line([(10, curr_y), (img_w - 10, curr_y)], fill='black', width=3)
#         curr_y += 30

#         dt_parts = str(date).split(' ')
#         d_str = dt_parts[0]
#         t_str = dt_parts[1] if len(dt_parts) > 1 else ""

#         draw.text((img_w - 15, curr_y), ar(f"رقم الفاتورة: {bid}"), fill='black', font=font_reg, anchor="rm")
#         draw.text((15, curr_y), ar(f"التاريخ: {d_str}"), fill='black', font=font_reg, anchor="lm")
#         curr_y += 45

#         draw.text((img_w - 15, curr_y), ar(f"نوع العملية: {tr_type}"), fill='black', font=font_bd, anchor="rm")
#         draw.text((15, curr_y), ar(f"الوقت: {t_str}"), fill='black', font=font_reg, anchor="lm")
#         curr_y += 55

#         if discount_type != "بدون خصم":
#             draw.text((img_w / 2, curr_y), ar(f"شامل عرض: {discount_type}"), fill='black', font=font_bd, anchor="mm")
#             curr_y += 50

#         # --- تنسيق الجدول ---
#         row_h = 50 # زيادة ارتفاع السطر في الجدول ليكون مريحاً للعين
#         draw.rectangle([(10, curr_y), (img_w - 10, curr_y + row_h)], outline='black', width=2)
#         draw.text((430, curr_y + 25), ar("اسم المنتج"), fill='black', font=font_bd, anchor="mm")
#         draw.text((220, curr_y + 25), ar("الكمية"),    fill='black', font=font_bd, anchor="mm")
#         draw.text((95,  curr_y + 25), ar("الإجمالي"),  fill='black', font=font_bd, anchor="mm")

#         draw.line([(280, curr_y), (280, curr_y + row_h)], fill='black', width=2)
#         draw.line([(160, curr_y), (160, curr_y + row_h)], fill='black', width=2)
#         curr_y += row_h

#         for item in getattr(self, 'cart', []):
#             draw.rectangle([(10, curr_y), (img_w - 10, curr_y + row_h)], outline='black', width=1)
#             prod_name = ar(item.get('name', '')[:22])
#             qty_str   = ar(str(item.get('qty', 1)))
#             total_str = ar(f"{item.get('total', 0):g}")

#             draw.text((img_w - 20, curr_y + 25), prod_name,  fill='black', font=font_reg, anchor="rm")
#             draw.text((220,       curr_y + 25), qty_str,     fill='black', font=font_reg, anchor="mm")
#             draw.text((95,        curr_y + 25), total_str,   fill='black', font=font_reg, anchor="mm")

#             draw.line([(280, curr_y), (280, curr_y + row_h)], fill='black', width=1)
#             draw.line([(160, curr_y), (160, curr_y + row_h)], fill='black', width=1)
#             curr_y += row_h

#         curr_y += 40
#         cname = "عميل نقدي"
#         if hasattr(self, 'ent_name'):
#             cname = self.ent_name.get().strip() or "عميل نقدي"

#         draw.text((img_w - 15, curr_y), ar(f"اسم العميل: {cname}"), fill='black', font=font_bd, anchor="rm")
#         curr_y += 60

#         draw.text((img_w - 15, curr_y), ar(f"طريقة الدفع: {method}"), fill='black', font=font_reg, anchor="rm")
#         draw.text((15, curr_y), ar(f"الإجمالي: {abs(total):g} EGP"), fill='black', font=font_bd, anchor="lm")
#         curr_y += 55

#         if discount > 0:
#             draw.text((15, curr_y), ar(f"قيمة الخصم: {discount:g} EGP"), fill='black', font=font_sm, anchor="lm")
#             curr_y += 45

#         draw.line([(10, curr_y), (img_w - 10, curr_y)], fill='black', width=2)
#         curr_y += 35

#         policy = "سياسة الاستبدال والاسترجاع خلال 30 يوم بشرط سلامة المنتج."
#         draw.text((img_w / 2, curr_y), ar(policy), fill='black', font=font_sm, anchor="mm")
#         curr_y += 50

#         # --- إضافة حقوق المطور المطلوبة ---
#         draw.text((img_w / 2, curr_y), "- - - - - - - - - - - - - - - - - - - -", fill='black', font=font_sm, anchor="mm")
#         curr_y += 35
        
#         dev_text = "Developed by Mohamed Magdy 01093272709"
#         # لم نستخدم ar() هنا لأن النص إنجليزي وأرقام حتى لا يتم تشويهه
#         draw.text((img_w / 2, curr_y), dev_text, fill='black', font=font_sm, anchor="mm")
        
#         # --- حل مشكلة الكلام المقطوع في الأسفل ---
#         curr_y += 130 # إضافة هامش سفلي كبير جداً لضمان تجاوز شفرة القص في الطابعة

#         final_img = img.crop((0, 0, img_w, int(curr_y))).convert("RGB")
#         temp_dir = tempfile.gettempdir()
#         tmp_img = os.path.join(temp_dir, "receipt_print.bmp")
#         final_img.save(tmp_img)

#         try:
#             printer_name = win32print.GetDefaultPrinter()
#             hDC = win32ui.CreateDC()
#             hDC.CreatePrinterDC(printer_name)

#             bmp = Image.open(tmp_img)
#             printer_width = int(hDC.GetDeviceCaps(8)) 
#             printer_height = int(bmp.size[1] * (printer_width / bmp.size[0]))

#             hDC.StartDoc("Receipt")
#             hDC.StartPage()
#             dib = ImageWin.Dib(bmp)
#             dib.draw(hDC.GetHandleOutput(), (0, 0, printer_width, printer_height))
#             hDC.EndPage()
#             hDC.EndDoc()
#             hDC.DeleteDC()
#         except Exception as print_err:
#             messagebox.showerror("خطأ في الطابعة", f"{print_err}\n\nاسم الطابعة الحالي: {win32print.GetDefaultPrinter()}")

#         try:
#             os.remove(tmp_img)
#         except:
#             pass

#     except Exception as e:
#         messagebox.showerror("خطأ في تصميم الفاتورة", f"{str(e)}")
#         try:
#             os.remove(tmp_img)
#         except:
#             pass



"""
ملف مسؤول عن توليد وطباعة الفاتورة الحرارية (80mm) 
وتمت إضافة اختيار الطابعة الافتراضية تلقائياً والتوافق مع الـ PDF
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
    # محاولة تعيين الطابعة الحرارية كافتراضية قبل الطباعة
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
    curr_y = 20 # مسافة علوية
    # مساحة بيضاء مبدئية عملاقة لضمان عدم حدوث أي قص برمجي
    img = Image.new('RGB', (img_w, 4000), color='white') 
    draw = ImageDraw.Draw(img)

    try:
        font_xs   = ImageFont.truetype("arial.ttf",   20)
        font_sm   = ImageFont.truetype("arial.ttf",   22)
        font_reg  = ImageFont.truetype("arial.ttf",   26)
        font_bd   = ImageFont.truetype("arialbd.ttf", 32)
        font_title = ImageFont.truetype("arialbd.ttf", 45)
        # خط خاص بحقوق المطور
        font_dev  = ImageFont.truetype("arialbd.ttf", 24)

        if os.path.exists(LOGO_FILENAME):
            try:
                logo = Image.open(LOGO_FILENAME).convert("RGBA")
                logo.thumbnail((200, 200)) 
                logo_w, logo_h = logo.size 
                img.paste(logo, (int((img_w - logo_w) / 2), int(curr_y)), logo)
                curr_y += logo_h + 40 
            except Exception as logo_err:
                print("خطأ في تحميل اللوجو:", logo_err)

        draw.text((img_w / 2, curr_y), ar("3SSAM MEN'S WEAR"), fill='black', font=font_title, anchor="mm")
        curr_y += 60
        
        draw.text((img_w / 2, curr_y), ar("الفيوم - لطف الله"), fill='black', font=font_reg, anchor="mm")
        curr_y += 50

        draw.line([(10, curr_y), (img_w - 10, curr_y)], fill='black', width=3)
        curr_y += 30

        dt_parts = str(date).split(' ')
        d_str = dt_parts[0]
        t_str = dt_parts[1] if len(dt_parts) > 1 else ""

        draw.text((img_w - 15, curr_y), ar(f"رقم الفاتورة: {bid}"), fill='black', font=font_reg, anchor="rm")
        draw.text((15, curr_y), ar(f"التاريخ: {d_str}"), fill='black', font=font_reg, anchor="lm")
        curr_y += 45

        draw.text((img_w - 15, curr_y), ar(f"نوع العملية: {tr_type}"), fill='black', font=font_bd, anchor="rm")
        draw.text((15, curr_y), ar(f"الوقت: {t_str}"), fill='black', font=font_reg, anchor="lm")
        curr_y += 55

        if discount_type != "بدون خصم":
            draw.text((img_w / 2, curr_y), ar(f"شامل عرض: {discount_type}"), fill='black', font=font_bd, anchor="mm")
            curr_y += 50

        # --- رسم الجدول ---
        row_h = 50 
        draw.rectangle([(10, curr_y), (img_w - 10, curr_y + row_h)], outline='black', width=2)
        draw.text((430, curr_y + 25), ar("اسم المنتج"), fill='black', font=font_bd, anchor="mm")
        draw.text((220, curr_y + 25), ar("الكمية"),    fill='black', font=font_bd, anchor="mm")
        draw.text((95,  curr_y + 25), ar("الإجمالي"),  fill='black', font=font_bd, anchor="mm")

        draw.line([(280, curr_y), (280, curr_y + row_h)], fill='black', width=2)
        draw.line([(160, curr_y), (160, curr_y + row_h)], fill='black', width=2)
        curr_y += row_h

        for item in getattr(self, 'cart', []):
            draw.rectangle([(10, curr_y), (img_w - 10, curr_y + row_h)], outline='black', width=1)
            prod_name = ar(item.get('name', '')[:22])
            qty_str   = ar(str(item.get('qty', 1)))
            total_str = ar(f"{item.get('total', 0):g}")

            draw.text((img_w - 20, curr_y + 25), prod_name,  fill='black', font=font_reg, anchor="rm")
            draw.text((220,       curr_y + 25), qty_str,     fill='black', font=font_reg, anchor="mm")
            draw.text((95,        curr_y + 25), total_str,   fill='black', font=font_reg, anchor="mm")

            draw.line([(280, curr_y), (280, curr_y + row_h)], fill='black', width=1)
            draw.line([(160, curr_y), (160, curr_y + row_h)], fill='black', width=1)
            curr_y += row_h

        curr_y += 40
        cname = "عميل نقدي"
        if hasattr(self, 'ent_name'):
            cname = self.ent_name.get().strip() or "عميل نقدي"

        draw.text((img_w - 15, curr_y), ar(f"اسم العميل: {cname}"), fill='black', font=font_bd, anchor="rm")
        curr_y += 60

        draw.text((img_w - 15, curr_y), ar(f"طريقة الدفع: {method}"), fill='black', font=font_reg, anchor="rm")
        draw.text((15, curr_y), ar(f"الإجمالي: {abs(total):g} EGP"), fill='black', font=font_bd, anchor="lm")
        curr_y += 55

        if discount > 0:
            draw.text((15, curr_y), ar(f"قيمة الخصم: {discount:g} EGP"), fill='black', font=font_sm, anchor="lm")
            curr_y += 45

        draw.line([(10, curr_y), (img_w - 10, curr_y)], fill='black', width=2)
        curr_y += 35

        policy = "سياسة الاستبدال والاسترجاع خلال 30 يوم بشرط سلامة المنتج."
        draw.text((img_w / 2, curr_y), ar(policy), fill='black', font=font_sm, anchor="mm")
        curr_y += 50

        draw.text((img_w / 2, curr_y), "- - - - - - - - - - - - - - - - - - -", fill='black', font=font_sm, anchor="mm")
        curr_y += 45
        
        # --- حقوق المطور ---
        dev_text = "Developed by Mohamed Magdy 01093272709"
        draw.text((img_w / 2, curr_y), dev_text, fill='black', font=font_dev, anchor="mm")
        
        curr_y += 120 # هامش سفلي للقص

        # قص الصورة لتكون على قد المحتوى الفعلي
        final_img = img.crop((0, 0, img_w, int(curr_y))).convert("RGB")
        temp_dir = tempfile.gettempdir()
        tmp_img = os.path.join(temp_dir, "receipt_print.bmp")
        final_img.save(tmp_img)

        # ---------------- الطباعة الذكية ----------------
        try:
            printer_name = win32print.GetDefaultPrinter()
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)

            bmp = Image.open(tmp_img)
            
            # قراءة أبعاد الطابعة (أو ورقة الـ PDF)
            HORZRES = hDC.GetDeviceCaps(8)  # العرض المتاح للطباعة
            VERTRES = hDC.GetDeviceCaps(10) # الطول المتاح للطباعة

            printer_width = HORZRES
            printer_height = int(bmp.size[1] * (printer_width / float(bmp.size[0])))

            x_offset = 0
            
            # إذا كان ارتفاع الفاتورة أكبر من طول الورقة الوهمية (مثل PDF A4)
            if printer_height > VERTRES:
                # تصغير الفاتورة لتناسب حجم شاشة الـ PDF بالكامل ولا يتم قصها
                ratio = VERTRES / float(printer_height)
                printer_width = int(printer_width * ratio)
                printer_height = VERTRES
                # توسيط الفاتورة في الـ PDF
                x_offset = (HORZRES - printer_width) // 2

            hDC.StartDoc("Receipt")
            hDC.StartPage()
            dib = ImageWin.Dib(bmp)
            dib.draw(hDC.GetHandleOutput(), (x_offset, 0, x_offset + printer_width, printer_height))
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