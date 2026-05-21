# views/components/sidebar.py
# Komponen sidebar navigasi reusable

import customtkinter as ctk
from config.settings import APP_NAME, ROLES


class Sidebar(ctk.CTkFrame):
    """Sidebar navigasi utama untuk semua dashboard."""

    def __init__(self, parent, app, menu_items: list[dict], **kwargs):
        super().__init__(parent, width=250, corner_radius=0,
                         fg_color=("gray90", "gray14"), **kwargs)
        self.app = app
        self.pack_propagate(False)

        # ── Logo & Nama Aplikasi ──
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(25, 5))

        ctk.CTkLabel(
            logo_frame, text="📋", font=ctk.CTkFont(size=32)
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_frame, text=APP_NAME,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1565C0", "#42A5F5")
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_frame, text="Pengaduan & Aspirasi Publik",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack(anchor="w")

        # ── Separator ──
        sep = ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray30"))
        sep.pack(fill="x", padx=20, pady=15)

        # ── Info User ──
        user = app.current_user or {}
        user_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray20"),
                                  corner_radius=10)
        user_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            user_frame, text=user.get("nama_lengkap", "User"),
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=200, justify="left"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        role_text = ROLES.get(user.get("role", ""), "")
        ctk.CTkLabel(
            user_frame, text=role_text,
            font=ctk.CTkFont(size=11),
            text_color=("#1E88E5", "#64B5F6")
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # ── Menu Items ──
        menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        menu_frame.pack(fill="x", padx=10, pady=5)

        for item in menu_items:
            icon = item.get("icon", "")
            label = item.get("label", "")
            command = item.get("command", None)

            btn = ctk.CTkButton(
                menu_frame,
                text=f"  {icon}  {label}",
                anchor="w",
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=("gray20", "gray90"),
                hover_color=("gray80", "gray25"),
                command=command
            )
            btn.pack(fill="x", pady=2)

        # ── Spacer ──
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # ── Bottom Section ──
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        # Toggle tema
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_btn = ctk.CTkButton(
            bottom_frame,
            text="  🌙  Mode Gelap/Terang",
            anchor="w",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=("gray40", "gray70"),
            hover_color=("gray80", "gray25"),
            command=self._toggle_theme
        )
        theme_btn.pack(fill="x", pady=2)

        # Tombol Logout
        logout_btn = ctk.CTkButton(
            bottom_frame,
            text="  🚪  Keluar",
            anchor="w",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=("#E53935", "#EF5350"),
            hover_color=("gray80", "gray25"),
            command=self._logout
        )
        logout_btn.pack(fill="x", pady=2)

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def _logout(self):
        from tkinter import messagebox
        if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin keluar?"):
            self.app.logout()
