# views/admin_kota/dashboard_kota.py
# Master Dashboard Admin Kota — Redesign Knowvio-style

"""
Dashboard Admin Kota dengan dua halaman:
  1. Analitik  — stat cards + 4 grafik (tren bulanan, sebaran status, 
                 per kategori, per kecamatan) + tabel laporan terbaru
  2. Manajemen — filter, tabel data, panel aksi proses/eskalasi
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.data_table import DataTable
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.wilayah import get_semua_kecamatan
from config.settings import STATUS_LAPORAN


# ── Palet warna ────────────────────────────
ACCENT       = "#567C8D"
ACCENT_HOVER = "#2F4156"
STATUS_COLORS = {
    "Menunggu":            "#FFA726",
    "Diproses Kelurahan":  "#42A5F5",
    "Diproses Kecamatan":  "#AB47BC",
    "Diproses Kota":       "#FF7043",
    "Selesai":             "#66BB6A",
    "Ditolak":             "#EF5350",
}
PIE_COLORS  = ["#FFA726", "#42A5F5", "#AB47BC", "#FF7043", "#66BB6A", "#EF5350"]
CHART_LINE  = "#567C8D"
CHART_BAR1  = "#87CEEB"
CHART_BAR2  = "#2F4156"


class DashboardKota(ctk.CTkFrame):
    """Master Dashboard Admin Kota: Analitik + Manajemen Laporan."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=("gray96", "gray12"), **kwargs)
        self.app = app
        self.laporan_ctrl = LaporanController(app.db)
        self.selected_laporan = None
        self._chart_canvases = []          # simpan referensi canvas agar GC-safe
        self._current_page = "analitik"    # track halaman aktif
        self._theme_updating = False       # guard re-render saat ganti tema

        # ── Layout: Sidebar | Content ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = Sidebar(self, app=app, menu_items=[
            {"icon": "📊", "label": "Dashboard",         "command": self._show_analitik},
            {"icon": "📋", "label": "Manajemen Laporan",  "command": self._show_manajemen},
        ])
        sidebar.grid(row=0, column=0, sticky="nsw")

        # ── Scrollable Content ──
        self.content = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=("gray78", "gray30")
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        self._show_analitik()

    # ── Override: re-render chart saat tema berubah ──
    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        if self._current_page == "analitik" and not self._theme_updating:
            self._theme_updating = True
            self.after(250, self._rerender_theme)

    def _rerender_theme(self):
        self._theme_updating = False
        self._show_analitik()

    # ──────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────

    def _clear(self):
        for cv in self._chart_canvases:
            try:
                cv.get_tk_widget().destroy()
                cv.figure.clear()
                plt.close(cv.figure)
            except Exception:
                pass
        self._chart_canvases.clear()
        for w in self.content.winfo_children():
            w.destroy()
        self.selected_laporan = None

    def _refresh(self):
        self._show_analitik()

    @staticmethod
    def _mpl_colors(dark: bool):
        """Mengembalikan dict konfigurasi warna matplotlib."""
        if dark:
            return dict(
                fig_face="#2B2B2B", ax_face="#2B2B2B",
                text="white", tick="#CCCCCC", grid="#444444"
            )
        return dict(
            fig_face="white", ax_face="white",
            text="#333333", tick="#666666", grid="#E0E0E0"
        )

    # ══════════════════════════════════════════════
    #  PAGE 1 : ANALITIK  (Knowvio-style dashboard)
    # ══════════════════════════════════════════════

    def _show_analitik(self):
        self._current_page = "analitik"
        self._clear()
        c = self.content
        dark = ctk.get_appearance_mode() == "Dark"
        mc = self._mpl_colors(dark)

        # ── Header ──
        hdr = ctk.CTkFrame(c, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(25, 4))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left")
        name = self.app.current_user.get("nama_lengkap", "Admin")
        ctk.CTkLabel(left, text=f"Selamat Datang, {name}!",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text="Berikut ringkasan laporan masyarakat Kota Manado",
                     font=ctk.CTkFont(size=13),
                     text_color=("gray50", "gray60")).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            hdr, text="🔄  Refresh Data", height=36, corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._show_analitik
        ).pack(side="right")

        # ── Subtitle ──
        ctk.CTkLabel(c, text="Highlights",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     anchor="w").pack(fill="x", padx=30, pady=(18, 8))

        # ── Stat Cards ──
        all_data = self.laporan_ctrl.get_laporan_kota()
        total    = len(all_data)
        menunggu = sum(1 for d in all_data if d["status"] == "Menunggu")
        proses   = sum(1 for d in all_data if "Diproses" in d.get("status", ""))
        selesai  = sum(1 for d in all_data if d["status"] == "Selesai")
        ditolak  = sum(1 for d in all_data if d["status"] == "Ditolak")

        cards_f = ctk.CTkFrame(c, fg_color="transparent")
        cards_f.pack(fill="x", padx=30, pady=(0, 20))
        for i in range(5):
            cards_f.grid_columnconfigure(i, weight=1)

        card_defs = [
            ("Total Laporan", total,    ACCENT,    "📋"),
            ("Menunggu",      menunggu, "#FFA726",  "⏳"),
            ("Dalam Proses",  proses,   "#42A5F5",  "🔄"),
            ("Selesai",       selesai,  "#66BB6A",  "✅"),
            ("Ditolak",       ditolak,  "#EF5350",  "❌"),
        ]
        for i, (lbl, val, clr, ico) in enumerate(card_defs):
            card = ctk.CTkFrame(cards_f, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray88", "gray28"))
            card.grid(row=0, column=i, sticky="ew", padx=5)

            inn = ctk.CTkFrame(card, fg_color="transparent")
            inn.pack(fill="x", padx=14, pady=12)

            top = ctk.CTkFrame(inn, fg_color="transparent")
            top.pack(fill="x")
            ctk.CTkLabel(top, text=lbl, font=ctk.CTkFont(size=11),
                         text_color=("gray50", "gray60")).pack(side="left")
            ctk.CTkLabel(top, text=ico, font=ctk.CTkFont(size=16),
                         text_color=("gray82", "gray32")).pack(side="right")

            ctk.CTkLabel(inn, text=f"{val:02d}",
                         font=ctk.CTkFont(size=26, weight="bold"),
                         text_color=clr, anchor="w").pack(anchor="w", pady=(4, 0))

        # ── Chart Row 1 : Tren Bulanan (60 %) + Sebaran Status (40 %) ──
        row1 = ctk.CTkFrame(c, fg_color="transparent")
        row1.pack(fill="x", padx=30, pady=(0, 14))
        row1.grid_columnconfigure(0, weight=3)
        row1.grid_columnconfigure(1, weight=2)

        stats = self.laporan_ctrl.get_statistik()

        # --- Line chart: Tren Bulanan ---
        line_card = ctk.CTkFrame(row1, corner_radius=12,
                                 fg_color=("white", "gray17"),
                                 border_width=1, border_color=("gray88", "gray28"))
        line_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

        li = ctk.CTkFrame(line_card, fg_color="transparent")
        li.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(li, text="📈  Tren Bulanan",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(side="left")
        ctk.CTkLabel(li, text="Aktivitas laporan per bulan",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(side="right")

        line_area = ctk.CTkFrame(line_card, fg_color="transparent", height=185)
        line_area.pack(fill="x", padx=8, pady=(0, 8))
        line_area.pack_propagate(False)

        bulanan = stats.get("bulanan", [])
        bulan_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                       "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        if bulanan:
            x_data = [bulan_names[b["bulan"] - 1] for b in bulanan]
            y_data = [b["jumlah"] for b in bulanan]
        else:
            x_data = bulan_names[:6]
            y_data = [0] * 6

        fig_l = Figure(figsize=(5.5, 2.0), dpi=100)
        fig_l.set_facecolor(mc["fig_face"])
        ax_l = fig_l.add_subplot(111)
        ax_l.set_facecolor(mc["ax_face"])
        ax_l.plot(x_data, y_data, color=CHART_LINE, linewidth=2,
                  marker="o", markersize=4, zorder=3)
        ax_l.fill_between(x_data, y_data, alpha=0.15, color=CHART_LINE)
        ax_l.set_ylabel("Jumlah", color=mc["text"], fontsize=8)
        ax_l.tick_params(colors=mc["tick"], labelsize=7)
        ax_l.grid(True, alpha=0.25, color=mc["grid"])
        for sp in ax_l.spines.values():
            sp.set_visible(False)
        fig_l.tight_layout(pad=1.0)

        cv_l = FigureCanvasTkAgg(fig_l, master=line_area)
        cv_l.draw()
        cv_l.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(cv_l)

        # --- Donut chart: Sebaran Status ---
        donut_card = ctk.CTkFrame(row1, corner_radius=12,
                                  fg_color=("white", "gray17"),
                                  border_width=1, border_color=("gray88", "gray28"))
        donut_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        di = ctk.CTkFrame(donut_card, fg_color="transparent")
        di.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(di, text="🍩  Sebaran Status",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(side="left")

        donut_area = ctk.CTkFrame(donut_card, fg_color="transparent", height=185)
        donut_area.pack(fill="x", padx=8, pady=(0, 8))
        donut_area.pack_propagate(False)

        per_status = stats.get("per_status", [])
        if per_status:
            d_labels = [s["status"] for s in per_status]
            d_values = [s["jumlah"] for s in per_status]
            d_colors = [STATUS_COLORS.get(s["status"], "#95A5A6") for s in per_status]
        else:
            d_labels = ["Belum ada"]
            d_values = [1]
            d_colors = ["#CCCCCC"]

        fig_d = Figure(figsize=(3.2, 2.0), dpi=100)
        fig_d.set_facecolor(mc["fig_face"])
        ax_d = fig_d.add_subplot(111)
        ax_d.set_facecolor(mc["ax_face"])
        wedges, texts, autotexts = ax_d.pie(
            d_values, labels=None, colors=d_colors,
            autopct='%1.0f%%', startangle=90,
            wedgeprops=dict(width=0.42, edgecolor=mc["fig_face"], linewidth=1.5),
            textprops=dict(color=mc["text"], fontsize=7),
            pctdistance=0.78
        )
        # Center text
        ax_d.text(0, 0.08, f"{total}", ha="center", va="center",
                  fontsize=18, fontweight="bold", color=mc["text"])
        ax_d.text(0, -0.12, "Total", ha="center", va="center",
                  fontsize=8, color=mc["tick"])
        # Legend below
        ax_d.legend(wedges, d_labels, loc="lower center",
                    bbox_to_anchor=(0.5, -0.15), ncol=3,
                    fontsize=6, frameon=False,
                    labelcolor=mc["text"])
        fig_d.tight_layout(pad=0.3)

        cv_d = FigureCanvasTkAgg(fig_d, master=donut_area)
        cv_d.draw()
        cv_d.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(cv_d)

        # ── Chart Row 2 : Kategori (50 %) + Kecamatan (50 %) ──
        row2 = ctk.CTkFrame(c, fg_color="transparent")
        row2.pack(fill="x", padx=30, pady=(0, 14))
        row2.grid_columnconfigure(0, weight=1)
        row2.grid_columnconfigure(1, weight=1)

        # --- Bar chart: Kategori ---
        kat_card = ctk.CTkFrame(row2, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray88", "gray28"))
        kat_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

        ki = ctk.CTkFrame(kat_card, fg_color="transparent")
        ki.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(ki, text="📊  Laporan per Kategori",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(side="left")

        kat_area = ctk.CTkFrame(kat_card, fg_color="transparent", height=175)
        kat_area.pack(fill="x", padx=8, pady=(0, 8))
        kat_area.pack_propagate(False)

        per_kategori = stats.get("per_kategori", [])
        if per_kategori:
            k_labels = [k["kategori"][:14] for k in per_kategori]
            k_values = [k["jumlah"] for k in per_kategori]
        else:
            k_labels = ["(kosong)"]
            k_values = [0]

        fig_k = Figure(figsize=(4.5, 1.9), dpi=100)
        fig_k.set_facecolor(mc["fig_face"])
        ax_k = fig_k.add_subplot(111)
        ax_k.set_facecolor(mc["ax_face"])
        bars_k = ax_k.barh(k_labels, k_values, color=CHART_BAR1,
                           edgecolor="white", linewidth=0.5, height=0.55)
        ax_k.invert_yaxis()
        ax_k.tick_params(colors=mc["tick"], labelsize=7)
        ax_k.set_xlabel("Jumlah", color=mc["text"], fontsize=8)
        for sp in ax_k.spines.values():
            sp.set_visible(False)
        ax_k.grid(axis="x", alpha=0.2, color=mc["grid"])
        # Value labels
        for bar in bars_k:
            w = bar.get_width()
            if w > 0:
                ax_k.text(w + 0.2, bar.get_y() + bar.get_height() / 2,
                          f"{int(w)}", va="center", fontsize=7, color=mc["text"])
        fig_k.tight_layout(pad=1.0)

        cv_k = FigureCanvasTkAgg(fig_k, master=kat_area)
        cv_k.draw()
        cv_k.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(cv_k)

        # --- Bar chart: Kecamatan ---
        kec_card = ctk.CTkFrame(row2, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray88", "gray28"))
        kec_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        kci = ctk.CTkFrame(kec_card, fg_color="transparent")
        kci.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(kci, text="🏢  Laporan per Kecamatan",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(side="left")

        kec_area = ctk.CTkFrame(kec_card, fg_color="transparent", height=175)
        kec_area.pack(fill="x", padx=8, pady=(0, 8))
        kec_area.pack_propagate(False)

        per_kecamatan = stats.get("per_kecamatan", [])
        if per_kecamatan:
            kc_labels = [k["kecamatan"] for k in per_kecamatan]
            kc_values = [k["jumlah"] for k in per_kecamatan]
        else:
            kc_labels = ["(kosong)"]
            kc_values = [0]

        fig_kc = Figure(figsize=(4.5, 1.9), dpi=100)
        fig_kc.set_facecolor(mc["fig_face"])
        ax_kc = fig_kc.add_subplot(111)
        ax_kc.set_facecolor(mc["ax_face"])
        bars_kc = ax_kc.barh(kc_labels, kc_values, color=CHART_BAR2,
                             edgecolor="white", linewidth=0.5, height=0.55)
        ax_kc.invert_yaxis()
        ax_kc.tick_params(colors=mc["tick"], labelsize=7)
        ax_kc.set_xlabel("Jumlah", color=mc["text"], fontsize=8)
        for sp in ax_kc.spines.values():
            sp.set_visible(False)
        ax_kc.grid(axis="x", alpha=0.2, color=mc["grid"])
        for bar in bars_kc:
            w = bar.get_width()
            if w > 0:
                ax_kc.text(w + 0.2, bar.get_y() + bar.get_height() / 2,
                           f"{int(w)}", va="center", fontsize=7, color=mc["text"])
        fig_kc.tight_layout(pad=1.0)

        cv_kc = FigureCanvasTkAgg(fig_kc, master=kec_area)
        cv_kc.draw()
        cv_kc.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(cv_kc)

        # ── Laporan Terbaru (Tabel) ──
        tbl_card = ctk.CTkFrame(c, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray88", "gray28"))
        tbl_card.pack(fill="x", padx=30, pady=(0, 20))

        ti = ctk.CTkFrame(tbl_card, fg_color="transparent")
        ti.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(ti, text="📌  Laporan Terbaru",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").pack(side="left")
        ctk.CTkLabel(ti, text="10 laporan terakhir masuk",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(side="right")

        # Table header
        th = ctk.CTkFrame(tbl_card, fg_color=("gray94", "gray20"),
                          corner_radius=6, height=34)
        th.pack(fill="x", padx=16, pady=(10, 0))
        th.pack_propagate(False)

        th_cols = [("No", 50), ("Judul", 180), ("Pelapor", 120),
                   ("Kelurahan", 110), ("Kategori", 110), ("Status", 130),
                   ("Tanggal", 110)]
        for label, w in th_cols:
            ctk.CTkLabel(th, text=label, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=("gray45", "gray65"), anchor="w"
                         ).pack(side="left", padx=(8, 0))

        # Table rows (last 10)
        recent = all_data[:10]
        rows_f = ctk.CTkFrame(tbl_card, fg_color="transparent")
        rows_f.pack(fill="x", padx=16, pady=(0, 14))

        if not recent:
            ctk.CTkLabel(rows_f, text="Belum ada laporan.",
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(pady=20)
        else:
            for idx, lap in enumerate(recent):
                row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
                rr = ctk.CTkFrame(rows_f, fg_color=row_bg, height=38,
                                  corner_radius=4)
                rr.pack(fill="x", pady=1)
                rr.pack_propagate(False)

                ctk.CTkLabel(rr, text=f"#{lap['id']}", width=50,
                             font=ctk.CTkFont(size=12),
                             text_color=(ACCENT, "#87CEEB"),
                             anchor="w").pack(side="left", padx=(8, 0))
                ctk.CTkLabel(rr, text=truncate_text(lap.get("judul", ""), 22),
                             width=180, font=ctk.CTkFont(size=12),
                             anchor="w").pack(side="left", padx=(8, 0))
                ctk.CTkLabel(rr, text=truncate_text(lap.get("nama_pelapor", ""), 16),
                             width=120, font=ctk.CTkFont(size=12),
                             anchor="w").pack(side="left", padx=(8, 0))
                ctk.CTkLabel(rr, text=truncate_text(lap.get("kelurahan", ""), 14),
                             width=110, font=ctk.CTkFont(size=12),
                             anchor="w").pack(side="left", padx=(8, 0))
                ctk.CTkLabel(rr, text=truncate_text(lap.get("kategori", ""), 14),
                             width=110, font=ctk.CTkFont(size=12),
                             anchor="w").pack(side="left", padx=(8, 0))

                st_color = STATUS_COLORS.get(lap["status"], "#95A5A6")
                ctk.CTkLabel(rr, text=f"● {lap['status']}", width=130,
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=st_color, anchor="w"
                             ).pack(side="left", padx=(8, 0))

                ctk.CTkLabel(rr, text=format_tanggal(lap.get("created_at")),
                             width=110, font=ctk.CTkFont(size=11),
                             text_color=("gray50", "gray60"),
                             anchor="w").pack(side="left", padx=(8, 0))

    # ══════════════════════════════════════════════
    #  PAGE 2 : MANAJEMEN LAPORAN  (Ticket-list style)
    # ══════════════════════════════════════════════

    _ITEMS_PER_PAGE = 10      # jumlah baris per halaman

    def _show_manajemen(self):
        self._current_page = "manajemen"
        self._clear()
        self._mgmt_page = 1        # reset ke halaman pertama
        c = self.content

        # ── Header Row (title left, filter+search right) ──
        hdr = ctk.CTkFrame(c, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(25, 18))

        # Left: title + subtitle
        left_hdr = ctk.CTkFrame(hdr, fg_color="transparent")
        left_hdr.pack(side="left")
        ctk.CTkLabel(left_hdr, text="Manajemen Laporan",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(left_hdr, text="Kelola dan proses laporan dari seluruh Kota Manado",
                     font=ctk.CTkFont(size=13),
                     text_color=("gray50", "gray60")).pack(anchor="w", pady=(2, 0))

        # Right: filter button + search
        right_hdr = ctk.CTkFrame(hdr, fg_color="transparent")
        right_hdr.pack(side="right")

        # Filter toggle (opens/closes filter bar)
        self._filter_visible = True
        self._filter_btn = ctk.CTkButton(
            right_hdr, text="🔽 Filters", height=34, corner_radius=8, width=100,
            font=ctk.CTkFont(size=12),
            fg_color=(ACCENT, ACCENT), hover_color=(ACCENT_HOVER, ACCENT_HOVER),
            command=self._toggle_filter_bar
        )
        self._filter_btn.pack(side="left", padx=(0, 8))

        # Search bar
        self.mgmt_search_var = ctk.StringVar(value="")
        self.mgmt_search = ctk.CTkEntry(
            right_hdr, height=34, corner_radius=8, width=250,
            placeholder_text="🔍  Cari judul / pelapor / ID ...",
            textvariable=self.mgmt_search_var,
            font=ctk.CTkFont(size=12)
        )
        self.mgmt_search.pack(side="left")
        self.mgmt_search.bind("<KeyRelease>", lambda _: self._apply_filter())

        # ── Filter Bar (collapsible) ──
        self._filter_card = ctk.CTkFrame(c, corner_radius=10,
                                          fg_color=("white", "gray17"),
                                          border_width=1, border_color=("gray88", "gray28"))
        self._filter_card.pack(fill="x", padx=30, pady=(0, 15))

        fi = ctk.CTkFrame(self._filter_card, fg_color="transparent")
        fi.pack(fill="x", padx=20, pady=12)

        # Kecamatan
        ctk.CTkLabel(fi, text="Kecamatan", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=("gray50", "gray60")).pack(side="left", padx=(0, 4))
        kecamatan_list = ["Semua"] + get_semua_kecamatan()
        self.mgmt_kec = ctk.CTkComboBox(
            fi, values=kecamatan_list,
            width=160, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_filter(), state="readonly"
        )
        self.mgmt_kec.pack(side="left", padx=(0, 16))
        self.mgmt_kec.set("Semua")

        # Status
        ctk.CTkLabel(fi, text="Status", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=("gray50", "gray60")).pack(side="left", padx=(0, 4))
        self.mgmt_status = ctk.CTkComboBox(
            fi, values=["Semua"] + STATUS_LAPORAN,
            width=160, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_filter(), state="readonly"
        )
        self.mgmt_status.pack(side="left", padx=(0, 16))
        self.mgmt_status.set("Semua")

        # Reset
        ctk.CTkButton(
            fi, text="Reset", height=32, corner_radius=8, width=80,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._reset_filter
        ).pack(side="right")

        # ── Ticket Table Card ──
        self._table_card = ctk.CTkFrame(c, corner_radius=12,
                                        fg_color=("white", "gray17"),
                                        border_width=1, border_color=("gray88", "gray28"))
        self._table_card.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        # Table header
        header_row = ctk.CTkFrame(self._table_card,
                                   fg_color=("gray94", "gray20"),
                                   corner_radius=6, height=40)
        header_row.pack(fill="x", padx=14, pady=(12, 0))
        header_row.pack_propagate(False)

        headers = [
            ("Pelapor", 190),
            ("Ticket ID", 90),
            ("Judul", 210),
            ("Kategori", 120),
            ("Status", 130),
            ("Tanggal", 120),
        ]
        for label, w in headers:
            ctk.CTkLabel(
                header_row, text=label, width=w,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray45", "gray65"), anchor="w"
            ).pack(side="left", padx=(12, 0))

        # Scrollable rows area
        self.mgmt_list = ctk.CTkScrollableFrame(
            self._table_card, fg_color="transparent", height=380
        )
        self.mgmt_list.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        # Pagination container
        self._pagination_frame = ctk.CTkFrame(self._table_card, fg_color="transparent", height=50)
        self._pagination_frame.pack(fill="x", padx=14, pady=(4, 12))
        self._pagination_frame.pack_propagate(False)

        self._apply_filter()

    # ── Filter bar toggle ──

    def _toggle_filter_bar(self):
        if self._filter_visible:
            self._filter_card.pack_forget()
            self._filter_visible = False
            self._filter_btn.configure(text="🔼 Filters")
        else:
            # Re-insert filter card before the table card
            self._filter_card.pack(fill="x", padx=30, pady=(0, 15),
                                   before=self._table_card)
            self._filter_visible = True
            self._filter_btn.configure(text="🔽 Filters")

    # ── Filter logic ──

    def _apply_filter(self):
        kec = self.mgmt_kec.get()
        st  = self.mgmt_status.get()
        status_p = st if st != "Semua" else None

        if kec == "Semua":
            data = self.laporan_ctrl.get_laporan_kota(status_p)
        else:
            data = self.laporan_ctrl.get_laporan_kecamatan(kec, status_p)

        q = self.mgmt_search_var.get().strip().lower()
        if q:
            def _match(item: dict) -> bool:
                hay = " ".join([
                    str(item.get("id", "")),
                    item.get("judul", ""),
                    item.get("nama_pelapor", ""),
                    item.get("kelurahan", ""),
                    item.get("kecamatan", ""),
                    item.get("kategori", ""),
                ]).lower()
                return q in hay

            data = [d for d in data if _match(d)]

        self._mgmt_all_data = data
        self._mgmt_page = 1
        self._render_mgmt_page()
        self.selected_laporan = None

    def _reset_filter(self):
        self.mgmt_kec.set("Semua")
        self.mgmt_status.set("Semua")
        self.mgmt_search_var.set("")
        self._apply_filter()

    # ── Pagination helpers ──

    def _total_pages(self):
        n = len(self._mgmt_all_data)
        return max(1, (n + self._ITEMS_PER_PAGE - 1) // self._ITEMS_PER_PAGE)

    def _goto_page(self, page: int):
        total = self._total_pages()
        self._mgmt_page = max(1, min(page, total))
        self._render_mgmt_page()

    def _render_mgmt_page(self):
        """Render rows for the current page + update pagination."""
        start = (self._mgmt_page - 1) * self._ITEMS_PER_PAGE
        end = start + self._ITEMS_PER_PAGE
        page_data = self._mgmt_all_data[start:end]
        self._render_mgmt_rows(page_data)
        self._render_pagination()

    def _render_pagination(self):
        """Draw pagination controls like: ← 1 2 3 ... 10 →"""
        for w in self._pagination_frame.winfo_children():
            w.destroy()

        total_pages = self._total_pages()
        total_items = len(self._mgmt_all_data)
        current = self._mgmt_page

        # Info text: "Menampilkan X-Y dari Z"
        s = (current - 1) * self._ITEMS_PER_PAGE + 1
        e = min(current * self._ITEMS_PER_PAGE, total_items)
        info_text = f"Menampilkan {s}-{e} dari {total_items}"
        ctk.CTkLabel(
            self._pagination_frame, text=info_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack(side="left")

        # Page buttons container (right-aligned)
        pg_f = ctk.CTkFrame(self._pagination_frame, fg_color="transparent")
        pg_f.pack(side="right")

        btn_style_inactive = dict(
            height=30, width=34, corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=("gray30", "gray80"),
            hover_color=("gray85", "gray25"),
        )
        btn_style_active = dict(
            height=30, width=34, corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=(ACCENT, ACCENT),
            text_color="white",
            hover_color=(ACCENT_HOVER, ACCENT_HOVER),
        )

        # ← Previous
        ctk.CTkButton(
            pg_f, text="←", **btn_style_inactive,
            state="normal" if current > 1 else "disabled",
            command=lambda: self._goto_page(current - 1)
        ).pack(side="left", padx=2)

        # Page numbers: show max 5 pages with ellipsis
        if total_pages <= 7:
            pages_to_show = list(range(1, total_pages + 1))
        else:
            pages_to_show = []
            if current <= 4:
                pages_to_show = [1, 2, 3, 4, 5, "...", total_pages]
            elif current >= total_pages - 3:
                pages_to_show = [1, "...",
                                 total_pages - 4, total_pages - 3,
                                 total_pages - 2, total_pages - 1, total_pages]
            else:
                pages_to_show = [1, "...",
                                 current - 1, current, current + 1,
                                 "...", total_pages]

        for p in pages_to_show:
            if p == "...":
                ctk.CTkLabel(
                    pg_f, text="•••", width=30,
                    font=ctk.CTkFont(size=10),
                    text_color=("gray50", "gray60")
                ).pack(side="left", padx=1)
            else:
                style = btn_style_active if p == current else btn_style_inactive
                ctk.CTkButton(
                    pg_f, text=str(p), **style,
                    command=lambda pp=p: self._goto_page(pp)
                ).pack(side="left", padx=2)

        # → Next
        ctk.CTkButton(
            pg_f, text="→", **btn_style_inactive,
            state="normal" if current < total_pages else "disabled",
            command=lambda: self._goto_page(current + 1)
        ).pack(side="left", padx=2)

    def _render_mgmt_rows(self, data: list[dict]):
        for w in self.mgmt_list.winfo_children():
            w.destroy()

        if not data:
            ctk.CTkLabel(
                self.mgmt_list, text="Tidak ada laporan.",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60")
            ).pack(pady=20)
            return

        for idx, lap in enumerate(data):
            row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
            row = ctk.CTkFrame(
                self.mgmt_list, fg_color=row_bg,
                height=54, corner_radius=4
            )
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            # Pelapor (name + kelurahan subtitle)
            pelapor_f = ctk.CTkFrame(row, fg_color="transparent", width=190)
            pelapor_f.pack(side="left", padx=(12, 0))
            pelapor_f.pack_propagate(False)
            ctk.CTkLabel(
                pelapor_f, text=truncate_text(lap.get("nama_pelapor", ""), 22),
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            ).pack(anchor="w", pady=(8, 0))
            ctk.CTkLabel(
                pelapor_f, text=truncate_text(lap.get("kelurahan", ""), 24),
                font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray60"),
                anchor="w"
            ).pack(anchor="w")

            # Ticket ID
            ctk.CTkLabel(
                row, text=f"#{lap['id']:06d}", width=90,
                font=ctk.CTkFont(size=11),
                text_color=(ACCENT, "#87CEEB"), anchor="w"
            ).pack(side="left", padx=(12, 0))

            # Judul (subject)
            judul_f = ctk.CTkFrame(row, fg_color="transparent", width=210)
            judul_f.pack(side="left", padx=(12, 0))
            judul_f.pack_propagate(False)
            ctk.CTkLabel(
                judul_f, text=truncate_text(lap.get("judul", ""), 26),
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(anchor="w", pady=(8, 0))
            ctk.CTkLabel(
                judul_f,
                text=truncate_text(lap.get("deskripsi", ""), 32),
                font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray60"),
                anchor="w"
            ).pack(anchor="w")

            # Kategori (priority-like)
            kat_text = truncate_text(lap.get("kategori", ""), 14)
            kat_frame = ctk.CTkFrame(row, fg_color=("#EEF2FF", "gray25"),
                                      corner_radius=6, width=110)
            kat_frame.pack(side="left", padx=(12, 0))
            ctk.CTkLabel(
                kat_frame, text=kat_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=(ACCENT, "#87CEEB")
            ).pack(padx=8, pady=4)

            # Status badge
            st_color = STATUS_COLORS.get(lap["status"], "#95A5A6")
            status_frame = ctk.CTkFrame(row, fg_color=st_color,
                                         corner_radius=6, width=110)
            status_frame.pack(side="left", padx=(12, 0))
            ctk.CTkLabel(
                status_frame, text=lap["status"],
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="white"
            ).pack(padx=8, pady=4)

            # Tanggal
            ctk.CTkLabel(
                row, text=format_tanggal(lap.get("created_at")),
                width=110, font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60"), anchor="w"
            ).pack(side="left", padx=(12, 0))

            # Three-dot menu
            ctk.CTkLabel(
                row, text="•••", width=30,
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60")
            ).pack(side="right", padx=(0, 10))

            # Click binding
            def _bind_click(widget, data=lap):
                widget.bind("<Button-1>", lambda e: self._show_detail_page(data))
                if hasattr(widget, "winfo_children"):
                    for child in widget.winfo_children():
                        _bind_click(child, data)

            _bind_click(row)

            # Hover effects
            hover_bg = ("gray96", "gray22")
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=hover_bg))
            row.bind("<Leave>", lambda e, r=row, b=row_bg: r.configure(fg_color=b))

            # Separator line
            ctk.CTkFrame(self.mgmt_list, height=1,
                         fg_color=("gray92", "gray25")).pack(fill="x")

    # ══════════════════════════════════════════════
    #  PAGE 3 : DETAIL LAPORAN
    # ══════════════════════════════════════════════

    def _show_detail_page(self, laporan: dict):
        """Halaman detail laporan terpisah untuk Admin Kota."""
        self._current_page = "detail"
        self._clear()
        c = self.content
        self.selected_laporan = laporan

        # ── Header ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 20))

        ctk.CTkButton(
            header, text="←  Kembali", height=34, corner_radius=8, width=120,
            font=ctk.CTkFont(size=13), fg_color="transparent",
            border_width=1, border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._show_manajemen
        ).pack(side="left")

        ctk.CTkLabel(header, text=f"Detail Laporan #{laporan['id']}",
                     font=ctk.CTkFont(size=22, weight="bold")
                     ).pack(side="left", padx=(20, 0))
        StatusBadge(header, status=laporan["status"]).pack(side="right")

        # ── Info Card ──
        info_card = ctk.CTkFrame(c, corner_radius=12,
                                  fg_color=("white", "gray17"),
                                  border_width=1, border_color=("gray88", "gray28"))
        info_card.pack(fill="x", padx=30, pady=(0, 15))

        ic = ctk.CTkFrame(info_card, fg_color="transparent")
        ic.pack(fill="x", padx=28, pady=24)

        info_row = ctk.CTkFrame(ic, fg_color="transparent")
        info_row.pack(fill="x")
        info_row.grid_columnconfigure(0, weight=1)
        info_row.grid_columnconfigure(1, weight=1)

        # Left column
        left = ctk.CTkFrame(info_row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        for lbl, val in [("Judul", laporan.get("judul", "")),
                          ("Pelapor", laporan.get("nama_pelapor", "")),
                          ("Kategori", laporan.get("kategori", "")),
                          ("Lokasi", laporan.get("lokasi", ""))]:
            rf = ctk.CTkFrame(left, fg_color="transparent")
            rf.pack(fill="x", pady=3)
            ctk.CTkLabel(rf, text=f"{lbl}:", width=85,
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60"), anchor="w").pack(side="left")
            ctk.CTkLabel(rf, text=val,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w", wraplength=300).pack(side="left")

        # Right column
        right = ctk.CTkFrame(info_row, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        for lbl, val in [("Kelurahan", laporan.get("kelurahan", "")),
                          ("Kecamatan", laporan.get("kecamatan", "")),
                          ("Dibuat", format_tanggal(laporan.get("created_at"))),
                          ("Diperbarui", format_tanggal(laporan.get("updated_at", laporan.get("created_at"))))]:
            rf = ctk.CTkFrame(right, fg_color="transparent")
            rf.pack(fill="x", pady=3)
            ctk.CTkLabel(rf, text=f"{lbl}:", width=95,
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60"), anchor="w").pack(side="left")
            ctk.CTkLabel(rf, text=val,
                         font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

        # Deskripsi
        ctk.CTkFrame(ic, height=1, fg_color=("gray88", "gray28")).pack(
            fill="x", pady=(14, 10))
        ctk.CTkLabel(ic, text="Deskripsi:",
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(ic, text=laporan.get("deskripsi", ""),
                     font=ctk.CTkFont(size=12), anchor="w",
                     wraplength=650, justify="left").pack(fill="x", pady=(4, 0))

        if laporan.get("status") != "Selesai":
            # ── Action Card ──
            action_card = ctk.CTkFrame(c, corner_radius=12,
                                        fg_color=("white", "gray17"),
                                        border_width=1, border_color=("gray88", "gray28"))
            action_card.pack(fill="x", padx=30, pady=(0, 15))

            af = ctk.CTkFrame(action_card, fg_color="transparent")
            af.pack(fill="x", padx=28, pady=20)

            ctk.CTkLabel(af, text="⚡  Aksi Admin Kota",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=(ACCENT, "#87CEEB"), anchor="w").pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(af, text="Catatan Admin *",
                         font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
            self.catatan_text = ctk.CTkTextbox(
                af, height=60, corner_radius=8,
                font=ctk.CTkFont(size=12),
                border_width=1, border_color=("gray72", "gray35"))
            self.catatan_text.pack(fill="x", pady=(3, 12))

            btn_f = ctk.CTkFrame(af, fg_color="transparent")
            btn_f.pack(fill="x")

            actions = [
                ("✅ Proses Kota", "Diproses Kota", "#1E88E5"),
                ("🏁 Selesai",     "Selesai",       "#43A047"),
                ("❌ Tolak",       "Ditolak",       "#E53935"),
            ]
            for text, status, color in actions:
                ctk.CTkButton(
                    btn_f, text=text, height=38, corner_radius=8,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color=color, hover_color=color,
                    command=lambda s=status: self._do_proses(s)
                ).pack(side="left", padx=(0, 8))

        # ── Timeline Card ──
        tl_card = ctk.CTkFrame(c, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray88", "gray28"))
        tl_card.pack(fill="x", padx=30, pady=(0, 20))

        tc = ctk.CTkFrame(tl_card, fg_color="transparent")
        tc.pack(fill="x", padx=28, pady=20)

        ctk.CTkLabel(tc, text="📌  Timeline Status",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=(ACCENT, "#87CEEB"), anchor="w").pack(fill="x", pady=(0, 12))

        riwayat = self.laporan_ctrl.get_riwayat_laporan(laporan["id"])
        if not riwayat:
            ctk.CTkLabel(tc, text="Belum ada riwayat perubahan status.",
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(pady=10)
        else:
            tl_f = ctk.CTkFrame(tc, fg_color="transparent")
            tl_f.pack(fill="x")

            status_bg = {
                "Menunggu": ("#E9F2FF", "#2B2B2B"),
                "Selesai": ("#E9F8EF", "#2B2B2B"),
            }
            diproses_bg = ("#FFF4D6", "#2B2B2B")

            for j, rw in enumerate(riwayat):
                tanggal = format_tanggal(rw.get("created_at"))
                if ", " in tanggal:
                    date_part, time_part = tanggal.split(", ", 1)
                else:
                    date_part, time_part = tanggal, ""

                card = ctk.CTkFrame(
                    tl_f, corner_radius=10,
                    fg_color=("white", "gray17"),
                    border_width=1, border_color=("gray88", "gray28")
                )
                card.pack(fill="x", pady=(0, 8))

                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=10)

                st_value = rw.get("status_baru", "")
                if "Diproses" in st_value:
                    pill_bg = diproses_bg
                else:
                    pill_bg = status_bg.get(st_value, ("#EEF2FF", "#2B2B2B"))
                time_card = ctk.CTkFrame(
                    row, width=105, corner_radius=9,
                    fg_color=pill_bg, border_width=0
                )
                time_card.pack(side="left")
                time_card.pack_propagate(False)

                ctk.CTkLabel(
                    time_card, text=date_part,
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color=(ACCENT, "#87CEEB")
                ).pack(pady=(6, 0))
                ctk.CTkLabel(
                    time_card, text=time_part,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=(ACCENT, "#87CEEB")
                ).pack(pady=(2, 6))

                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=(12, 0))

                st_text = rw.get("status_baru", "")
                ctk.CTkLabel(
                    info, text=st_text,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w"
                ).pack(fill="x")

                catatan = rw.get("catatan_admin", "")
                admin_name = rw.get("nama_admin", "Sistem")
                sub_text = f"oleh {admin_name}: {catatan}" if catatan else ""
                if sub_text:
                    ctk.CTkLabel(
                        info, text=sub_text,
                        font=ctk.CTkFont(size=10),
                        text_color=("gray45", "gray62"),
                        anchor="w", wraplength=520
                    ).pack(fill="x", pady=(2, 0))

                ctk.CTkLabel(
                    row, text="+",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=("gray60", "gray50")
                ).pack(side="right")

    def _do_proses(self, status_baru: str):
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
            self._show_manajemen()
        else:
            messagebox.showerror("Gagal", result["message"])


