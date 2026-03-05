import os
import shutil
from datetime import datetime
from config import DB_NAME, BACKUP_DIR

def backup_database():
    """نسخ احتياطي لقاعدة البيانات كل أسبوعين (14 يوماً) تلقائياً"""
    try:
        # التأكد من وجود قاعدة البيانات الأصلية أولاً
        if not os.path.exists(DB_NAME):
            return

        # التأكد من وجود مجلد النسخ الاحتياطي أو إنشائه
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # البحث عن كل ملفات الباك أب القديمة
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
        needs_backup = False

        if not backups:
            # إذا كان المجلد فارغاً ولا يوجد أي باك أب سابق
            needs_backup = True
        else:
            # العثور على أحدث ملف باك أب تم إنشاؤه
            latest_backup = max(backups, key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f)))
            latest_backup_path = os.path.join(BACKUP_DIR, latest_backup)
            
            # حساب عدد الأيام التي مرت منذ آخر باك أب
            file_time = os.path.getmtime(latest_backup_path)
            last_backup_date = datetime.fromtimestamp(file_time)
            days_passed = (datetime.now() - last_backup_date).days
            
            if days_passed >= 14:
                # مر 14 يوماً (أسبوعين) أو أكثر
                needs_backup = True
            else:
                print(f"تخطي الباك أب: آخر نسخة كانت منذ {days_passed} يوم. (المطلوب 14 يوم)")

        # تنفيذ النسخ الاحتياطي إذا لزم الأمر
        if needs_backup:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_path = os.path.join(BACKUP_DIR, f"3ssam_store_backup_{ts}.db")
            shutil.copy2(DB_NAME, backup_path)
            print(f"تم أخذ نسخة احتياطية بنجاح: {backup_path}")

    except Exception as e:
        print(f"خطأ في النسخ الاحتياطي: {e}")