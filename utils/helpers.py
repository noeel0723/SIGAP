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
