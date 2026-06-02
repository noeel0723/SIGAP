# config/settings.py
# Konfigurasi umum aplikasi SIGAP

"""
Pengaturan global untuk aplikasi SIGAP.
Semua konstanta konfigurasi dipusatkan di sini agar mudah diubah.
"""

# ──────────────────────────────────────────────
# IDENTITAS APLIKASI
# ──────────────────────────────────────────────
APP_NAME = "SIGAP"
APP_FULL_NAME = "Sistem Informasi Pengaduan dan Aspirasi Publik"
APP_VERSION = "1.0.0"

# ──────────────────────────────────────────────
# KONFIGURASI UI (CustomTkinter)
# ──────────────────────────────────────────────
APPEARANCE_MODE = "light"       # "dark", "light", atau "system"
COLOR_THEME = "blue"            # "blue", "dark-blue", "green"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
MIN_WIDTH = 1024
MIN_HEIGHT = 600

# ──────────────────────────────────────────────
# KONFIGURASI DATABASE (MySQL via Laragon)
# ──────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",              # Default Laragon: tanpa password
    "database": "sigap_db",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "autocommit": True,
}

# ──────────────────────────────────────────────
# ROLE PENGGUNA
# ──────────────────────────────────────────────
ROLES = {
    "warga": "Warga",
    "admin_kelurahan": "Admin Kelurahan",
    "admin_kecamatan": "Admin Kecamatan",
    "admin_kota": "Admin Kota",
}

# ──────────────────────────────────────────────
# STATUS LAPORAN (urutan workflow eskalasi)
# ──────────────────────────────────────────────
STATUS_LAPORAN = [
    "Menunggu",
    "Diproses Kelurahan",
    "Diproses Kecamatan",
    "Diproses Kota",
    "Selesai",
    "Ditolak",
]

# ──────────────────────────────────────────────
# KATEGORI LAPORAN
# ──────────────────────────────────────────────
KATEGORI_LAPORAN = [
    "Jalan & Jembatan",
    "Drainase & Saluran Air",
    "Penerangan Jalan",
    "Kebersihan & Sampah",
    "Taman & Ruang Terbuka Hijau",
    "Fasilitas Kesehatan",
    "Fasilitas Pendidikan",
    "Keamanan & Ketertiban",
    "Transportasi Publik",
    "Lainnya",
]
