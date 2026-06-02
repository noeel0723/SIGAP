# views/warga/form_laporan.py
# Form pembuatan laporan baru — versi modal (CTkToplevel)
# NOTE: Dashboard Warga sekarang menggunakan inline form (page 2).
#       File ini tetap tersedia sebagai fallback / reusable modal.

import customtkinter as ctk
from tkinter import messagebox
from controllers.laporan_controller import LaporanController
from config.settings import KATEGORI_LAPORAN
from config.wilayah import get_semua_kecamatan, get_kelurahan_by_kecamatan


class FormLaporan(ctk.CTkToplevel):
    """Dialog modal form pembuatan laporan baru (fallback)."""

    def __init__(self, parent, app, on_success=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.laporan_ctrl = LaporanController(app.db)
        self.on_success = on_success

        self.title("Buat Laporan Baru — SIGAP")
        self.geometry("620x660")
        self.resizable(False, False)
        self.grab_set()
        self.focus()

        # ── Main container ──
        outer = ctk.CTkFrame(self, fg_color=("gray96", "gray12"))
        outer.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(outer, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # ── Card ──
        card = ctk.CTkFrame(
            scroll, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        card.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=28, pady=24)

        # ── Title ──
        ctk.CTkLabel(
            inner, text="📝  Buat Laporan Baru",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#2F4156", "#87CEEB")
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner, text="Isi semua informasi di bawah, lalu klik kirim",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 18))

        # ── Helper ──
        def add_field(parent_f, label, placeholder, is_combo=False, values=None,
                      is_text=False, height=36, combo_cmd=None):
            ctk.CTkLabel(
                parent_f, text=label,
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60")
            ).pack(anchor="w")

            if is_combo:
                w = ctk.CTkComboBox(
                    parent_f, values=values or [],
                    height=height, corner_radius=8,
                    font=ctk.CTkFont(size=13),
                    command=combo_cmd,
                    state="readonly"
                )
                w.pack(fill="x", pady=(3, 12))
                w.set(placeholder)
                return w
            elif is_text:
                w = ctk.CTkTextbox(
                    parent_f, height=height, corner_radius=8,
                    font=ctk.CTkFont(size=13),
                    border_width=1, border_color=("gray72", "gray35")
                )
                w.pack(fill="x", pady=(3, 12))
                return w
            else:
                w = ctk.CTkEntry(
                    parent_f, height=height, corner_radius=8,
                    placeholder_text=placeholder,
                    font=ctk.CTkFont(size=13)
                )
                w.pack(fill="x", pady=(3, 12))
                return w

        # ── Fields ──
        self.judul_entry = add_field(inner, "Judul Laporan *", "Ringkasan singkat masalah")

        self.kategori_combo = add_field(
            inner, "Kategori *", "Pilih Kategori",
            is_combo=True, values=KATEGORI_LAPORAN
        )

        # Kecamatan + Kelurahan side by side
        loc_row = ctk.CTkFrame(inner, fg_color="transparent")
        loc_row.pack(fill="x")
        loc_row.grid_columnconfigure(0, weight=1)
        loc_row.grid_columnconfigure(1, weight=1)

        kec_f = ctk.CTkFrame(loc_row, fg_color="transparent")
        kec_f.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.kecamatan_combo = add_field(
            kec_f, "Kecamatan *", "Pilih Kecamatan",
            is_combo=True, values=get_semua_kecamatan(),
            combo_cmd=self._on_kecamatan_changed
        )

        kel_f = ctk.CTkFrame(loc_row, fg_color="transparent")
        kel_f.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.kelurahan_combo = add_field(
            kel_f, "Kelurahan *", "Pilih kecamatan dahulu",
            is_combo=True, values=["Pilih kecamatan dahulu"]
        )

        self.lokasi_entry = add_field(
            inner, "Lokasi Spesifik *", "Contoh: Jl. Sam Ratulangi No. 12, depan SPBU"
        )

        self.deskripsi_text = add_field(
            inner, "Deskripsi Detail *", "",
            is_text=True, height=100
        )

        # ── Separator ──
        ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(
            fill="x", pady=(4, 14))

        # ── Buttons ──
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")

        self.submit_btn = ctk.CTkButton(
            btn_row, text="📤  Kirim Laporan",
            height=40, corner_radius=8, width=180,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#567C8D", "#567C8D"),
            hover_color=("#2F4156", "#2F4156"),
            command=self._submit
        )
        self.submit_btn.pack(side="left")

        ctk.CTkButton(
            btn_row, text="Batal",
            height=40, corner_radius=8, width=100,
            font=ctk.CTkFont(size=13),
            fg_color=("gray78", "gray30"),
            hover_color=("gray68", "gray40"),
            text_color=("gray20", "gray90"),
            command=self.destroy
        ).pack(side="left", padx=(10, 0))

    def _on_kecamatan_changed(self, kec: str):
        kel_list = get_kelurahan_by_kecamatan(kec)
        if kel_list:
            self.kelurahan_combo.configure(values=kel_list)
            self.kelurahan_combo.set(kel_list[0])
        else:
            self.kelurahan_combo.configure(values=["Tidak ada data"])
            self.kelurahan_combo.set("Tidak ada data")

    def _submit(self):
        kategori = self.kategori_combo.get()
        if kategori.startswith("Pilih"):
            kategori = ""

        kelurahan = self.kelurahan_combo.get()
        if kelurahan.startswith("Pilih") or kelurahan == "Tidak ada data":
            kelurahan = ""

        result = self.laporan_ctrl.buat_laporan(
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
