# utils/helpers.py
# Fungsi utilitas umum

"""
Kumpulan fungsi helper yang digunakan di berbagai modul.
"""

from datetime import datetime


def format_tanggal(dt: datetime, format_str: str = "%d %b %Y, %H:%M") -> str:
    """Format datetime ke string Indonesia-friendly."""
    if dt is None:
        return "-"
    
    bulan_id = {
        "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr",
        "May": "Mei", "Jun": "Jun", "Jul": "Jul", "Aug": "Agu",
        "Sep": "Sep", "Oct": "Okt", "Nov": "Nov", "Dec": "Des",
    }
    
    result = dt.strftime(format_str)
    for en, idn in bulan_id.items():
        result = result.replace(en, idn)
    return result


def truncate_text(text: str, max_length: int = 50) -> str:
    """Potong teks panjang dan tambahkan ellipsis."""
    if text and len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text or ""


def format_status_label(status: str) -> str:
    """Format status untuk ditampilkan di badge."""
    return status.strip() if status else "Unknown"


def validate_email(email: str) -> bool:
    """Validasi sederhana format email."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def klasifikasi_prioritas(judul: str, deskripsi: str) -> str:
    """
    Klasifikasi prioritas laporan secara otomatis berdasarkan kata kunci.
    
    Memeriksa judul dan deskripsi terhadap daftar kata kunci darurat/penting
    yang didefinisikan di config/settings.py.
    
    Returns: 'Tinggi', 'Sedang', atau 'Rendah'
    """
    from config.settings import PRIORITAS_KEYWORDS

    teks = f"{judul} {deskripsi}".lower()

    # Periksa prioritas Tinggi terlebih dahulu (precedence)
    for keyword in PRIORITAS_KEYWORDS.get("Tinggi", []):
        if keyword in teks:
            return "Tinggi"

    # Kemudian periksa Sedang
    for keyword in PRIORITAS_KEYWORDS.get("Sedang", []):
        if keyword in teks:
            return "Sedang"

    return "Rendah"


def save_uploaded_image(source_filepath: str) -> str | None:
    """
    Kopi gambar yang diupload ke folder assets/uploads/ dengan nama unik.
    Returns relative path dari file yang tersimpan (misal: 'assets/uploads/img_12345.jpg')
    """
    import os
    import shutil
    import uuid
    from datetime import datetime

    if not source_filepath or not os.path.isfile(source_filepath):
        return None

    import sys
    if getattr(sys, 'frozen', False):
        # Jika dijalankan dari file .exe (PyInstaller) yang lokasinya berbeda (dist/SIGAP_Admin vs dist/SIGAP_Warga)
        # Gunakan folder bersama di user directory agar Admin dan Warga membaca file fisik yang sama
        base_dir = os.path.join(os.path.expanduser("~"), "SIGAP_Data")
    else:
        # Tentukan direktori upload relatif terhadap root project
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, "assets", "uploads")

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Buat nama unik
    ext = os.path.splitext(source_filepath)[1]
    # Fallback to .jpg if no extension
    if not ext:
        ext = ".jpg"
        
    unique_filename = f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    dest_path = os.path.join(upload_dir, unique_filename)

    try:
        shutil.copy2(source_filepath, dest_path)
        # Return path relatif untuk disimpan ke DB
        return f"assets/uploads/{unique_filename}"
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan gambar: {e}")
        return None
