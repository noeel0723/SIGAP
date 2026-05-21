# views/warga/dashboard_warga.py
# Dashboard utama untuk Warga

import customtkinter as ctk
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.data_table import DataTable
from views.components.status_badge import StatusBadge
from views.warga.form_laporan import FormLaporan
from utils.helpers import format_tanggal


class DashboardWarga(ctk.CTkFrame):
    """Dashboard utama Warga: ringkasan, tabel laporan, detail & timeline."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=("gray95", "gray12"), **kwargs)
        self.app = app
        self.laporan_ctrl = LaporanController(app.db)

        # ── Layout: Sidebar + Content ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = Sidebar(self, app=app, menu_items=[
            {"icon": "🏠", "label": "Dashboard", "command": self._refresh_data},
            {"icon": "📝", "label": "Buat Laporan", "command": self._show_form_laporan},
            {"icon": "🔄", "label": "Refresh Data", "command": self._refresh_data},
        ])
        sidebar.grid(row=0, column=0, sticky="nsw")

        # ── Content Area ──
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            header_frame, text=f"Selamat Datang, {app.current_user.get('nama_lengkap', '')}!",
            font=ctk.CTkFont(size=22, weight="bold"), anchor="w"
        ).pack(side="left")

        ctk.CTkButton(
            header_frame, text="➕  Buat Laporan",
            height=36, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#1565C0", "#1E88E5"),
            hover_color=("#0D47A1", "#1565C0"),
            command=self._show_form_laporan
        ).pack(side="right")

        # ── Summary Cards ──
        cards_frame = ctk.CTkFrame(content, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)

        self.card_data = [
            {"label": "Total Laporan", "color": "#1E88E5", "key": "total"},
            {"label": "Menunggu", "color": "#FFA726", "key": "menunggu"},
            {"label": "Diproses", "color": "#AB47BC", "key": "diproses"},
            {"label": "Selesai", "color": "#66BB6A", "key": "selesai"},
        ]
        self.card_values = {}

        for i, card_info in enumerate(self.card_data):
            card = ctk.CTkFrame(cards_frame, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray85", "gray28"))
            card.grid(row=0, column=i, sticky="ew", padx=5)

            val_lbl = ctk.CTkLabel(
                card, text="0",
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=card_info["color"]
            )
            val_lbl.pack(padx=18, pady=(15, 2))
            self.card_values[card_info["key"]] = val_lbl

            ctk.CTkLabel(
                card, text=card_info["label"],
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60")
            ).pack(padx=18, pady=(0, 12))

        # ── Tabel Laporan ──
        table_label = ctk.CTkLabel(
            content, text="📋  Riwayat Laporan Anda",
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        table_label.grid(row=2, column=0, sticky="w", pady=(5, 8))

        self.table = DataTable(
            content,
            columns=[
                {"key": "id", "label": "#", "width": 40, "max_len": 6},
                {"key": "judul", "label": "Judul Laporan", "width": 200, "max_len": 35},
                {"key": "kategori", "label": "Kategori", "width": 140, "max_len": 20},
                {"key": "kelurahan", "label": "Kelurahan", "width": 130, "max_len": 20},
                {"key": "status", "label": "Status", "width": 140, "max_len": 25},
                {"key": "created_at", "label": "Tanggal", "width": 140},
            ],
            on_row_click=self._show_detail
        )
        self.table.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        content.grid_rowconfigure(3, weight=1)

        # ── Detail Panel ──
        self.detail_frame = ctk.CTkFrame(content, corner_radius=12,
                                         fg_color=("white", "gray17"),
                                         border_width=1,
                                         border_color=("gray85", "gray28"))
        self.detail_frame.grid(row=4, column=0, sticky="ew", pady=(5, 0))
        self.detail_frame.grid_remove()  # Hidden by default

        # Load data
        self._refresh_data()

    def _refresh_data(self):
        user_id = self.app.current_user["id"]
        laporan_list = self.laporan_ctrl.get_laporan_warga(user_id)

        # Update cards
        total = len(laporan_list)
        menunggu = sum(1 for l in laporan_list if l["status"] == "Menunggu")
        diproses = sum(1 for l in laporan_list if "Diproses" in l.get("status", ""))
        selesai = sum(1 for l in laporan_list if l["status"] == "Selesai")

        self.card_values["total"].configure(text=str(total))
        self.card_values["menunggu"].configure(text=str(menunggu))
        self.card_values["diproses"].configure(text=str(diproses))
        self.card_values["selesai"].configure(text=str(selesai))

        # Update table
        self.table.set_data(laporan_list)
        self.detail_frame.grid_remove()

    def _show_form_laporan(self):
        FormLaporan(self, app=self.app, on_success=self._refresh_data)

    def _show_detail(self, laporan: dict):
        """Tampilkan detail laporan dan timeline tracking."""
        # Clear detail
        for w in self.detail_frame.winfo_children():
            w.destroy()
        self.detail_frame.grid()

        inner = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        # Header detail
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header, text=f"Detail Laporan #{laporan['id']}",
            font=ctk.CTkFont(size=15, weight="bold"), anchor="w"
        ).pack(side="left")

        StatusBadge(header, status=laporan["status"]).pack(side="right")

        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(fill="x", pady=(8, 0))

        details = [
            ("Judul", laporan.get("judul", "")),
            ("Kategori", laporan.get("kategori", "")),
            ("Lokasi", f"{laporan.get('lokasi', '')} — Kel. {laporan.get('kelurahan', '')}, Kec. {laporan.get('kecamatan', '')}"),
            ("Tanggal", format_tanggal(laporan.get("created_at"))),
        ]

        for label, value in details:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{label}:", font=ctk.CTkFont(size=12, weight="bold"),
                         width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12),
                         anchor="w", wraplength=500).pack(side="left", fill="x")

        # ── Timeline Riwayat ──
        ctk.CTkLabel(
            inner, text="📌  Timeline Status",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).pack(fill="x", pady=(12, 5))

        riwayat = self.laporan_ctrl.get_riwayat_laporan(laporan["id"])
        timeline_frame = ctk.CTkFrame(inner, fg_color="transparent")
        timeline_frame.pack(fill="x")

        for i, rw in enumerate(riwayat):
            is_last = (i == len(riwayat) - 1)

            item = ctk.CTkFrame(timeline_frame, fg_color="transparent")
            item.pack(fill="x")

            # Dot + Line
            dot_frame = ctk.CTkFrame(item, fg_color="transparent", width=30)
            dot_frame.pack(side="left", anchor="n")
            dot_frame.pack_propagate(False)

            dot_color = "#1E88E5" if is_last else ("gray60", "gray50")
            dot = ctk.CTkLabel(dot_frame, text="●", text_color=dot_color,
                               font=ctk.CTkFont(size=16))
            dot.pack(pady=(3, 0))

            if not is_last:
                line = ctk.CTkFrame(dot_frame, width=2, height=30,
                                    fg_color=("gray70", "gray40"))
                line.pack()

            # Content
            content_f = ctk.CTkFrame(item, fg_color="transparent")
            content_f.pack(side="left", fill="x", expand=True, padx=(5, 0))

            status_text = rw.get("status_baru", "")
            time_text = format_tanggal(rw.get("created_at"))
            admin_name = rw.get("nama_admin", "Sistem")
            catatan = rw.get("catatan_admin", "")

            ctk.CTkLabel(
                content_f, text=f"{status_text}  •  {time_text}",
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
            ).pack(fill="x")

            if catatan:
                ctk.CTkLabel(
                    content_f,
                    text=f"oleh {admin_name}: {catatan}",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray45", "gray65"),
                    anchor="w", wraplength=500
                ).pack(fill="x")
