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

import os
import customtkinter as ctk
from PIL import Image, ImageTk
from config.settings import APP_NAME, APP_VERSION, APPEARANCE_MODE, COLOR_THEME
from config.database import DatabaseConnection
from views.auth.login_view import LoginView

# Logo path
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "sigap_icon.PNG")

# Inactivity timeout (30 minutes in milliseconds)
INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000  # 30 minutes
WARNING_BEFORE_MS = 60 * 1000  # Show warning 1 minute before timeout


class SIGAPApp(ctk.CTk):
    """Kelas utama aplikasi SIGAP."""

    def __init__(self):
        super().__init__()
        
        # Konfigurasi window utama
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x720")
        self.minsize(1024, 600)
        
        # Set window icon
        if os.path.exists(LOGO_PATH):
            icon_img = Image.open(LOGO_PATH)
            self._icon_photo = ImageTk.PhotoImage(icon_img.resize((32, 32)))
            self.iconphoto(True, self._icon_photo)

        # Set appearance
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)
        
        # Inisialisasi koneksi database
        self.db = DatabaseConnection()
        
        # State management
        self.current_user = None
        
        # Inactivity timer state
        self._inactivity_timer_id = None
        self._warning_timer_id = None
        self._warning_dialog = None
        self._activity_bound = False
        
        # Container utama
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        # Tampilkan halaman login
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
        
        # Start inactivity monitoring
        self._start_inactivity_monitor()
    
    def logout(self):
        """Logout user dan kembali ke halaman login."""
        self._stop_inactivity_monitor()
        self.current_user = None
        self.show_login()
    
    def _clear_container(self):
        """Hapus semua widget dari container utama."""
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def on_closing(self):
        """Handler saat aplikasi ditutup."""
        self._stop_inactivity_monitor()
        if self.db:
            self.db.close()
        self.destroy()
    
    # ──────────────────────────────────────────────
    # INACTIVITY TIMEOUT (30 menit)
    # ──────────────────────────────────────────────
    
    def _start_inactivity_monitor(self):
        """Start monitoring user inactivity."""
        self._stop_inactivity_monitor()  # Clear any existing timers
        
        # Bind activity events
        if not self._activity_bound:
            self.bind_all("<Motion>", self._on_activity, add="+")
            self.bind_all("<Key>", self._on_activity, add="+")
            self.bind_all("<Button>", self._on_activity, add="+")
            self.bind_all("<MouseWheel>", self._on_activity, add="+")
            self._activity_bound = True
        
        self._reset_inactivity_timer()
    
    def _stop_inactivity_monitor(self):
        """Stop monitoring user inactivity."""
        if self._inactivity_timer_id:
            self.after_cancel(self._inactivity_timer_id)
            self._inactivity_timer_id = None
        if self._warning_timer_id:
            self.after_cancel(self._warning_timer_id)
            self._warning_timer_id = None
        if self._warning_dialog:
            try:
                self._warning_dialog.destroy()
            except Exception:
                pass
            self._warning_dialog = None
        
        # Unbind events
        if self._activity_bound:
            try:
                self.unbind_all("<Motion>")
                self.unbind_all("<Key>")
                self.unbind_all("<Button>")
                self.unbind_all("<MouseWheel>")
            except Exception:
                pass
            self._activity_bound = False
    
    def _on_activity(self, event=None):
        """Called on any user activity — reset the timer."""
        if self.current_user is None:
            return
        self._reset_inactivity_timer()
        
        # Dismiss warning if it's showing
        if self._warning_dialog:
            try:
                self._warning_dialog.destroy()
            except Exception:
                pass
            self._warning_dialog = None
    
    def _reset_inactivity_timer(self):
        """Reset the inactivity timer."""
        # Cancel existing timers
        if self._inactivity_timer_id:
            self.after_cancel(self._inactivity_timer_id)
        if self._warning_timer_id:
            self.after_cancel(self._warning_timer_id)
        
        # Set warning timer (fires 1 minute before timeout)
        warning_time = INACTIVITY_TIMEOUT_MS - WARNING_BEFORE_MS
        self._warning_timer_id = self.after(warning_time, self._show_timeout_warning)
        
        # Set logout timer
        self._inactivity_timer_id = self.after(INACTIVITY_TIMEOUT_MS, self._auto_logout)
    
    def _show_timeout_warning(self):
        """Show warning dialog before auto-logout."""
        if self._warning_dialog:
            return
        
        self._warning_dialog = ctk.CTkToplevel(self)
        dialog = self._warning_dialog
        dialog.title("Peringatan Sesi")
        dialog.geometry("420x240")
        dialog.resizable(False, False)
        dialog.configure(fg_color=("white", "gray17"))
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 210
        y = (dialog.winfo_screenheight() // 2) - 120
        dialog.geometry(f"+{x}+{y}")
        
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_force()
        
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=25)
        
        ctk.CTkLabel(
            content, text="⏰",
            font=ctk.CTkFont(size=42)
        ).pack(pady=(0, 8))
        
        ctk.CTkLabel(
            content, text="Sesi Akan Berakhir",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=("#2F4156", "#87CEEB")
        ).pack(pady=(0, 6))
        
        self._timeout_countdown = 60
        self._timeout_label = ctk.CTkLabel(
            content,
            text=f"Anda akan otomatis logout dalam 60 detik karena tidak ada aktivitas.",
            font=ctk.CTkFont(size=13),
            text_color=("gray45", "gray60"),
            wraplength=360, justify="center"
        )
        self._timeout_label.pack(pady=(0, 18))
        
        ctk.CTkButton(
            content, text="Tetap Masuk",
            height=38, corner_radius=8, width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#567C8D", "#567C8D"),
            hover_color=("#2F4156", "#2F4156"),
            text_color="white",
            command=self._dismiss_warning
        ).pack()
        
        dialog.protocol("WM_DELETE_WINDOW", self._dismiss_warning)
        
        # Start countdown
        self._tick_timeout_warning()
    
    def _tick_timeout_warning(self):
        """Tick the timeout warning countdown."""
        if not self._warning_dialog or self._timeout_countdown <= 0:
            return
        
        self._timeout_countdown -= 1
        try:
            self._timeout_label.configure(
                text=f"Anda akan otomatis logout dalam {self._timeout_countdown} detik karena tidak ada aktivitas."
            )
        except Exception:
            return
        
        if self._timeout_countdown > 0:
            self._warning_dialog.after(1000, self._tick_timeout_warning)
    
    def _dismiss_warning(self):
        """Dismiss the timeout warning and reset timer."""
        if self._warning_dialog:
            try:
                self._warning_dialog.grab_release()
                self._warning_dialog.destroy()
            except Exception:
                pass
            self._warning_dialog = None
        self._reset_inactivity_timer()
    
    def _auto_logout(self):
        """Auto-logout due to inactivity."""
        if self._warning_dialog:
            try:
                self._warning_dialog.grab_release()
                self._warning_dialog.destroy()
            except Exception:
                pass
            self._warning_dialog = None
        
        if self.current_user:
            self.logout()


if __name__ == "__main__":
    app = SIGAPApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
