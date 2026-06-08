# views/components/sidebar.py
# Komponen sidebar navigasi reusable

import os
import customtkinter as ctk
from PIL import Image
from config.settings import APP_NAME, ROLES

# Logo path
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "IMG_8046.PNG")


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

        # Load logo image
        if os.path.exists(LOGO_PATH):
            logo_img = Image.open(LOGO_PATH)
            self._logo_ctk = ctk.CTkImage(light_image=logo_img,
                                            dark_image=logo_img,
                                            size=(48, 48))
            ctk.CTkLabel(
                logo_frame, image=self._logo_ctk, text=""
            ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                logo_frame, text="📋", font=ctk.CTkFont(size=32)
            ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame, text=APP_NAME,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#2F4156", "#87CEEB")
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
            text_color=("#567C8D", "#87CEEB")
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

        # ── Bottom Section ──
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 20))

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
            text="  🚪  Log Out",
            anchor="w",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2F4156",
            text_color="white",
            hover_color="#1E2D3D",
            command=self._logout
        )
        logout_btn.pack(fill="x", pady=2)

        # ── Spacer ──
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(side="top", fill="both", expand=True)

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def _logout(self):
        from tkinter import messagebox
        if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin keluar?"):
            self.app.logout()
