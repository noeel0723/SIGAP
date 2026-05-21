# views/admin_kota/dashboard_kota.py
# Master Dashboard untuk Admin Kota

import customtkinter as ctk
from tkinter import messagebox
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.data_table import DataTable
from utils.helpers import format_tanggal
from utils.chart_helper import (
    configure_chart_style, create_pie_chart,
    create_bar_chart, create_line_chart
)
from config.wilayah import get_semua_kecamatan
from config.settings import STATUS_LAPORAN


class DashboardKota(ctk.CTkFrame):
    """Master Dashboard Admin Kota: analitik + manajemen laporan."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=("gray95", "gray12"), **kwargs)
        self.app = app
        self.laporan_ctrl = LaporanController(app.db)
        self.selected_laporan = None
        self.current_tab = "analitik"

        # ── Layout ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = Sidebar(self, app=app, menu_items=[
            {"icon": "📊", "label": "Analitik", "command": lambda: self._switch_tab("analitik")},
            {"icon": "📋", "label": "Manajemen Laporan", "command": lambda: self._switch_tab("manajemen")},
            {"icon": "🔄", "label": "Refresh Data", "command": self._refresh_all},
        ])
        sidebar.grid(row=0, column=0, sticky="nsw")

        # ── Content Container ──
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # Header
        ctk.CTkLabel(
            self.content, text="📊  Master Dashboard — Kota Manado",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))

        # Tab frames
        self.analitik_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.manajemen_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.manajemen_frame.grid_columnconfigure(0, weight=1)

        self._build_analitik_tab()
        self._build_manajemen_tab()
        self._switch_tab("analitik")
        self._refresh_all()

    # ══════════════════════════════════════
    # TAB ANALITIK
    # ══════════════════════════════════════

    def _build_analitik_tab(self):
        f = self.analitik_frame
        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=1)

        # Summary cards row
        cards_frame = ctk.CTkFrame(f, fg_color="transparent")
        cards_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)

        self.kota_cards = {}
        card_defs = [
            {"label": "Total Laporan", "color": "#1E88E5", "key": "total"},
            {"label": "Menunggu", "color": "#FFA726", "key": "menunggu"},
            {"label": "Dalam Proses", "color": "#AB47BC", "key": "proses"},
            {"label": "Selesai", "color": "#66BB6A", "key": "selesai"},
        ]
        for i, cd in enumerate(card_defs):
            card = ctk.CTkFrame(cards_frame, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray85", "gray28"))
            card.grid(row=0, column=i, sticky="ew", padx=4)
            val = ctk.CTkLabel(card, text="0",
                               font=ctk.CTkFont(size=28, weight="bold"),
                               text_color=cd["color"])
            val.pack(padx=18, pady=(15, 2))
            self.kota_cards[cd["key"]] = val
            ctk.CTkLabel(card, text=cd["label"],
                         font=ctk.CTkFont(size=11),
                         text_color=("gray50", "gray60")).pack(padx=18, pady=(0, 12))

        # Chart containers (2x2 grid)
        self.chart_frames = {}
        positions = [
            ("status", 1, 0, "Sebaran Status"),
            ("kategori", 1, 1, "Laporan per Kategori"),
            ("kecamatan", 2, 0, "Laporan per Kecamatan"),
            ("bulanan", 2, 1, "Tren Bulanan"),
        ]
        for key, row, col, title in positions:
            container = ctk.CTkFrame(f, corner_radius=12,
                                     fg_color=("white", "gray17"),
                                     border_width=1,
                                     border_color=("gray85", "gray28"))
            container.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            f.grid_rowconfigure(row, weight=1)

            ctk.CTkLabel(container, text=title,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         anchor="w").pack(padx=15, pady=(10, 0), anchor="w")

            chart_area = ctk.CTkFrame(container, fg_color="transparent")
            chart_area.pack(fill="both", expand=True, padx=10, pady=(5, 10))
            self.chart_frames[key] = chart_area

    def _render_charts(self):
        """Render semua grafik matplotlib."""
        dark = ctk.get_appearance_mode() == "Dark"
        configure_chart_style(dark)
        stats = self.laporan_ctrl.get_statistik()

        # Clear existing charts
        for key, frame in self.chart_frames.items():
            for w in frame.winfo_children():
                w.destroy()

        # 1. Pie Chart - Status
        per_status = stats.get("per_status", [])
        if per_status:
            labels = [s["status"] for s in per_status]
            values = [s["jumlah"] for s in per_status]
            colors = ["#FFA726", "#42A5F5", "#AB47BC", "#FF7043", "#66BB6A", "#EF5350"]
            canvas = create_pie_chart(self.chart_frames["status"],
                                      labels, values, "", colors)
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.chart_frames["status"], text="Belum ada data",
                         text_color=("gray50", "gray60")).pack(expand=True)

        # 2. Bar Chart - Kategori
        per_kategori = stats.get("per_kategori", [])
        if per_kategori:
            labels = [k["kategori"][:12] for k in per_kategori]
            values = [k["jumlah"] for k in per_kategori]
            canvas = create_bar_chart(self.chart_frames["kategori"],
                                      labels, values, "", "Kategori", "Jumlah", "#42A5F5")
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.chart_frames["kategori"], text="Belum ada data",
                         text_color=("gray50", "gray60")).pack(expand=True)

        # 3. Bar Chart - Kecamatan
        per_kecamatan = stats.get("per_kecamatan", [])
        if per_kecamatan:
            labels = [k["kecamatan"] for k in per_kecamatan]
            values = [k["jumlah"] for k in per_kecamatan]
            canvas = create_bar_chart(self.chart_frames["kecamatan"],
                                      labels, values, "", "Kecamatan", "Jumlah", "#66BB6A")
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.chart_frames["kecamatan"], text="Belum ada data",
                         text_color=("gray50", "gray60")).pack(expand=True)

        # 4. Line Chart - Bulanan
        bulanan = stats.get("bulanan", [])
        if bulanan:
            bulan_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
            x = [bulan_names[b["bulan"] - 1] for b in bulanan]
            y = [b["jumlah"] for b in bulanan]
            canvas = create_line_chart(self.chart_frames["bulanan"],
                                       x, y, "", "Bulan", "Jumlah", "#AB47BC")
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.chart_frames["bulanan"], text="Belum ada data",
                         text_color=("gray50", "gray60")).pack(expand=True)

    # ══════════════════════════════════════
    # TAB MANAJEMEN
    # ══════════════════════════════════════

    def _build_manajemen_tab(self):
        f = self.manajemen_frame

        # Filter bar
        filter_bar = ctk.CTkFrame(f, fg_color="transparent")
        filter_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(filter_bar, text="Kecamatan:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        kecamatan_list = ["Semua"] + get_semua_kecamatan()
        self.mgmt_kec_var = ctk.StringVar(value="Semua")
        ctk.CTkComboBox(
            filter_bar, values=kecamatan_list,
            variable=self.mgmt_kec_var,
            width=170, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_mgmt_filter(),
            state="readonly"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(filter_bar, text="Status:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        self.mgmt_status_var = ctk.StringVar(value="Semua")
        ctk.CTkComboBox(
            filter_bar, values=["Semua"] + STATUS_LAPORAN,
            variable=self.mgmt_status_var,
            width=170, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_mgmt_filter(),
            state="readonly"
        ).pack(side="left")

        # Tabel
        self.mgmt_table = DataTable(
            f,
            columns=[
                {"key": "id", "label": "#", "width": 40, "max_len": 6},
                {"key": "judul", "label": "Judul", "width": 160, "max_len": 26},
                {"key": "nama_pelapor", "label": "Pelapor", "width": 110, "max_len": 16},
                {"key": "kelurahan", "label": "Kelurahan", "width": 110, "max_len": 16},
                {"key": "kecamatan", "label": "Kecamatan", "width": 100, "max_len": 14},
                {"key": "kategori", "label": "Kategori", "width": 110, "max_len": 14},
                {"key": "status", "label": "Status", "width": 130, "max_len": 20},
                {"key": "created_at", "label": "Tanggal", "width": 110},
            ],
            on_row_click=self._on_mgmt_select
        )
        self.mgmt_table.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        f.grid_rowconfigure(1, weight=1)

        # Panel Aksi
        self.mgmt_action_frame = ctk.CTkFrame(f, corner_radius=12,
                                               fg_color=("white", "gray17"),
                                               border_width=1,
                                               border_color=("gray85", "gray28"))
        self.mgmt_action_frame.grid(row=2, column=0, sticky="ew")
        self.mgmt_action_frame.grid_remove()
        self._build_mgmt_action_panel()

    def _build_mgmt_action_panel(self):
        inner = ctk.CTkFrame(self.mgmt_action_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        self.mgmt_detail_title = ctk.CTkLabel(
            inner, text="Detail Laporan",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.mgmt_detail_title.pack(fill="x")

        self.mgmt_detail_info = ctk.CTkLabel(
            inner, text="", font=ctk.CTkFont(size=12),
            anchor="w", justify="left", wraplength=600)
        self.mgmt_detail_info.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(inner, text="Catatan Admin *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x")
        self.mgmt_catatan = ctk.CTkTextbox(
            inner, height=60, corner_radius=8,
            font=ctk.CTkFont(size=12),
            border_width=1, border_color=("gray70", "gray35"))
        self.mgmt_catatan.pack(fill="x", pady=(3, 10))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")

        actions = [
            ("✅ Proses Kota", "Diproses Kota", "#1E88E5"),
            ("🏁 Selesai", "Selesai", "#43A047"),
            ("❌ Tolak", "Ditolak", "#E53935"),
        ]
        for text, status, color in actions:
            ctk.CTkButton(
                btn_frame, text=text, height=36, corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=color, hover_color=color,
                command=lambda s=status: self._mgmt_proses(s)
            ).pack(side="left", padx=(0, 6))

    def _on_mgmt_select(self, laporan: dict):
        self.selected_laporan = laporan
        self.mgmt_action_frame.grid()
        self.mgmt_detail_title.configure(
            text=f"Detail Laporan #{laporan['id']}: {laporan.get('judul', '')}")
        info = (f"Pelapor: {laporan.get('nama_pelapor', '')}  |  "
                f"Kel. {laporan.get('kelurahan', '')}  |  "
                f"Kec. {laporan.get('kecamatan', '')}  |  "
                f"Kategori: {laporan.get('kategori', '')}  |  "
                f"Lokasi: {laporan.get('lokasi', '')}  |  "
                f"Status: {laporan.get('status', '')}")
        self.mgmt_detail_info.configure(text=info)
        self.mgmt_catatan.delete("1.0", "end")

    def _mgmt_proses(self, status_baru: str):
        if not self.selected_laporan:
            return
        catatan = self.mgmt_catatan.get("1.0", "end-1c")
        result = self.laporan_ctrl.proses_laporan(
            laporan_id=self.selected_laporan["id"],
            admin_id=self.app.current_user["id"],
            status_baru=status_baru,
            catatan=catatan
        )
        if result["success"]:
            messagebox.showinfo("Berhasil", result["message"])
            self._refresh_all()
        else:
            messagebox.showerror("Gagal", result["message"])

    def _apply_mgmt_filter(self):
        kec = self.mgmt_kec_var.get()
        st = self.mgmt_status_var.get()

        status_param = st if st != "Semua" else None

        if kec == "Semua":
            data = self.laporan_ctrl.get_laporan_kota(status_param)
        else:
            data = self.laporan_ctrl.get_laporan_kecamatan(kec, status_param)

        self.mgmt_table.set_data(data)
        self.mgmt_action_frame.grid_remove()
        self.selected_laporan = None

    # ══════════════════════════════════════
    # TAB SWITCHING & REFRESH
    # ══════════════════════════════════════

    def _switch_tab(self, tab: str):
        self.current_tab = tab
        self.analitik_frame.grid_forget()
        self.manajemen_frame.grid_forget()

        if tab == "analitik":
            self.analitik_frame.grid(row=1, column=0, sticky="nsew",
                                     in_=self.content)
            self._render_charts()
        elif tab == "manajemen":
            self.manajemen_frame.grid(row=1, column=0, sticky="nsew",
                                      in_=self.content)
            self._apply_mgmt_filter()

    def _refresh_all(self):
        all_data = self.laporan_ctrl.get_laporan_kota()
        total = len(all_data)
        menunggu = sum(1 for d in all_data if d["status"] == "Menunggu")
        proses = sum(1 for d in all_data if "Diproses" in d.get("status", ""))
        selesai = sum(1 for d in all_data if d["status"] == "Selesai")

        self.kota_cards["total"].configure(text=str(total))
        self.kota_cards["menunggu"].configure(text=str(menunggu))
        self.kota_cards["proses"].configure(text=str(proses))
        self.kota_cards["selesai"].configure(text=str(selesai))

        if self.current_tab == "analitik":
            self._render_charts()
        elif self.current_tab == "manajemen":
            self._apply_mgmt_filter()
