# views/warga/dashboard_warga.py
# Dashboard Warga — InvestIQ-style dashboard + Support Ticket-style form

import customtkinter as ctk
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.settings import KATEGORI_LAPORAN, STATUS_LAPORAN, PRIORITAS_COLORS
from config.wilayah import get_semua_kecamatan, get_kelurahan_by_kecamatan


# ── Palette Sky Blue ──
NAVY      = "#2F4156"
TEAL      = "#567C8D"
SKY_BLUE  = "#87CEEB"
BEIGE     = "#C8D9E6"
OFF_WHITE = "#F5EFEB"

# ── Warna dot per-status ──
STATUS_DOT_COLORS = {
    "Menunggu": "#FFA726",
    "Diproses Kelurahan": "#42A5F5",
    "Diproses Kecamatan": "#AB47BC",
    "Diproses Kota": "#FF7043",
    "Selesai": "#66BB6A",
    "Ditolak": "#EF5350",
}


class DashboardWarga(ctk.CTkFrame):
    """Dashboard Warga: Dashboard / Buat Laporan / Detail."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=("gray96", "gray12"), **kwargs)
        self.app = app
        self.laporan_ctrl = LaporanController(app.db)
        self.all_laporan = []
        self.filtered_laporan = []
        self.selected_laporan = None

        # ── Layout: Sidebar + Content ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = Sidebar(self, app=app, menu_items=[
            {"icon": "🏠", "label": "Dashboard", "command": self._show_dashboard_page},
            {"icon": "📝", "label": "Buat Laporan", "command": self._show_form_page},
            {"icon": "📋", "label": "Riwayat Laporan", "command": self._show_riwayat_page},
        ])
        sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=("gray78", "gray30")
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        self._load_data()
        self._show_dashboard_page()

    # ══════════════════════════════════════════
    # DATA
    # ══════════════════════════════════════════

    def _load_data(self):
        uid = self.app.current_user["id"]
        self.all_laporan = self.laporan_ctrl.get_laporan_warga(uid)
        self.filtered_laporan = list(self.all_laporan)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()
        self.selected_laporan = None

    def _refresh(self):
        self._load_data()
        self._show_dashboard_page()

    # ══════════════════════════════════════════
    # PAGE 1 : DASHBOARD (InvestIQ-style)
    # ══════════════════════════════════════════

    def _show_dashboard_page(self):
        self._clear_content()
        self._load_data()
        c = self.content
        data = self.all_laporan

        # ── Header ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 5))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        name = self.app.current_user.get("nama_lengkap", "User")
        ctk.CTkLabel(
            left, text=f"Selamat Datang, {name}!",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Pantau laporan pengaduan dan aspirasi Anda.",
            font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 0))

        # Header buttons
        hdr_btns = ctk.CTkFrame(header, fg_color="transparent")
        hdr_btns.pack(side="right")
        ctk.CTkButton(
            hdr_btns, text="🔽  Filter", height=34, corner_radius=8, width=100,
            font=ctk.CTkFont(size=12), fg_color="transparent",
            border_width=1, border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._show_dashboard_page
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            hdr_btns, text="＋  Buat Laporan",
            height=34, corner_radius=8, width=150,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=(TEAL, TEAL), hover_color=(NAVY, NAVY),
            command=self._show_form_page
        ).pack(side="left")

        # ── Summary + Activity Row ──
        row1 = ctk.CTkFrame(c, fg_color="transparent")
        row1.pack(fill="x", padx=30, pady=(18, 0))
        row1.grid_columnconfigure(0, weight=2)
        row1.grid_columnconfigure(1, weight=3)

        # ═══ Summary Card (large, left) ═══
        summary_card = ctk.CTkFrame(
            row1, corner_radius=14,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        summary_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 12))

        sc = ctk.CTkFrame(summary_card, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=20, pady=18)

        sc_hdr = ctk.CTkFrame(sc, fg_color="transparent")
        sc_hdr.pack(fill="x")
        ctk.CTkLabel(sc_hdr, text="Ringkasan",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkLabel(sc_hdr, text="Semua ▾",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(side="right")

        ctk.CTkLabel(sc, text="Pantau statistik laporan Anda.",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w", pady=(2, 14))

        # Summary stats row
        stats_row = ctk.CTkFrame(sc, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 10))

        total = len(data)
        selesai = sum(1 for d in data if d["status"] == "Selesai")

        # Total stat
        ts = ctk.CTkFrame(stats_row, fg_color="transparent")
        ts.pack(side="left", padx=(0, 30))
        ctk.CTkLabel(ts, text="↓  Total Laporan",
                     font=ctk.CTkFont(size=12),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        ctk.CTkLabel(ts, text=f"{total}",
                     font=ctk.CTkFont(size=34, weight="bold")).pack(anchor="w")

        # Selesai stat
        ss = ctk.CTkFrame(stats_row, fg_color="transparent")
        ss.pack(side="left")
        ctk.CTkLabel(ss, text="↑  Selesai",
                     font=ctk.CTkFont(size=12),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        ctk.CTkLabel(ss, text=f"{selesai}",
                     font=ctk.CTkFont(size=34, weight="bold")).pack(anchor="w")

        # Mini bar chart (status distribution)
        chart_f = ctk.CTkFrame(sc, fg_color="transparent", height=60)
        chart_f.pack(fill="x", pady=(4, 0))
        chart_f.pack_propagate(False)

        status_counts = {}
        for s_name in ["Menunggu", "Diproses", "Selesai", "Ditolak"]:
            if s_name == "Diproses":
                status_counts[s_name] = sum(1 for d in data if "Diproses" in d.get("status", ""))
            else:
                status_counts[s_name] = sum(1 for d in data if d["status"] == s_name)

        max_val = max(status_counts.values()) if status_counts.values() and max(status_counts.values()) > 0 else 1
        bar_colors = {"Menunggu": "#FFA726", "Diproses": SKY_BLUE, "Selesai": "#66BB6A", "Ditolak": "#EF5350"}

        for s_name, count in status_counts.items():
            bar_col = ctk.CTkFrame(chart_f, fg_color="transparent", width=40)
            bar_col.pack(side="left", expand=True, fill="y", padx=4)
            bar_col.pack_propagate(False)

            bar_h = max(int((count / max_val) * 40), 4)
            spacer = ctk.CTkFrame(bar_col, fg_color="transparent")
            spacer.pack(side="top", fill="x", expand=True)
            ctk.CTkFrame(bar_col, fg_color=bar_colors.get(s_name, "gray"),
                         height=bar_h, corner_radius=3).pack(fill="x", side="bottom")

        # Legend with counts below bars
        legend_f = ctk.CTkFrame(sc, fg_color="transparent")
        legend_f.pack(fill="x", pady=(6, 0))
        for s_name, color in bar_colors.items():
            count = status_counts[s_name]
            lf = ctk.CTkFrame(legend_f, fg_color="transparent")
            lf.pack(side="left", expand=True)
            ctk.CTkLabel(lf, text="●", text_color=color,
                         font=ctk.CTkFont(size=9)).pack(side="left")
            ctk.CTkLabel(lf, text=f" {s_name} ({count})",
                         font=ctk.CTkFont(size=10),
                         text_color=("gray45", "gray60")).pack(side="left")

        # ═══ Activity Cards (right) ═══
        activity_card = ctk.CTkFrame(
            row1, corner_radius=14,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        activity_card.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=(0, 12))

        ac = ctk.CTkFrame(activity_card, fg_color="transparent")
        ac.pack(fill="both", expand=True, padx=20, pady=18)

        ac_hdr = ctk.CTkFrame(ac, fg_color="transparent")
        ac_hdr.pack(fill="x")
        ctk.CTkLabel(ac_hdr, text="Aktivitas",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkLabel(ac_hdr, text="Detail laporan Anda.",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(side="right")

        # 3 activity mini-cards
        acts_row = ctk.CTkFrame(ac, fg_color="transparent")
        acts_row.pack(fill="x", pady=(14, 0))
        for i in range(3):
            acts_row.grid_columnconfigure(i, weight=1)

        menunggu_cnt = sum(1 for d in data if d["status"] == "Menunggu")
        diproses_cnt = sum(1 for d in data if "Diproses" in d.get("status", ""))
        selesai_cnt = selesai

        act_defs = [
            ("⏳  Menunggu", menunggu_cnt, "#FFA726", ("white", "gray20")),
            ("🔄  Diproses", diproses_cnt, SKY_BLUE, ("white", "gray20")),
            ("✅  Selesai", selesai_cnt, "#66BB6A", (NAVY, NAVY)),
        ]
        for i, (alabel, aval, acolor, abg) in enumerate(act_defs):
            acard = ctk.CTkFrame(acts_row, corner_radius=12,
                                  fg_color=abg,
                                  border_width=1, border_color=("gray85", "gray28"))
            acard.grid(row=0, column=i, sticky="nsew", padx=4)

            ai = ctk.CTkFrame(acard, fg_color="transparent")
            ai.pack(fill="x", padx=16, pady=16)

            # Text color: white for dark bg (last card), dark for others
            txt_clr = ("white", "white") if abg == (NAVY, NAVY) else ("gray30", "gray80")
            sub_clr = ("gray85", "gray85") if abg == (NAVY, NAVY) else ("gray50", "gray60")

            ctk.CTkLabel(ai, text=alabel,
                         font=ctk.CTkFont(size=12),
                         text_color=sub_clr).pack(anchor="w")
            ctk.CTkLabel(ai, text=f"{aval}",
                         font=ctk.CTkFont(size=32, weight="bold"),
                         text_color=txt_clr).pack(anchor="w", pady=(4, 0))

            # Color accent line
            ctk.CTkFrame(ai, height=3, fg_color=acolor,
                         corner_radius=2).pack(fill="x", pady=(8, 0))

        # ── Small stat cards row ──
        row2 = ctk.CTkFrame(c, fg_color="transparent")
        row2.pack(fill="x", padx=30, pady=(0, 12))
        row2.grid_columnconfigure(0, weight=1)
        row2.grid_columnconfigure(1, weight=1)

        ditolak_cnt = sum(1 for d in data if d["status"] == "Ditolak")
        persen_selesai = f"{(selesai_cnt / total * 100):.0f}%" if total > 0 else "0%"

        small_defs = [
            ("❌  Ditolak", str(ditolak_cnt), "#EF5350"),
            ("📊  Tingkat Selesai", persen_selesai, "#66BB6A"),
        ]
        for i, (slabel, sval, scolor) in enumerate(small_defs):
            scard = ctk.CTkFrame(row2, corner_radius=12,
                                  fg_color=("white", "gray17"),
                                  border_width=1, border_color=("gray88", "gray28"))
            scard.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 5, 5 if i == 0 else 0))
            si = ctk.CTkFrame(scard, fg_color="transparent")
            si.pack(fill="x", padx=18, pady=14)
            ctk.CTkLabel(si, text=slabel, font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(anchor="w")
            ctk.CTkLabel(si, text=sval,
                         font=ctk.CTkFont(size=26, weight="bold"),
                         text_color=scolor).pack(anchor="w", pady=(2, 0))

        # ── Transactions History (Riwayat Laporan) ──
        hist_card = ctk.CTkFrame(
            c, corner_radius=14,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        hist_card.pack(fill="x", padx=30, pady=(0, 20))

        hi = ctk.CTkFrame(hist_card, fg_color="transparent")
        hi.pack(fill="x", padx=24, pady=20)

        hi_hdr = ctk.CTkFrame(hi, fg_color="transparent")
        hi_hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hi_hdr, text="Riwayat Laporan",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        ctk.CTkLabel(hi, text="Daftar laporan terbaru Anda.",
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w", pady=(0, 12))

        # Table header
        ht = ctk.CTkFrame(hi, fg_color=("gray94", "gray20"),
                          corner_radius=6, height=36)
        ht.pack(fill="x")
        ht.pack_propagate(False)

        hist_cols = [
            ("Judul", 220), ("No. Laporan", 110),
            ("Status", 150), ("Tanggal", 130), ("Kategori", 150),
        ]
        for col_label, w in hist_cols:
            ctk.CTkLabel(
                ht, text=col_label, width=w,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray45", "gray65"), anchor="w"
            ).pack(side="left", padx=(14, 0), pady=8)

        # Table rows
        recent = self.all_laporan[:10]
        if not recent:
            ctk.CTkLabel(
                hi, text="Belum ada laporan.",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60")
            ).pack(pady=20)
        else:
            for idx, lap in enumerate(recent):
                row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
                rr = ctk.CTkFrame(hi, fg_color=row_bg, height=44,
                                  corner_radius=4)
                rr.pack(fill="x", pady=1)
                rr.pack_propagate(False)

                # Judul
                c0 = ctk.CTkFrame(rr, fg_color="transparent", width=220, height=44)
                c0.pack(side="left", padx=(14, 0))
                c0.pack_propagate(False)
                ctk.CTkLabel(
                    c0, text=truncate_text(lap.get("judul", ""), 28),
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w"
                ).pack(side="left", pady=8)

                # No. Laporan
                c1 = ctk.CTkFrame(rr, fg_color="transparent", width=110, height=44)
                c1.pack(side="left", padx=(14, 0))
                c1.pack_propagate(False)
                ctk.CTkLabel(
                    c1, text=f"#LP{lap['id']:06d}",
                    font=ctk.CTkFont(size=12),
                    text_color=(TEAL, SKY_BLUE), anchor="w"
                ).pack(side="left", pady=8)

                # Status with dot
                c2 = ctk.CTkFrame(rr, fg_color="transparent", width=150, height=44)
                c2.pack(side="left", padx=(14, 0))
                c2.pack_propagate(False)
                st_color = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
                ctk.CTkLabel(
                    c2, text=f"●  {lap['status']}",
                    font=ctk.CTkFont(size=11),
                    text_color=st_color, anchor="w"
                ).pack(side="left", pady=8)

                # Tanggal
                c3 = ctk.CTkFrame(rr, fg_color="transparent", width=130, height=44)
                c3.pack(side="left", padx=(14, 0))
                c3.pack_propagate(False)
                ctk.CTkLabel(
                    c3, text=format_tanggal(lap.get("created_at")),
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray60"), anchor="w"
                ).pack(side="left", pady=8)

                # Kategori
                c4 = ctk.CTkFrame(rr, fg_color="transparent", width=150, height=44)
                c4.pack(side="left", padx=(14, 0))
                c4.pack_propagate(False)
                ctk.CTkLabel(
                    c4, text=truncate_text(lap.get("kategori", ""), 20),
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                ).pack(side="left", pady=8)

                # Click → detail page
                def _bind_click(widget, data=lap):
                    widget.bind("<Button-1>", lambda e: self._show_detail_page(data))
                    if hasattr(widget, "winfo_children"):
                        for child in widget.winfo_children():
                            _bind_click(child, data)
                _bind_click(rr)

                # Hover
                rr.bind("<Enter>", lambda e, r=rr: r.configure(fg_color=("gray92", "gray22")))
                rr.bind("<Leave>", lambda e, r=rr, b=row_bg: r.configure(fg_color=b))

                # Separator
                ctk.CTkFrame(hi, height=1, fg_color=("gray92", "gray25")).pack(fill="x")

    # ══════════════════════════════════════════
    # PAGE 1B : RIWAYAT LAPORAN
    # ══════════════════════════════════════════

    def _show_riwayat_page(self):
        """Halaman khusus riwayat laporan dengan filter."""
        self._clear_content()
        self._load_data()
        c = self.content
        data = self.all_laporan

        # ── Header ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 20))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(
            left, text="📋  Riwayat Laporan",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Semua laporan yang pernah Anda buat.",
            font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 0))

        # ── Filter Bar ──
        filter_bar = ctk.CTkFrame(c, corner_radius=10,
                                   fg_color=("white", "gray17"),
                                   border_width=1, border_color=("gray88", "gray28"))
        filter_bar.pack(fill="x", padx=30, pady=(0, 15))

        fi = ctk.CTkFrame(filter_bar, fg_color="transparent")
        fi.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(fi, text="Status:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        self.riwayat_filter_var = ctk.StringVar(value="Semua")
        ctk.CTkComboBox(
            fi, values=["Semua", "Menunggu", "Diproses", "Selesai", "Ditolak"],
            variable=self.riwayat_filter_var,
            width=150, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._filter_riwayat(), state="readonly"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            fi, text="Reset", width=60, height=32, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._reset_riwayat_filter
        ).pack(side="left")

        # ── Table ──
        self._riwayat_data = data
        self._riwayat_container = ctk.CTkFrame(c, fg_color="transparent")
        self._riwayat_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self._render_riwayat_table(data)

    def _filter_riwayat(self):
        status = self.riwayat_filter_var.get()
        data = self.all_laporan
        if status == "Diproses":
            data = [d for d in data if "Diproses" in d.get("status", "")]
        elif status != "Semua":
            data = [d for d in data if d["status"] == status]
        self._render_riwayat_table(data)

    def _reset_riwayat_filter(self):
        self.riwayat_filter_var.set("Semua")
        self._render_riwayat_table(self.all_laporan)

    def _render_riwayat_table(self, data):
        """Render riwayat laporan table."""
        container = self._riwayat_container
        for w in container.winfo_children():
            w.destroy()

        table_card = ctk.CTkFrame(container, corner_radius=14,
                                   fg_color=("white", "gray17"),
                                   border_width=1, border_color=("gray88", "gray28"))
        table_card.pack(fill="both", expand=True)

        hi = ctk.CTkFrame(table_card, fg_color="transparent")
        hi.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(hi, text=f"{len(data)} laporan ditemukan",
                     font=ctk.CTkFont(size=12),
                     text_color=("gray50", "gray60")).pack(anchor="w", pady=(0, 10))

        # Table header
        ht = ctk.CTkFrame(hi, fg_color=("gray94", "gray20"),
                          corner_radius=6, height=36)
        ht.pack(fill="x")
        ht.pack_propagate(False)

        hist_cols = [
            ("Judul", 220), ("No. Laporan", 110),
            ("Status", 150), ("Tanggal", 130), ("Kategori", 150),
        ]
        for col_label, w in hist_cols:
            ctk.CTkLabel(
                ht, text=col_label, width=w,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray45", "gray65"), anchor="w"
            ).pack(side="left", padx=(14, 0), pady=8)

        # Scrollable rows
        scroll = ctk.CTkScrollableFrame(hi, fg_color="transparent", height=400)
        scroll.pack(fill="both", expand=True, pady=(4, 0))

        if not data:
            ctk.CTkLabel(
                scroll, text="Tidak ada laporan.",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60")
            ).pack(pady=30)
            return

        for idx, lap in enumerate(data):
            row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
            rr = ctk.CTkFrame(scroll, fg_color=row_bg, height=44, corner_radius=4)
            rr.pack(fill="x", pady=1)
            rr.pack_propagate(False)

            c0 = ctk.CTkFrame(rr, fg_color="transparent", width=220, height=44)
            c0.pack(side="left", padx=(14, 0))
            c0.pack_propagate(False)
            ctk.CTkLabel(
                c0, text=truncate_text(lap.get("judul", ""), 28),
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
            ).pack(side="left", pady=8)

            c1 = ctk.CTkFrame(rr, fg_color="transparent", width=110, height=44)
            c1.pack(side="left", padx=(14, 0))
            c1.pack_propagate(False)
            ctk.CTkLabel(
                c1, text=f"#LP{lap['id']:06d}",
                font=ctk.CTkFont(size=12),
                text_color=(TEAL, SKY_BLUE), anchor="w"
            ).pack(side="left", pady=8)

            c2 = ctk.CTkFrame(rr, fg_color="transparent", width=150, height=44)
            c2.pack(side="left", padx=(14, 0))
            c2.pack_propagate(False)
            st_color = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
            ctk.CTkLabel(
                c2, text=f"●  {lap['status']}",
                font=ctk.CTkFont(size=11),
                text_color=st_color, anchor="w"
            ).pack(side="left", pady=8)

            c3 = ctk.CTkFrame(rr, fg_color="transparent", width=130, height=44)
            c3.pack(side="left", padx=(14, 0))
            c3.pack_propagate(False)
            ctk.CTkLabel(
                c3, text=format_tanggal(lap.get("created_at")),
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60"), anchor="w"
            ).pack(side="left", pady=8)

            c4 = ctk.CTkFrame(rr, fg_color="transparent", width=150, height=44)
            c4.pack(side="left", padx=(14, 0))
            c4.pack_propagate(False)
            ctk.CTkLabel(
                c4, text=truncate_text(lap.get("kategori", ""), 20),
                font=ctk.CTkFont(size=11), anchor="w"
            ).pack(side="left", pady=8)

            def _bind_click(widget, d=lap):
                widget.bind("<Button-1>", lambda e: self._show_detail_page(d))
                if hasattr(widget, "winfo_children"):
                    for child in widget.winfo_children():
                        _bind_click(child, d)
            _bind_click(rr)

            rr.bind("<Enter>", lambda e, r=rr: r.configure(fg_color=("gray92", "gray22")))
            rr.bind("<Leave>", lambda e, r=rr, b=row_bg: r.configure(fg_color=b))

            ctk.CTkFrame(scroll, height=1, fg_color=("gray92", "gray25")).pack(fill="x")

    # ══════════════════════════════════════════
    # PAGE 2 : BUAT LAPORAN (Support Ticket-style)
    # ══════════════════════════════════════════

    def _show_form_page(self):
        self._clear_content()
        self._load_data()
        c = self.content

        # ── Header ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 20))

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left")
        ctk.CTkLabel(
            left_hdr, text="Buat Laporan",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            left_hdr, text="Sampaikan keluhan atau aspirasi Anda kepada pemerintah.",
            font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 0))

        # ── Form Card ──
        form_card = ctk.CTkFrame(
            c, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        form_card.pack(fill="x", padx=30, pady=(0, 20))

        fi = ctk.CTkFrame(form_card, fg_color="transparent")
        fi.pack(fill="x", padx=28, pady=24)

        ctk.CTkLabel(
            fi, text="Buat Laporan Baru",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            fi, text="Isi semua informasi di bawah, lalu klik tombol kirim.",
            font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 18))

        # ── Row 1: Judul + Kategori ──
        row1 = ctk.CTkFrame(fi, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)

        # Judul
        f_judul = ctk.CTkFrame(row1, fg_color="transparent")
        f_judul.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(f_judul, text="Judul Laporan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_judul = ctk.CTkEntry(
            f_judul, height=34, corner_radius=8,
            placeholder_text="Judul Laporan (Ringkasan masalah)",
            font=ctk.CTkFont(size=13)
        )
        self.form_judul.pack(fill="x", pady=(3, 0))

        # Kategori
        f_kat = ctk.CTkFrame(row1, fg_color="transparent")
        f_kat.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(f_kat, text="Kategori *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kategori = ctk.CTkComboBox(
            f_kat, values=KATEGORI_LAPORAN,
            height=34, corner_radius=8, font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.form_kategori.pack(fill="x", pady=(3, 0))
        self.form_kategori.set("Pilih Kategori")

        # ── Row 2: Kecamatan + Kelurahan ──
        row2 = ctk.CTkFrame(fi, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 12))
        row2.grid_columnconfigure(0, weight=1)
        row2.grid_columnconfigure(1, weight=1)

        # Kecamatan
        f_kec = ctk.CTkFrame(row2, fg_color="transparent")
        f_kec.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(f_kec, text="Kecamatan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kecamatan = ctk.CTkComboBox(
            f_kec, values=get_semua_kecamatan(),
            height=34, corner_radius=8, font=ctk.CTkFont(size=13),
            command=self._on_kecamatan_changed, state="readonly"
        )
        self.form_kecamatan.pack(fill="x", pady=(3, 0))
        self.form_kecamatan.set("Pilih Kecamatan")

        # Kelurahan
        f_kel = ctk.CTkFrame(row2, fg_color="transparent")
        f_kel.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(f_kel, text="Kelurahan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kelurahan = ctk.CTkComboBox(
            f_kel, values=["Pilih kecamatan dahulu"],
            height=34, corner_radius=8, font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.form_kelurahan.pack(fill="x", pady=(3, 0))
        self.form_kelurahan.set("Pilih kecamatan dahulu")

        # ── Row 3: Lokasi Spesifik (full width) ──
        row3 = ctk.CTkFrame(fi, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(row3, text="Lokasi Spesifik *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_lokasi = ctk.CTkEntry(
            row3, height=34, corner_radius=8,
            placeholder_text="Contoh: Jl. Sam Ratulangi No. 12",
            font=ctk.CTkFont(size=13)
        )
        self.form_lokasi.pack(fill="x", pady=(3, 0))

        # ── Row 4: Deskripsi Detail (full width, below Lokasi) ──
        row4 = ctk.CTkFrame(fi, fg_color="transparent")
        row4.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(row4, text="Deskripsi Detail *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_deskripsi = ctk.CTkTextbox(
            row4, height=80, corner_radius=8,
            font=ctk.CTkFont(size=13),
            border_width=1, border_color=("gray72", "gray35")
        )
        self.form_deskripsi.pack(fill="x", pady=(3, 0))

        # ── Row 5: Lampiran Foto (Opsional) ──
        row5 = ctk.CTkFrame(fi, fg_color="transparent")
        row5.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(row5, text="Lampiran Foto (Opsional)", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        
        f_foto = ctk.CTkFrame(row5, fg_color="transparent")
        f_foto.pack(fill="x", pady=(3, 0))
        
        self.form_foto_path = None
        self.lbl_foto_name = ctk.CTkLabel(
            f_foto, text="Tidak ada file yang dipilih",
            font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")
        )
        
        ctk.CTkButton(
            f_foto, text="Pilih Foto", height=30, width=100, corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray85", "gray25"), text_color=("gray20", "gray85"),
            hover_color=("gray75", "gray35"),
            command=self._pilih_foto_laporan
        ).pack(side="left", padx=(0, 10))
        self.lbl_foto_name.pack(side="left")

        # ── Anonymous Option ──
        ctk.CTkFrame(fi, height=1, fg_color=("gray85", "gray28")).pack(
            fill="x", pady=(4, 14))

        self.form_anon_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            fi, text="🔒  Sembunyikan identitas saya (Laporan Anonim)",
            variable=self.form_anon_var,
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70"),
            checkbox_width=20, checkbox_height=20, corner_radius=4,
        ).pack(anchor="w", pady=(0, 14))

        # ── Submit Button ──
        self.submit_btn = ctk.CTkButton(
            fi, text="📤  Kirim Laporan",
            height=40, corner_radius=8, width=180,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=(TEAL, TEAL),
            hover_color=(NAVY, NAVY),
            command=self._submit_form
        )
        self.submit_btn.pack(anchor="e", pady=(2, 0))

        # ── Riwayat Laporan Terbaru + FAQ ──
        bottom_row = ctk.CTkFrame(c, fg_color="transparent")
        bottom_row.pack(fill="x", padx=30, pady=(0, 20))
        bottom_row.grid_columnconfigure(0, weight=1)

        # ── Left: Latest Support History ──
        hist_card = ctk.CTkFrame(
            bottom_row, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        hist_card.grid(row=0, column=0, sticky="nsew")

        hf = ctk.CTkFrame(hist_card, fg_color="transparent")
        hf.pack(fill="x", padx=22, pady=18)

        hf_hdr = ctk.CTkFrame(hf, fg_color="transparent")
        hf_hdr.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(hf_hdr, text="Riwayat Laporan Terbaru",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        recent = self.all_laporan[:5]
        if not recent:
            ctk.CTkLabel(hf, text="Belum ada laporan.",
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(pady=15)
        else:
            for lap in recent:
                rr = ctk.CTkFrame(hf, fg_color="transparent")
                rr.pack(fill="x", pady=4)

                ctk.CTkLabel(
                    rr, text=f"LP#{lap['id']:06d}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=(TEAL, SKY_BLUE), width=110, anchor="w"
                ).pack(side="left")
                ctk.CTkLabel(
                    rr, text=truncate_text(lap.get("kategori", ""), 18),
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray60"), width=130, anchor="w"
                ).pack(side="left")
                ctk.CTkLabel(
                    rr, text=format_tanggal(lap.get("created_at")),
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray60"), width=120, anchor="w"
                ).pack(side="left")

                st_color = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
                ctk.CTkLabel(
                    rr, text=lap["status"],
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=st_color, anchor="w"
                ).pack(side="left")

                ctk.CTkFrame(hf, height=1, fg_color=("gray92", "gray25")).pack(fill="x")


    # ── Form helpers ──
    def _pilih_foto_laporan(self):
        import tkinter.filedialog as fd
        import os
        filepath = fd.askopenfilename(
            title="Pilih Lampiran Foto",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if filepath:
            self.form_foto_path = filepath
            filename = os.path.basename(filepath)
            from utils.helpers import truncate_text
            self.lbl_foto_name.configure(text=truncate_text(filename, 30), text_color=("black", "white"))

    def _on_kecamatan_changed(self, kec: str):
        kel_list = get_kelurahan_by_kecamatan(kec)
        if kel_list:
            self.form_kelurahan.configure(values=kel_list)
            self.form_kelurahan.set(kel_list[0])
        else:
            self.form_kelurahan.configure(values=["Tidak ada data"])
            self.form_kelurahan.set("Tidak ada data")

    def _submit_form(self):
        from tkinter import messagebox

        kategori = self.form_kategori.get()
        if kategori.startswith("Pilih"):
            kategori = ""

        kelurahan = self.form_kelurahan.get()
        if kelurahan.startswith("Pilih") or kelurahan == "Tidak ada data":
            kelurahan = ""

        result = self.laporan_ctrl.buat_laporan(
            user_id=self.app.current_user["id"],
            judul=self.form_judul.get(),
            kategori=kategori,
            deskripsi=self.form_deskripsi.get("1.0", "end-1c"),
            lokasi=self.form_lokasi.get(),
            kelurahan=kelurahan,
            is_anonymous=self.form_anon_var.get(),
            foto_laporan_path=self.form_foto_path
        )

        if result["success"]:
            messagebox.showinfo("Berhasil", result["message"])
            self._load_data()
            self._show_dashboard_page()
        else:
            messagebox.showerror("Gagal", result["message"])

    # ══════════════════════════════════════════
    # PAGE 3 : DETAIL LAPORAN (Invoice-detail style)
    # ══════════════════════════════════════════

    def _show_detail_page(self, laporan: dict):
        """Halaman detail laporan — invoice style."""
        from views.components.detail_invoice import build_detail_header, build_detail_card
        self._clear_content()
        c = self.content
        self.selected_laporan = laporan

        # ── Invoice-style Header ──
        build_detail_header(
            c, laporan, back_command=self._show_dashboard_page,
            title="Detail Laporan",
            breadcrumb="Dashboard  ›  Detail Laporan"
        )

        # ── Invoice-style Main Card ──
        build_detail_card(c, laporan)

        # ── Timeline ──
        tl_card = ctk.CTkFrame(
            c, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        tl_card.pack(fill="x", padx=30, pady=(0, 20))

        tc = ctk.CTkFrame(tl_card, fg_color="transparent")
        tc.pack(fill="x", padx=28, pady=20)

        ctk.CTkLabel(tc, text="📌  Timeline Status",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=(NAVY, SKY_BLUE), anchor="w").pack(fill="x", pady=(0, 12))

        riwayat = self.laporan_ctrl.get_riwayat_laporan(laporan["id"])
        if not riwayat:
            ctk.CTkLabel(tc, text="Belum ada riwayat perubahan status.",
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(pady=10)
        else:
            tl_f = ctk.CTkFrame(tc, fg_color="transparent")
            tl_f.pack(fill="x")

            pastel_bg = [
                ("#EEF2FF", "#2B2B2B"),
                ("#F3ECFF", "#2B2B2B"),
                ("#F1F7EE", "#2B2B2B"),
                ("#FFF2E2", "#2B2B2B"),
            ]

            for j, rw in enumerate(riwayat):
                tanggal = format_tanggal(rw.get("created_at"))
                if ", " in tanggal:
                    date_part, time_part = tanggal.split(", ", 1)
                else:
                    date_part, time_part = tanggal, ""

                card = ctk.CTkFrame(
                    tl_f, corner_radius=12,
                    fg_color=("white", "gray17"),
                    border_width=1, border_color=("gray88", "gray28")
                )
                card.pack(fill="x", pady=(0, 10))

                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=12)

                pill_bg = pastel_bg[j % len(pastel_bg)]
                time_card = ctk.CTkFrame(
                    row, width=120, corner_radius=10,
                    fg_color=pill_bg, border_width=0
                )
                time_card.pack(side="left")
                time_card.pack_propagate(False)

                ctk.CTkLabel(
                    time_card, text=date_part,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=(NAVY, SKY_BLUE)
                ).pack(pady=(8, 0))
                ctk.CTkLabel(
                    time_card, text=time_part,
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=(NAVY, SKY_BLUE)
                ).pack(pady=(2, 8))

                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=(14, 0))

                st_text = rw.get("status_baru", "")
                ctk.CTkLabel(
                    info, text=st_text,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    anchor="w"
                ).pack(fill="x")

                catatan = rw.get("catatan_admin", "")
                admin_name = rw.get("nama_admin", "Sistem")
                sub_text = f"oleh {admin_name}: {catatan}" if catatan else ""
                if sub_text:
                    ctk.CTkLabel(
                        info, text=sub_text,
                        font=ctk.CTkFont(size=11),
                        text_color=("gray45", "gray62"),
                        anchor="w", wraplength=520
                    ).pack(fill="x", pady=(2, 0))

                ctk.CTkLabel(
                    row, text="+",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=("gray60", "gray50")
                ).pack(side="right")

    # ══════════════════════════════════════════
    # PAGE 4 : ASPIRASI SEKITAR (Upvote / Dukungan)
    # ══════════════════════════════════════════

    def _show_aspirasi_page(self):
        """Halaman publik: lihat laporan warga lain di kelurahan & beri dukungan."""
        self._clear_content()
        c = self.content

        # ── Header ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 20))

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left")
        ctk.CTkLabel(
            left_hdr, text="🏘️  Aspirasi Sekitar",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")

        # Determine user's kelurahan — try to get from user data
        user = self.app.current_user
        user_kel = user.get("kelurahan", "")
        
        if not user_kel:
            # If no kelurahan set, show info
            ctk.CTkLabel(
                left_hdr,
                text="Lihat dan dukung laporan warga lain di wilayah Anda.",
                font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")
            ).pack(anchor="w", pady=(2, 0))
        else:
            ctk.CTkLabel(
                left_hdr,
                text=f"Laporan aktif di Kelurahan {user_kel} — dukung yang paling mendesak!",
                font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")
            ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            header, text="🔄  Refresh", height=34, corner_radius=8, width=100,
            font=ctk.CTkFont(size=12), fg_color="transparent",
            border_width=1, border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._show_aspirasi_page
        ).pack(side="right")

        # ── Kelurahan Selector (if user has no fixed kelurahan) ──
        if not user_kel:
            sel_f = ctk.CTkFrame(c, fg_color="transparent")
            sel_f.pack(fill="x", padx=30, pady=(0, 10))
            ctk.CTkLabel(sel_f, text="Pilih Kelurahan:",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
            
            from config.wilayah import get_semua_kelurahan
            all_kel = get_semua_kelurahan() if hasattr(__import__('config.wilayah', fromlist=['get_semua_kelurahan']), 'get_semua_kelurahan') else []
            
            # Fallback: use kecamatan combo
            kec_list = get_semua_kecamatan()
            self._asp_kec_var = ctk.StringVar(value=kec_list[0] if kec_list else "")
            ctk.CTkComboBox(
                sel_f, values=kec_list, variable=self._asp_kec_var,
                width=160, height=32, corner_radius=8,
                font=ctk.CTkFont(size=12), state="readonly",
                command=self._on_asp_kecamatan_changed
            ).pack(side="left", padx=(0, 10))

            kel_list = get_kelurahan_by_kecamatan(kec_list[0]) if kec_list else []
            self._asp_kel_var = ctk.StringVar(value=kel_list[0] if kel_list else "")
            self._asp_kel_combo = ctk.CTkComboBox(
                sel_f, values=kel_list, variable=self._asp_kel_var,
                width=160, height=32, corner_radius=8,
                font=ctk.CTkFont(size=12), state="readonly",
                command=lambda _: self._render_aspirasi_cards()
            )
            self._asp_kel_combo.pack(side="left", padx=(0, 10))

            user_kel = self._asp_kel_var.get()

        # ── Cards container ──
        self._aspirasi_container = ctk.CTkFrame(c, fg_color="transparent")
        self._aspirasi_container.pack(fill="x", padx=30, pady=(0, 20))

        self._asp_kelurahan = user_kel
        self._render_aspirasi_cards()

    def _on_asp_kecamatan_changed(self, kec: str):
        kel_list = get_kelurahan_by_kecamatan(kec)
        if kel_list:
            self._asp_kel_combo.configure(values=kel_list)
            self._asp_kel_combo.set(kel_list[0])
            self._asp_kel_var.set(kel_list[0])
        self._render_aspirasi_cards()

    def _render_aspirasi_cards(self):
        """Render kartu-kartu laporan publik dengan tombol dukungan."""
        container = self._aspirasi_container
        for w in container.winfo_children():
            w.destroy()

        # Determine kelurahan
        kel = getattr(self, '_asp_kel_var', None)
        if kel:
            kelurahan = kel.get()
        else:
            kelurahan = self._asp_kelurahan

        if not kelurahan:
            ctk.CTkLabel(
                container, text="Pilih kelurahan untuk melihat aspirasi warga.",
                font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")
            ).pack(pady=30)
            return

        user_id = self.app.current_user["id"]
        data = self.laporan_ctrl.get_laporan_publik(kelurahan)

        if not data:
            empty_card = ctk.CTkFrame(container, corner_radius=12,
                                       fg_color=("white", "gray17"),
                                       border_width=1, border_color=("gray88", "gray28"))
            empty_card.pack(fill="x", pady=5)
            ctk.CTkLabel(
                empty_card, text="🎉  Tidak ada laporan aktif di kelurahan ini saat ini.",
                font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")
            ).pack(pady=30)
            return

        for lap in data:
            card = ctk.CTkFrame(
                container, corner_radius=12,
                fg_color=("white", "gray17"),
                border_width=1, border_color=("gray88", "gray28")
            )
            card.pack(fill="x", pady=5)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=20, pady=16)

            # Top row: title + badges
            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x")

            ctk.CTkLabel(
                top, text=truncate_text(lap.get("judul", ""), 50),
                font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
            ).pack(side="left")

            # Priority badge
            pri = lap.get("prioritas", "Rendah")
            pri_color = PRIORITAS_COLORS.get(pri, "#66BB6A")
            pri_f = ctk.CTkFrame(top, fg_color=pri_color, corner_radius=5)
            pri_f.pack(side="right", padx=(6, 0))
            ctk.CTkLabel(pri_f, text=f"⚡{pri}",
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color="white").pack(padx=6, pady=2)

            # Status badge
            st_color = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
            st_f = ctk.CTkFrame(top, fg_color=st_color, corner_radius=5)
            st_f.pack(side="right")
            ctk.CTkLabel(st_f, text=lap["status"],
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color="white").pack(padx=6, pady=2)

            # Description snippet
            desc = truncate_text(lap.get("deskripsi", ""), 120)
            ctk.CTkLabel(
                inner, text=desc,
                font=ctk.CTkFont(size=12), text_color=("gray45", "gray65"),
                anchor="w", wraplength=650
            ).pack(fill="x", pady=(6, 0))

            # Bottom row: metadata + support button
            bot = ctk.CTkFrame(inner, fg_color="transparent")
            bot.pack(fill="x", pady=(10, 0))

            meta_items = [
                f"📁 {lap.get('kategori', '')}",
                f"📍 {truncate_text(lap.get('lokasi', ''), 30)}",
                f"👤 {lap.get('nama_pelapor', 'Anonim')}",
                f"📅 {format_tanggal(lap.get('created_at'))}",
            ]
            for m in meta_items:
                ctk.CTkLabel(
                    bot, text=m, font=ctk.CTkFont(size=10),
                    text_color=("gray50", "gray60")
                ).pack(side="left", padx=(0, 14))

            # Support / upvote button
            dukungan_info = self.laporan_ctrl.get_dukungan_status(lap["id"], user_id)
            is_supported = dukungan_info["supported"]
            count = lap.get("jumlah_dukungan", dukungan_info["count"])

            # Is this the user's own report?
            is_own = (lap.get("user_id") == user_id)

            btn_text = f"✅ Didukung ({count})" if is_supported else f"👍 Dukung ({count})"
            btn_fg = (TEAL, TEAL) if is_supported else ("transparent", "transparent")
            btn_text_clr = "white" if is_supported else (TEAL, SKY_BLUE)
            btn_border = (TEAL, TEAL)

            if is_own:
                # Can't upvote own report
                btn_text = f"📋 Laporan Anda ({count})"
                support_btn = ctk.CTkButton(
                    bot, text=btn_text, height=30, corner_radius=8,
                    font=ctk.CTkFont(size=11),
                    fg_color=("gray90", "gray25"),
                    text_color=("gray50", "gray60"),
                    state="disabled", width=150
                )
            else:
                support_btn = ctk.CTkButton(
                    bot, text=btn_text, height=30, corner_radius=8,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=btn_fg, text_color=btn_text_clr,
                    border_width=1, border_color=btn_border,
                    hover_color=(NAVY, NAVY), width=150,
                    command=lambda lid=lap["id"]: self._do_toggle_dukungan(lid)
                )

            support_btn.pack(side="right")

    def _do_toggle_dukungan(self, laporan_id: int):
        """Toggle dukungan dan refresh kartu."""
        user_id = self.app.current_user["id"]
        self.laporan_ctrl.toggle_dukungan(laporan_id, user_id)
        self._render_aspirasi_cards()

