# main.py - Entry point aplikasi SIGAP
# Titik masuk utama untuk menjalankan aplikasi SIGAP

"""
SIGAP - Sistem Informasi Pengaduan dan Aspirasi Publik
=====================================================
Aplikasi desktop native untuk manajemen pengaduan 
fasilitas publik terpadu.

Usage:
    python main.py
"""

import customtkinter as ctk
from config.settings import APP_NAME, APP_VERSION, APPEARANCE_MODE, COLOR_THEME
from config.database import DatabaseConnection
from views.auth.login_view import LoginView


class SIGAPApp(ctk.CTk):
    """Kelas utama aplikasi SIGAP."""

    def __init__(self):
        super().__init__()
        
        # Konfigurasi window utama
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x720")
        self.minsize(1024, 600)
        
        # Set appearance
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)
        
        # Inisialisasi koneksi database
        self.db = DatabaseConnection()
        
        # State management - menyimpan data user yang sedang login
        self.current_user = None
        
        # Container utama
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        # Tampilkan halaman login sebagai default
        self.show_login()
    
    def show_login(self):
        """Tampilkan halaman login."""
        self._clear_container()
        LoginView(self.container, app=self).pack(fill="both", expand=True)
    
    def show_dashboard(self, user_data: dict):
        """Tampilkan dashboard sesuai role user yang login."""
        self.current_user = user_data
        self._clear_container()
        
        role = user_data.get("role")
        
        if role == "warga":
            from views.warga.dashboard_warga import DashboardWarga
            DashboardWarga(self.container, app=self).pack(fill="both", expand=True)
        elif role == "admin_kelurahan":
            from views.admin_kelurahan.dashboard_kelurahan import DashboardKelurahan
            DashboardKelurahan(self.container, app=self).pack(fill="both", expand=True)
        elif role == "admin_kecamatan":
            from views.admin_kecamatan.dashboard_kecamatan import DashboardKecamatan
            DashboardKecamatan(self.container, app=self).pack(fill="both", expand=True)
        elif role == "admin_kota":
            from views.admin_kota.dashboard_kota import DashboardKota
            DashboardKota(self.container, app=self).pack(fill="both", expand=True)
    
    def logout(self):
        """Logout user dan kembali ke halaman login."""
        self.current_user = None
        self.show_login()
    
    def _clear_container(self):
        """Hapus semua widget dari container utama."""
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def on_closing(self):
        """Handler saat aplikasi ditutup."""
        if self.db:
            self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = SIGAPApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
