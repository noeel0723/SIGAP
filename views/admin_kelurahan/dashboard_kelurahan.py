# views/admin_kelurahan/dashboard_kelurahan.py
# Dashboard untuk Admin Kelurahan

import customtkinter as ctk
from tkinter import messagebox
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.data_table import DataTable
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal


class DashboardKelurahan(ctk.CTkFrame):
    """Dashboard Admin Kelurahan: proses laporan, eskalasi ke kecamatan."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=("gray95", "gray12"), **kwargs)
        self.app = app
        self.laporan_ctrl = LaporanController(app.db)
        self.kelurahan = app.current_user.get("kelurahan", "")
        self.selected_laporan = None

        # ── Layout ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = Sidebar(self, app=app, menu_items=[
            {"icon": "🏠", "label": "Dashboard", "command": lambda: self._refresh_data()},
            {"icon": "📋", "label": "Semua Laporan", "command": lambda: self._filter("Semua")},
            {"icon": "⏳", "label": "Menunggu", "command": lambda: self._filter("Menunggu")},
            {"icon": "🔄", "label": "Diproses", "command": lambda: self._filter("Diproses Kelurahan")},
            {"icon": "✅", "label": "Selesai", "command": lambda: self._filter("Selesai")},
        ])
        sidebar.grid(row=0, column=0, sticky="nsw")

        # ── Content ──
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(
            content, text=f"📋  Dashboard Kelurahan {self.kelurahan}",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))

        # ── Summary Cards ──
        cards_frame = ctk.CTkFrame(content, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        for i in range(5):
            cards_frame.grid_columnconfigure(i, weight=1)

        self.card_configs = [
            {"label": "Total", "key": "total"},
            {"label": "Menunggu", "key": "menunggu"},
            {"label": "Diproses", "key": "diproses"},
            {"label": "Selesai", "key": "selesai"},
            {"label": "Ditolak", "key": "ditolak"},
        ]
        self.card_values = {}
        for i, cc in enumerate(self.card_configs):
            card = ctk.CTkFrame(cards_frame, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray85", "gray28"))
            card.grid(row=0, column=i, sticky="ew", padx=4)
            val = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=24, weight="bold"),
                               text_color=("black", "white"))
            val.pack(padx=14, pady=(12, 2))
            self.card_values[cc["key"]] = val
            ctk.CTkLabel(card, text=cc["label"], font=ctk.CTkFont(size=10),
                         text_color=("gray50", "gray60")).pack(padx=14, pady=(0, 10))

        # ── Filter Tabs ──
        self.filter_var = ctk.StringVar(value="Semua")
        filter_frame = ctk.CTkSegmentedButton(
            content, values=["Semua", "Menunggu", "Diproses Kelurahan", "Selesai", "Ditolak"],
            variable=self.filter_var,
            command=self._filter,
            font=ctk.CTkFont(size=12),
            corner_radius=8
        )
        filter_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # ── Tabel ──
        self.table = DataTable(
            content,
            columns=[
                {"key": "id", "label": "#", "width": 40, "max_len": 6},
                {"key": "judul", "label": "Judul", "width": 180, "max_len": 30},
                {"key": "nama_pelapor", "label": "Pelapor", "width": 130, "max_len": 20},
                {"key": "kategori", "label": "Kategori", "width": 130, "max_len": 18},
                {"key": "status", "label": "Status", "width": 140, "max_len": 22},
                {"key": "created_at", "label": "Tanggal", "width": 130},
            ],
            on_row_click=self._on_select
        )
        self.table.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        content.grid_rowconfigure(3, weight=1)

        # ── Panel Aksi ──
        self.action_frame = ctk.CTkFrame(content, corner_radius=12,
                                         fg_color=("white", "gray17"),
                                         border_width=1, border_color=("gray85", "gray28"))
        self.action_frame.grid(row=4, column=0, sticky="ew")
        self.action_frame.grid_remove()

        self._build_action_panel()
        self._refresh_data()

    def _build_action_panel(self):
        inner = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        self.detail_title = ctk.CTkLabel(
            inner, text="Detail Laporan",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.detail_title.pack(fill="x")

        self.detail_info = ctk.CTkLabel(
            inner, text="", font=ctk.CTkFont(size=12),
            anchor="w", justify="left", wraplength=600)
        self.detail_info.pack(fill="x", pady=(4, 10))

        # Catatan Admin
        ctk.CTkLabel(inner, text="Catatan Admin *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x")
        self.catatan_text = ctk.CTkTextbox(
            inner, height=60, corner_radius=8,
            font=ctk.CTkFont(size=12),
            border_width=1, border_color=("gray70", "gray35"))
        self.catatan_text.pack(fill="x", pady=(3, 10))

        # Tombol Aksi
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")

        actions = [
            ("✅ Proses", "Diproses Kelurahan", "#1E88E5"),
            ("🏁 Selesai", "Selesai", "#43A047"),
            ("❌ Tolak", "Ditolak", "#E53935"),
            ("⬆️ Eskalasi Kecamatan", "Diproses Kecamatan", "#7B1FA2"),
        ]
        for text, status, color in actions:
            ctk.CTkButton(
                btn_frame, text=text, height=36, corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=color, hover_color=color,
                command=lambda s=status: self._proses(s)
            ).pack(side="left", padx=(0, 6))

    def _on_select(self, laporan: dict):
        self.selected_laporan = laporan
        self.action_frame.grid()
        self.detail_title.configure(text=f"Detail Laporan #{laporan['id']}: {laporan.get('judul', '')}")
        info = (f"Pelapor: {laporan.get('nama_pelapor', '')}  |  "
                f"Kategori: {laporan.get('kategori', '')}  |  "
                f"Lokasi: {laporan.get('lokasi', '')}  |  "
                f"Status: {laporan.get('status', '')}")
        self.detail_info.configure(text=info)
        self.catatan_text.delete("1.0", "end")

    def _proses(self, status_baru: str):
        if not self.selected_laporan:
            return
        catatan = self.catatan_text.get("1.0", "end-1c")
        result = self.laporan_ctrl.proses_laporan(
            laporan_id=self.selected_laporan["id"],
            admin_id=self.app.current_user["id"],
            status_baru=status_baru,
            catatan=catatan
        )
        if result["success"]:
            messagebox.showinfo("Berhasil", result["message"])
            self._refresh_data()
        else:
            messagebox.showerror("Gagal", result["message"])

    def _filter(self, status: str):
        if status == "Semua":
            self._refresh_data()
        else:
            data = self.laporan_ctrl.get_laporan_kelurahan(self.kelurahan, status)
            self.table.set_data(data)
            self.action_frame.grid_remove()
            self.selected_laporan = None

    def _refresh_data(self):
        data = self.laporan_ctrl.get_laporan_kelurahan(self.kelurahan)
        self.table.set_data(data)

        total = len(data)
        self.card_values["total"].configure(text=str(total))
        self.card_values["menunggu"].configure(
            text=str(sum(1 for d in data if d["status"] == "Menunggu")))
        self.card_values["diproses"].configure(
            text=str(sum(1 for d in data if "Diproses" in d.get("status", ""))))
        self.card_values["selesai"].configure(
            text=str(sum(1 for d in data if d["status"] == "Selesai")))
        self.card_values["ditolak"].configure(
            text=str(sum(1 for d in data if d["status"] == "Ditolak")))

        self.action_frame.grid_remove()
        self.selected_laporan = None
