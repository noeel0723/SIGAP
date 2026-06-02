# views/auth/login_view.py
# Halaman Login SIGAP

import customtkinter as ctk
from controllers.auth_controller import AuthController


class LoginView(ctk.CTkFrame):
    """Halaman login dengan desain card modern di tengah layar."""

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
        card.pack(padx=40, pady=40)
        card.pack_propagate(False)
        card.configure(width=420, height=520)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=35, pady=30)

        # ── Logo & Title ──
        ctk.CTkLabel(
            inner, text="📋",
            font=ctk.CTkFont(size=42)
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            inner, text="SIGAP",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=("#2F4156", "#87CEEB")
        ).pack(pady=(5, 0))

        ctk.CTkLabel(
            inner, text="Sistem Informasi Pengaduan\ndan Aspirasi Publik",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
            justify="center"
        ).pack(pady=(2, 25))

        # ── Email ──
        ctk.CTkLabel(
            inner, text="Email",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(fill="x")

        self.email_entry = ctk.CTkEntry(
            inner, height=40, corner_radius=8,
            placeholder_text="Masukkan email Anda",
            font=ctk.CTkFont(size=13)
        )
        self.email_entry.pack(fill="x", pady=(4, 12))

        # ── Password ──
        ctk.CTkLabel(
            inner, text="Password",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(fill="x")

        pw_frame = ctk.CTkFrame(inner, fg_color="transparent")
        pw_frame.pack(fill="x", pady=(4, 8))

        self.password_entry = ctk.CTkEntry(
            pw_frame, height=40, corner_radius=8,
            placeholder_text="Masukkan password",
            show="●", font=ctk.CTkFont(size=13)
        )
        self.password_entry.pack(side="left", fill="x", expand=True)

        self.show_pw = False
        self.toggle_btn = ctk.CTkButton(
            pw_frame, text="👁", width=40, height=40,
            corner_radius=8, fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            text_color=("gray30", "gray80"),
            command=self._toggle_password
        )
        self.toggle_btn.pack(side="right", padx=(6, 0))

        # ── Error Message ──
        self.error_label = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=12),
            text_color="#E53935",
            wraplength=340
        )
        self.error_label.pack(fill="x", pady=(0, 5))

        # ── Tombol Login ──
        self.login_btn = ctk.CTkButton(
            inner, text="Masuk",
            height=42, corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#567C8D", "#567C8D"),
            hover_color=("#2F4156", "#2F4156"),
            command=self._do_login
        )
        self.login_btn.pack(fill="x", pady=(5, 15))

        # ── Link Register ──
        link_frame = ctk.CTkFrame(inner, fg_color="transparent")
        link_frame.pack()

        ctk.CTkLabel(
            link_frame, text="Belum punya akun?",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(side="left")

        ctk.CTkButton(
            link_frame, text="Daftar di sini",
            font=ctk.CTkFont(size=12, underline=True),
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("#567C8D", "#87CEEB"),
            width=10, height=25,
            command=self._show_register
        ).pack(side="left", padx=4)

        # ── Bind Enter key ──
        self.email_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._do_login())

    def _toggle_password(self):
        self.show_pw = not self.show_pw
        self.password_entry.configure(show="" if self.show_pw else "●")
        self.toggle_btn.configure(text="🔒" if self.show_pw else "👁")

    def _do_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        self.error_label.configure(text="")
        self.login_btn.configure(state="disabled", text="Memproses...")

        result = self.auth_controller.login(email, password)

        if result["success"]:
            self.app.show_dashboard(result["user"])
        else:
            self.error_label.configure(text=result["message"])
            self.login_btn.configure(state="normal", text="Masuk")

    def _show_register(self):
        from views.auth.register_view import RegisterView
        self.app._clear_container()
        RegisterView(self.app.container, app=self.app).pack(fill="both", expand=True)
