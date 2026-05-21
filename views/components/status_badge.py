# views/components/status_badge.py
# Komponen badge status laporan dengan warna dinamis

"""
Widget badge kecil yang menampilkan status laporan
dengan warna latar yang berbeda sesuai statusnya.
"""

import customtkinter as ctk

# Mapping warna untuk setiap status
STATUS_COLORS = {
    "Menunggu":             {"bg": "#FFA500", "fg": "#FFFFFF"},  # Orange
    "Diproses Kelurahan":   {"bg": "#3498DB", "fg": "#FFFFFF"},  # Blue
    "Diproses Kecamatan":   {"bg": "#9B59B6", "fg": "#FFFFFF"},  # Purple
    "Diproses Kota":        {"bg": "#E67E22", "fg": "#FFFFFF"},  # Dark Orange
    "Selesai":              {"bg": "#27AE60", "fg": "#FFFFFF"},  # Green
    "Ditolak":              {"bg": "#E74C3C", "fg": "#FFFFFF"},  # Red
}


class StatusBadge(ctk.CTkLabel):
    """Badge label berwarna untuk menampilkan status laporan."""

    def __init__(self, parent, status: str, **kwargs):
        colors = STATUS_COLORS.get(status, {"bg": "#95A5A6", "fg": "#FFFFFF"})
        super().__init__(
            parent,
            text=f"  {status}  ",
            fg_color=colors["bg"],
            text_color=colors["fg"],
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            **kwargs
        )
