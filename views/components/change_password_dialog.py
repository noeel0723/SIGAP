# views/components/change_password_dialog.py
# Dialog ganti password — tersedia untuk semua role

"""
Dialog modal modern untuk mengganti password user.
Dipanggil dari sidebar untuk semua role.
"""

import customtkinter as ctk
from views.components.confirmation_dialog import ResultDialog

# ── Palette ──
NAVY     = "#2F4156"
TEAL     = "#567C8D"
SKY_BLUE = "#87CEEB"


class ChangePasswordDialog(ctk.CTkToplevel):
    """
    Dialog ganti password modern.
    
    Usage:
        ChangePasswordDialog(parent, app=app)
    """

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.app = app
        
        # Window setup
        self.title("Ganti Password")
        self.geometry("460x530")
        self.resizable(False, False)
        self.configure(fg_color=("white", "gray17"))
        
        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 230
        y = (self.winfo_screenheight() // 2) - 265
        self.geometry(f"+{x}+{y}")
        
        # Modal
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()
        
        # ── Content ──
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=25)
        
        # Header
        ctk.CTkLabel(
            content, text="🔑",
            font=ctk.CTkFont(size=36)
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            content, text="Ganti Password",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(NAVY, SKY_BLUE)
        ).pack(pady=(0, 3))
        
        ctk.CTkLabel(
            content, text="Masukkan password lama dan password baru Anda.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack(pady=(0, 18))
        
        # Old password
        ctk.CTkLabel(
            content, text="Password Lama",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(fill="x")
        self.old_pw = ctk.CTkEntry(
            content, height=38, corner_radius=8,
            placeholder_text="Masukkan password lama",
            show="●", font=ctk.CTkFont(size=13)
        )
        self.old_pw.pack(fill="x", pady=(3, 10))
        
        # New password
        ctk.CTkLabel(
            content, text="Password Baru",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(fill="x")
        self.new_pw = ctk.CTkEntry(
            content, height=38, corner_radius=8,
            placeholder_text="Minimal 6 karakter",
            show="●", font=ctk.CTkFont(size=13)
        )
        self.new_pw.pack(fill="x", pady=(3, 10))
        
        # Confirm new password
        ctk.CTkLabel(
            content, text="Konfirmasi Password Baru",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(fill="x")
        self.confirm_pw = ctk.CTkEntry(
            content, height=38, corner_radius=8,
            placeholder_text="Ulangi password baru",
            show="●", font=ctk.CTkFont(size=13)
        )
        self.confirm_pw.pack(fill="x", pady=(3, 10))
        
        # Error label
        self.error_label = ctk.CTkLabel(
            content, text="",
            font=ctk.CTkFont(size=11),
            text_color="#E53935",
            wraplength=380
        )
        self.error_label.pack(fill="x", pady=(0, 8))
        
        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame, text="Batal",
            height=38, corner_radius=8, width=150,
            font=ctk.CTkFont(size=13),
            fg_color=("gray88", "gray28"),
            text_color=("gray30", "gray80"),
            hover_color=("gray78", "gray35"),
            command=self._close
        ).pack(side="left", expand=True, padx=(0, 6))
        
        ctk.CTkButton(
            btn_frame, text="Simpan Password",
            height=38, corner_radius=8, width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=(TEAL, TEAL),
            hover_color=(NAVY, NAVY),
            text_color="white",
            command=self._submit
        ).pack(side="right", expand=True, padx=(6, 0))
        
        # Bind enter key
        self.confirm_pw.bind("<Return>", lambda e: self._submit())
        
        # Handle X
        self.protocol("WM_DELETE_WINDOW", self._close)
    
    def _submit(self):
        old = self.old_pw.get()
        new = self.new_pw.get()
        confirm = self.confirm_pw.get()
        
        # Validate
        if not old:
            self.error_label.configure(text="Password lama wajib diisi.")
            return
        if not new:
            self.error_label.configure(text="Password baru wajib diisi.")
            return
        if len(new) < 6:
            self.error_label.configure(text="Password baru minimal 6 karakter.")
            return
        if new != confirm:
            self.error_label.configure(text="Konfirmasi password tidak cocok.")
            return
        if old == new:
            self.error_label.configure(text="Password baru harus berbeda dari password lama.")
            return
        
        self.error_label.configure(text="")
        
        # Call controller
        from controllers.auth_controller import AuthController
        auth_ctrl = AuthController(self.app.db)
        result = auth_ctrl.change_password(
            user_id=self.app.current_user["id"],
            old_password=old,
            new_password=new,
            confirm_password=confirm
        )
        
        if result["success"]:
            self._close()
            ResultDialog(
                self.master, success=True,
                message=result["message"]
            )
        else:
            self.error_label.configure(text=result["message"])
    
    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
