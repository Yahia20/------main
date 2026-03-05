import os
from pathlib import Path

# المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_FILENAME = ASSETS_DIR / "logo.png"
DB_NAME = BASE_DIR / "3ssam_store.db"
BACKUP_DIR = ASSETS_DIR / "backups"

# الألوان (الهوية البصرية)
COLOR_BG = "#3A4032"
COLOR_HEADER = "#2B3026"
COLOR_ACCENT = "#D4AF37"
COLOR_TEXT = "#FFFFFF"
COLOR_PANEL = "#F5F5F5"
COLOR_WARNING = "#e74c3c"
COLOR_SUCCESS = "#27ae60"

# كلمة مرور المدير 
ADMIN_PASSWORD = "1234"