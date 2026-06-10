# views/components/confirmation_dialog.py
# Dialog konfirmasi dan notifikasi hasil — pengganti messagebox
# Mengatasi bug freeze saat messagebox konflik dengan CTkScrollableFrame

"""
Dialog modern untuk konfirmasi aksi admin dan notifikasi hasil.
Menggantikan tkinter.messagebox yang menyebabkan window freeze.
"""

import customtkinter as ctk


# ── Palette ──
NAVY     = "#2F4156"
TEAL     = "#567C8D"
SKY_BLUE = "#87CEEB"


class ConfirmationDialog(ctk.CTkToplevel):
    """
    Dialog konfirmasi modern sebelum aksi admin.
    
    Usage:
        def on_confirm():
            # do action
            pass
        ConfirmationDialog(
            parent, title="Konfirmasi", 
            message="Yakin ingin memproses?",
            confirm_text="Ya, Proses",
            confirm_color="#43A047",
            on_confirm=on_confirm
        )
    """

    def __init__(self, parent, title="Konfirmasi Tindakan",
                 message="Apakah Anda yakin?",
                 icon_text="⚠️",
                 confirm_text="Ya, Lanjutkan",
                 cancel_text="Batal",
                 confirm_color="#43A047",
                 on_confirm=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_confirm = on_confirm
        self._result = False
        
        # Window setup
        self.title(title)
        self.geometry("420x260")
        self.resizable(False, False)
        self.configure(fg_color=("white", "gray17"))
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 210
        y = (self.winfo_screenheight() // 2) - 130
        self.geometry(f"+{x}+{y}")
        
        # Modal behavior
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()
        
        # ── Content ──
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=25)
        
        # Icon
        ctk.CTkLabel(
            content, text=icon_text,
            font=ctk.CTkFont(size=42)
        ).pack(pady=(0, 8))
        
        # Title
        ctk.CTkLabel(
            content, text=title,
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=(NAVY, SKY_BLUE)
        ).pack(pady=(0, 6))
        
        # Message
        ctk.CTkLabel(
            content, text=message,
            font=ctk.CTkFont(size=13),
            text_color=("gray45", "gray60"),
            wraplength=360, justify="center"
        ).pack(pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        # Cancel button (left)
        ctk.CTkButton(
            btn_frame, text=cancel_text,
            height=38, corner_radius=8, width=160,
            font=ctk.CTkFont(size=13),
            fg_color=("gray88", "gray28"),
            text_color=("gray30", "gray80"),
            hover_color=("gray78", "gray35"),
            command=self._cancel
        ).pack(side="left", expand=True, padx=(0, 6))
        
        # Confirm button (right)
        ctk.CTkButton(
            btn_frame, text=confirm_text,
            height=38, corner_radius=8, width=160,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=confirm_color,
            hover_color=self._darken(confirm_color),
            text_color="white",
            command=self._confirm
        ).pack(side="right", expand=True, padx=(6, 0))
        
        # Handle X button
        self.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def _confirm(self):
        self._result = True
        self._close()
        if self.on_confirm:
            # Schedule callback after dialog is fully closed
            self.after_idle(self.on_confirm)
    
    def _cancel(self):
        self._result = False
        self._close()
    
    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
    
    @staticmethod
    def _darken(hex_color, factor=0.8):
        """Darken a hex color."""
        hex_color = hex_color.lstrip('#')
        r = int(int(hex_color[0:2], 16) * factor)
        g = int(int(hex_color[2:4], 16) * factor)
        b = int(int(hex_color[4:6], 16) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"


class ResultDialog(ctk.CTkToplevel):
    """
    Dialog notifikasi hasil aksi (sukses/gagal).
    Menggantikan messagebox.showinfo dan messagebox.showerror.
    
    Usage:
        ResultDialog(parent, success=True, message="Berhasil!", on_close=refresh_fn)
    """

    def __init__(self, parent, success=True, title=None,
                 message="Operasi berhasil.",
                 on_close=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_close_callback = on_close
        
        if title is None:
            title = "Berhasil" if success else "Gagal"
        
        icon = "✅" if success else "❌"
        accent = "#43A047" if success else "#E53935"
        
        # Window setup
        self.title(title)
        self.geometry("400x230")
        self.resizable(False, False)
        self.configure(fg_color=("white", "gray17"))
        
        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 200
        y = (self.winfo_screenheight() // 2) - 115
        self.geometry(f"+{x}+{y}")
        
        # Modal
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()
        
        # ── Content ──
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=25)
        
        # Icon
        ctk.CTkLabel(
            content, text=icon,
            font=ctk.CTkFont(size=42)
        ).pack(pady=(0, 8))
        
        # Title
        ctk.CTkLabel(
            content, text=title,
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=accent
        ).pack(pady=(0, 6))
        
        # Message
        ctk.CTkLabel(
            content, text=message,
            font=ctk.CTkFont(size=13),
            text_color=("gray45", "gray60"),
            wraplength=340, justify="center"
        ).pack(pady=(0, 20))
        
        # OK button
        ctk.CTkButton(
            content, text="OK",
            height=38, corner_radius=8, width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=accent,
            hover_color=ConfirmationDialog._darken(accent),
            text_color="white",
            command=self._close
        ).pack()
        
        # Handle X
        self.protocol("WM_DELETE_WINDOW", self._close)
    
    def _close(self):
        callback = self.on_close_callback
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if callback:
            try:
                callback()
            except Exception:
                pass
