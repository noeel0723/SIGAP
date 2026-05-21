# views/auth/register_view.py
# Halaman Registrasi Warga

import customtkinter as ctk
from controllers.auth_controller import AuthController


class RegisterView(ctk.CTkFrame):
    """Halaman registrasi akun baru untuk Warga."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=("gray92", "gray13"), **kwargs)
        self.app = app
        self.auth_controller = AuthController(app.db)

        # ── Container tengah ──
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0)

        # ── Card Form ──
        card = ctk.CTkFrame(center, width=420, corner_radius=15,
                            fg_color=("white", "gray17"),
                            border_width=1,
                            border_color=("gray80", "gray30"))
        card.pack(padx=40, pady=30)
        card.pack_propagate(False)
        card.configure(width=420, height=620)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=35, pady=25)

        # ── Title ──
        ctk.CTkLabel(
            inner, text="📝  Daftar Akun Baru",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#1565C0", "#42A5F5")
        ).pack(pady=(5, 3))

        ctk.CTkLabel(
            inner, text="Buat akun Warga untuk mulai melapor",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(pady=(0, 20))

        # ── Helper untuk field ──
        def add_field(label_text, placeholder, show=None):
            ctk.CTkLabel(
                inner, text=label_text,
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
            ).pack(fill="x")
            entry = ctk.CTkEntry(
                inner, height=38, corner_radius=8,
                placeholder_text=placeholder,
                show=show if show else "",
                font=ctk.CTkFont(size=13)
            )
            entry.pack(fill="x", pady=(3, 10))
            return entry

        # ── Form Fields ──
        self.nama_entry = add_field("Nama Lengkap", "Masukkan nama lengkap")
        self.email_entry = add_field("Email", "contoh@email.com")
        self.telp_entry = add_field("No. Telepon (opsional)", "08xxxxxxxxxx")
        self.pw_entry = add_field("Password", "Minimal 6 karakter", show="●")
        self.pw_confirm_entry = add_field("Konfirmasi Password", "Ulangi password", show="●")

        # ── Message ──
        self.msg_label = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=12),
            text_color="#E53935",
            wraplength=340
        )
        self.msg_label.pack(fill="x", pady=(0, 5))

        # ── Tombol Daftar ──
        self.register_btn = ctk.CTkButton(
            inner, text="Daftar",
            height=42, corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#1565C0", "#1E88E5"),
            hover_color=("#0D47A1", "#1565C0"),
            command=self._do_register
        )
        self.register_btn.pack(fill="x", pady=(5, 15))

        # ── Link Login ──
        link_frame = ctk.CTkFrame(inner, fg_color="transparent")
        link_frame.pack()

        ctk.CTkLabel(
            link_frame, text="Sudah punya akun?",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(side="left")

        ctk.CTkButton(
            link_frame, text="Login di sini",
            font=ctk.CTkFont(size=12, underline=True),
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("#1565C0", "#42A5F5"),
            width=10, height=25,
            command=self._show_login
        ).pack(side="left", padx=4)

        # Bind Enter
        self.pw_confirm_entry.bind("<Return>", lambda e: self._do_register())

    def _do_register(self):
        self.msg_label.configure(text="", text_color="#E53935")
        self.register_btn.configure(state="disabled", text="Memproses...")

        result = self.auth_controller.register(
            nama=self.nama_entry.get(),
            email=self.email_entry.get(),
            password=self.pw_entry.get(),
            konfirmasi_password=self.pw_confirm_entry.get(),
            no_telepon=self.telp_entry.get()
        )

        if result["success"]:
            self.msg_label.configure(text=result["message"], text_color="#2E7D32")
            self.register_btn.configure(state="normal", text="Daftar")
            # Redirect ke login setelah 1.5 detik
            self.after(1500, self._show_login)
        else:
            self.msg_label.configure(text=result["message"])
            self.register_btn.configure(state="normal", text="Daftar")

    def _show_login(self):
        self.app.show_login()
