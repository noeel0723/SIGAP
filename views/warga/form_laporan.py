# views/warga/form_laporan.py
# Form pembuatan laporan baru

import customtkinter as ctk
from tkinter import messagebox
from controllers.laporan_controller import LaporanController
from config.settings import KATEGORI_LAPORAN
from config.wilayah import get_semua_kecamatan, get_kelurahan_by_kecamatan


class FormLaporan(ctk.CTkToplevel):
    """Dialog modal form pembuatan laporan baru."""

    def __init__(self, parent, app, on_success=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.laporan_controller = LaporanController(app.db)
        self.on_success = on_success

        self.title("Buat Laporan Baru")
        self.geometry("580x700")
        self.resizable(False, False)
        self.grab_set()
        self.focus()

        # ── Scrollable content ──
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        # Title
        ctk.CTkLabel(
            scroll, text="📝  Buat Laporan Baru",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1565C0", "#42A5F5")
        ).pack(anchor="w", pady=(0, 15))

        # ── Helper field builder ──
        def add_label(text):
            ctk.CTkLabel(
                scroll, text=text,
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
            ).pack(fill="x", pady=(8, 2))

        # ── Judul ──
        add_label("Judul Laporan *")
        self.judul_entry = ctk.CTkEntry(
            scroll, height=38, corner_radius=8,
            placeholder_text="Ringkasan singkat masalah",
            font=ctk.CTkFont(size=13)
        )
        self.judul_entry.pack(fill="x")

        # ── Kategori ──
        add_label("Kategori *")
        self.kategori_var = ctk.StringVar(value="")
        self.kategori_combo = ctk.CTkComboBox(
            scroll, height=38, corner_radius=8,
            values=KATEGORI_LAPORAN,
            variable=self.kategori_var,
            font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.kategori_combo.pack(fill="x")
        self.kategori_combo.set("Pilih Kategori...")

        # ── Deskripsi ──
        add_label("Deskripsi Detail *")
        self.deskripsi_text = ctk.CTkTextbox(
            scroll, height=120, corner_radius=8,
            font=ctk.CTkFont(size=13),
            border_width=1,
            border_color=("gray70", "gray35")
        )
        self.deskripsi_text.pack(fill="x")

        # ── Lokasi ──
        add_label("Lokasi Spesifik *")
        self.lokasi_entry = ctk.CTkEntry(
            scroll, height=38, corner_radius=8,
            placeholder_text="Contoh: Jl. Sam Ratulangi No. 12, depan SPBU",
            font=ctk.CTkFont(size=13)
        )
        self.lokasi_entry.pack(fill="x")

        # ── Kecamatan ──
        add_label("Kecamatan *")
        self.kecamatan_var = ctk.StringVar(value="")
        self.kecamatan_combo = ctk.CTkComboBox(
            scroll, height=38, corner_radius=8,
            values=get_semua_kecamatan(),
            variable=self.kecamatan_var,
            font=ctk.CTkFont(size=13),
            command=self._on_kecamatan_changed,
            state="readonly"
        )
        self.kecamatan_combo.pack(fill="x")
        self.kecamatan_combo.set("Pilih Kecamatan...")

        # ── Kelurahan (cascading) ──
        add_label("Kelurahan *")
        self.kelurahan_var = ctk.StringVar(value="")
        self.kelurahan_combo = ctk.CTkComboBox(
            scroll, height=38, corner_radius=8,
            values=["Pilih kecamatan terlebih dahulu"],
            variable=self.kelurahan_var,
            font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.kelurahan_combo.pack(fill="x")
        self.kelurahan_combo.set("Pilih kecamatan terlebih dahulu")

        # ── Separator ──
        ctk.CTkFrame(scroll, height=1, fg_color=("gray80", "gray30")).pack(
            fill="x", pady=20)

        # ── Tombol ──
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame, text="Batal",
            height=40, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            text_color=("gray20", "gray90"),
            width=120,
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        self.submit_btn = ctk.CTkButton(
            btn_frame, text="📤  Kirim Laporan",
            height=40, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#1565C0", "#1E88E5"),
            hover_color=("#0D47A1", "#1565C0"),
            width=180,
            command=self._submit
        )
        self.submit_btn.pack(side="right")

    def _on_kecamatan_changed(self, kecamatan: str):
        kelurahan_list = get_kelurahan_by_kecamatan(kecamatan)
        if kelurahan_list:
            self.kelurahan_combo.configure(values=kelurahan_list)
            self.kelurahan_combo.set(kelurahan_list[0])
        else:
            self.kelurahan_combo.configure(values=["Tidak ada data"])
            self.kelurahan_combo.set("Tidak ada data")

    def _submit(self):
        kategori = self.kategori_var.get()
        if kategori.startswith("Pilih"):
            kategori = ""

        kelurahan = self.kelurahan_var.get()
        if kelurahan.startswith("Pilih") or kelurahan == "Tidak ada data":
            kelurahan = ""

        result = self.laporan_controller.buat_laporan(
            user_id=self.app.current_user["id"],
            judul=self.judul_entry.get(),
            kategori=kategori,
            deskripsi=self.deskripsi_text.get("1.0", "end-1c"),
            lokasi=self.lokasi_entry.get(),
            kelurahan=kelurahan
        )

        if result["success"]:
            messagebox.showinfo("Berhasil", result["message"], parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            messagebox.showerror("Gagal", result["message"], parent=self)
