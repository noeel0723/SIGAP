# views/warga/dashboard_warga.py
# Dashboard Warga — InvestIQ-style dashboard + Support Ticket-style form

import customtkinter as ctk
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.settings import KATEGORI_LAPORAN, STATUS_LAPORAN
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
            {"icon": "🔄", "label": "Refresh", "command": self._refresh},
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
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        ctk.CTkLabel(ts, text=f"{total}",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w")

        # Selesai stat
        ss = ctk.CTkFrame(stats_row, fg_color="transparent")
        ss.pack(side="left")
        ctk.CTkLabel(ss, text="↑  Selesai",
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        ctk.CTkLabel(ss, text=f"{selesai}",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w")

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

        # Legend below bars
        legend_f = ctk.CTkFrame(sc, fg_color="transparent")
        legend_f.pack(fill="x", pady=(6, 0))
        for s_name, color in bar_colors.items():
            lf = ctk.CTkFrame(legend_f, fg_color="transparent")
            lf.pack(side="left", expand=True)
            ctk.CTkLabel(lf, text="●", text_color=color,
                         font=ctk.CTkFont(size=8)).pack(side="left")
            ctk.CTkLabel(lf, text=f" {s_name}",
                         font=ctk.CTkFont(size=9),
                         text_color=("gray50", "gray60")).pack(side="left")

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
                         font=ctk.CTkFont(size=11),
                         text_color=sub_clr).pack(anchor="w")
            ctk.CTkLabel(ai, text=f"{aval}",
                         font=ctk.CTkFont(size=28, weight="bold"),
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
            ctk.CTkLabel(si, text=slabel, font=ctk.CTkFont(size=11),
                         text_color=("gray50", "gray60")).pack(anchor="w")
            ctk.CTkLabel(si, text=sval,
                         font=ctk.CTkFont(size=22, weight="bold"),
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
                ctk.CTkLabel(
                    rr, text=truncate_text(lap.get("judul", ""), 28),
                    width=220, font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w"
                ).pack(side="left", padx=(14, 0), pady=8)

                # No. Laporan
                ctk.CTkLabel(
                    rr, text=f"#LP{lap['id']:06d}",
                    width=110, font=ctk.CTkFont(size=12),
                    text_color=(TEAL, SKY_BLUE), anchor="w"
                ).pack(side="left", padx=(0, 0), pady=8)

                # Status with dot
                st_color = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
                ctk.CTkLabel(
                    rr, text=f"●  {lap['status']}",
                    width=150, font=ctk.CTkFont(size=11),
                    text_color=st_color, anchor="w"
                ).pack(side="left", padx=(0, 0), pady=8)

                # Tanggal
                ctk.CTkLabel(
                    rr, text=format_tanggal(lap.get("created_at")),
                    width=130, font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray60"), anchor="w"
                ).pack(side="left", padx=(0, 0), pady=8)

                # Kategori
                ctk.CTkLabel(
                    rr, text=truncate_text(lap.get("kategori", ""), 20),
                    width=150, font=ctk.CTkFont(size=11),
                    anchor="w"
                ).pack(side="left", padx=(0, 0), pady=8)

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

        # ── Row 1: 4 columns ──
        row1 = ctk.CTkFrame(fi, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 14))
        for i in range(4):
            row1.grid_columnconfigure(i, weight=1)

        # Kategori
        f1 = ctk.CTkFrame(row1, fg_color="transparent")
        f1.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(f1, text="Kategori *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kategori = ctk.CTkComboBox(
            f1, values=KATEGORI_LAPORAN,
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.form_kategori.pack(fill="x", pady=(3, 0))
        self.form_kategori.set("Pilih Kategori")

        # Judul
        f2 = ctk.CTkFrame(row1, fg_color="transparent")
        f2.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(f2, text="Judul Laporan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_judul = ctk.CTkEntry(
            f2, height=36, corner_radius=8,
            placeholder_text="Ringkasan masalah",
            font=ctk.CTkFont(size=13)
        )
        self.form_judul.pack(fill="x", pady=(3, 0))

        # Kecamatan
        f3 = ctk.CTkFrame(row1, fg_color="transparent")
        f3.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(f3, text="Kecamatan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kecamatan = ctk.CTkComboBox(
            f3, values=get_semua_kecamatan(),
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            command=self._on_kecamatan_changed, state="readonly"
        )
        self.form_kecamatan.pack(fill="x", pady=(3, 0))
        self.form_kecamatan.set("Pilih Kecamatan")

        # Kelurahan
        f4 = ctk.CTkFrame(row1, fg_color="transparent")
        f4.grid(row=0, column=3, sticky="ew")
        ctk.CTkLabel(f4, text="Kelurahan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kelurahan = ctk.CTkComboBox(
            f4, values=["Pilih kecamatan dahulu"],
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.form_kelurahan.pack(fill="x", pady=(3, 0))
        self.form_kelurahan.set("Pilih kecamatan dahulu")

        # ── Row 2: 2 columns ──
        row2 = ctk.CTkFrame(fi, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 14))
        row2.grid_columnconfigure(0, weight=1)
        row2.grid_columnconfigure(1, weight=2)

        # Lokasi
        fl = ctk.CTkFrame(row2, fg_color="transparent")
        fl.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(fl, text="Lokasi Spesifik *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_lokasi = ctk.CTkEntry(
            fl, height=36, corner_radius=8,
            placeholder_text="Contoh: Jl. Sam Ratulangi No. 12",
            font=ctk.CTkFont(size=13)
        )
        self.form_lokasi.pack(fill="x", pady=(3, 0))

        # Deskripsi
        fd = ctk.CTkFrame(row2, fg_color="transparent")
        fd.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(fd, text="Deskripsi Detail *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_deskripsi = ctk.CTkTextbox(
            fd, height=70, corner_radius=8,
            font=ctk.CTkFont(size=13),
            border_width=1, border_color=("gray72", "gray35")
        )
        self.form_deskripsi.pack(fill="x", pady=(3, 0))

        # ── Submit Button ──
        self.submit_btn = ctk.CTkButton(
            fi, text="📤  Kirim Laporan",
            height=40, corner_radius=8, width=180,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=(TEAL, TEAL),
            hover_color=(NAVY, NAVY),
            command=self._submit_form
        )
        self.submit_btn.pack(anchor="w", pady=(4, 0))

        # ── Riwayat Laporan Terbaru + FAQ ──
        bottom_row = ctk.CTkFrame(c, fg_color="transparent")
        bottom_row.pack(fill="x", padx=30, pady=(0, 20))
        bottom_row.grid_columnconfigure(0, weight=3)
        bottom_row.grid_columnconfigure(1, weight=2)

        # ── Left: Latest Support History ──
        hist_card = ctk.CTkFrame(
            bottom_row, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        hist_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

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

        # ── Right: FAQ ──
        faq_card = ctk.CTkFrame(
            bottom_row, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        faq_card.grid(row=0, column=1, sticky="nsew")

        ff = ctk.CTkFrame(faq_card, fg_color="transparent")
        ff.pack(fill="x", padx=22, pady=18)

        ctk.CTkLabel(ff, text="Pertanyaan Umum",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 12))

        faqs = [
            "Bagaimana cara membuat laporan?",
            "Berapa lama laporan diproses?",
            "Bagaimana cara melihat status laporan?",
            "Apa itu eskalasi laporan?",
            "Siapa yang memproses laporan saya?",
        ]
        for faq in faqs:
            fq_row = ctk.CTkFrame(ff, fg_color="transparent")
            fq_row.pack(fill="x", pady=3)
            ctk.CTkLabel(fq_row, text=faq,
                         font=ctk.CTkFont(size=11),
                         text_color=("gray30", "gray75"),
                         anchor="w").pack(side="left", fill="x")
            ctk.CTkLabel(fq_row, text="›",
                         font=ctk.CTkFont(size=14),
                         text_color=("gray60", "gray50")).pack(side="right")
            ctk.CTkFrame(ff, height=1, fg_color=("gray92", "gray28")).pack(fill="x")

    # ── Form helpers ──
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
            kelurahan=kelurahan
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
        """Halaman detail laporan terpisah."""
        self._clear_content()
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
            command=self._show_dashboard_page
        ).pack(side="left")

        ctk.CTkLabel(header, text="Laporan",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=(20, 0))
        StatusBadge(header, status=laporan["status"]).pack(side="right")

        # ── Main Card ──
        main_card = ctk.CTkFrame(
            c, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        main_card.pack(fill="x", padx=30, pady=(0, 15))

        mc = ctk.CTkFrame(main_card, fg_color="transparent")
        mc.pack(fill="x", padx=28, pady=24)

        # Two-column info
        info_row = ctk.CTkFrame(mc, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 16))
        info_row.grid_columnconfigure(0, weight=1)
        info_row.grid_columnconfigure(1, weight=1)

        # Left: identitas laporan
        left_info = ctk.CTkFrame(info_row, fg_color="transparent")
        left_info.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        ctk.CTkLabel(left_info, text=f"Laporan #{laporan['id']:06d}",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=(NAVY, SKY_BLUE)).pack(anchor="w")
        ctk.CTkFrame(left_info, height=1, fg_color=("gray88", "gray28")).pack(
            fill="x", pady=(8, 10))

        info_left_items = [
            ("Status", laporan.get("status", "")),
            ("Kategori", laporan.get("kategori", "")),
            ("Pelapor", laporan.get("nama_pelapor",
                                     self.app.current_user.get("nama_lengkap", ""))),
        ]
        for label, value in info_left_items:
            rf = ctk.CTkFrame(left_info, fg_color="transparent")
            rf.pack(fill="x", pady=3)
            ctk.CTkLabel(rf, text=f"{label}:", width=85,
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60"), anchor="w").pack(side="left")
            if label == "Status":
                StatusBadge(rf, status=value).pack(side="left")
            else:
                ctk.CTkLabel(rf, text=value,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             anchor="w").pack(side="left")

        # Right: lokasi & tanggal
        right_info = ctk.CTkFrame(info_row, fg_color="transparent")
        right_info.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right_info, text="📋",
                     font=ctk.CTkFont(size=48),
                     text_color=("gray85", "gray30")).pack(anchor="e", pady=(0, 10))

        info_right_items = [
            ("Dibuat", format_tanggal(laporan.get("created_at"))),
            ("Diperbarui", format_tanggal(laporan.get("updated_at",
                                                        laporan.get("created_at")))),
            ("Lokasi", laporan.get("lokasi", "")),
            ("Wilayah", f"Kel. {laporan.get('kelurahan', '')}, "
                        f"Kec. {laporan.get('kecamatan', '')}"),
        ]
        for label, value in info_right_items:
            rf = ctk.CTkFrame(right_info, fg_color="transparent")
            rf.pack(fill="x", pady=2)
            ctk.CTkLabel(rf, text=f"{label}:", width=100,
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60"), anchor="w").pack(side="left")
            ctk.CTkLabel(rf, text=value, font=ctk.CTkFont(size=12),
                         anchor="w", wraplength=300).pack(side="left")

        # ── Detail table ──
        ctk.CTkFrame(mc, height=1, fg_color=("gray85", "gray28")).pack(
            fill="x", pady=(8, 14))
        ctk.CTkLabel(mc, text="📄  Detail Laporan",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=(NAVY, SKY_BLUE), anchor="w").pack(fill="x", pady=(0, 8))

        tbl_hdr = ctk.CTkFrame(mc, fg_color=(BEIGE, "gray22"),
                                corner_radius=6, height=36)
        tbl_hdr.pack(fill="x")
        tbl_hdr.pack_propagate(False)
        for col_lbl, w in [("FIELD", 150), ("DETAIL", 500)]:
            ctk.CTkLabel(tbl_hdr, text=col_lbl, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=("gray45", "gray65"), anchor="w"
                         ).pack(side="left", padx=(16, 0), pady=8)

        detail_items = [
            ("Judul", laporan.get("judul", "")),
            ("Kategori", laporan.get("kategori", "")),
            ("Lokasi", f"{laporan.get('lokasi', '')} — Kel. {laporan.get('kelurahan', '')}, Kec. {laporan.get('kecamatan', '')}"),
            ("Deskripsi", laporan.get("deskripsi", "")),
        ]
        for idx, (field, value) in enumerate(detail_items):
            row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
            tr = ctk.CTkFrame(mc, fg_color=row_bg, height=42, corner_radius=4)
            tr.pack(fill="x", pady=1)
            tr.pack_propagate(False)
            ctk.CTkLabel(tr, text=field, width=150,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=("gray40", "gray70"), anchor="w"
                         ).pack(side="left", padx=(16, 0), pady=6)
            ctk.CTkLabel(tr, text=value, font=ctk.CTkFont(size=12),
                         anchor="w", wraplength=480
                         ).pack(side="left", padx=(0, 16), pady=6, fill="x")

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
            for j, rw in enumerate(riwayat):
                is_last = j == len(riwayat) - 1
                item = ctk.CTkFrame(tl_f, fg_color="transparent")
                item.pack(fill="x")

                dot_f = ctk.CTkFrame(item, fg_color="transparent", width=30)
                dot_f.pack(side="left", anchor="n")
                dot_f.pack_propagate(False)
                dot_col = TEAL if is_last else ("gray60", "gray50")
                ctk.CTkLabel(dot_f, text="●", text_color=dot_col,
                             font=ctk.CTkFont(size=14)).pack(pady=(3, 0))
                if not is_last:
                    ctk.CTkFrame(dot_f, width=2, height=28,
                                 fg_color=("gray75", "gray38")).pack()

                cf = ctk.CTkFrame(item, fg_color="transparent")
                cf.pack(side="left", fill="x", expand=True, padx=(4, 0))
                ctk.CTkLabel(
                    cf, text=f"{rw.get('status_baru', '')}  •  {format_tanggal(rw.get('created_at'))}",
                    font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
                ).pack(fill="x")
                catatan = rw.get("catatan_admin", "")
                if catatan:
                    ctk.CTkLabel(
                        cf, text=f"oleh {rw.get('nama_admin', 'Sistem')}: {catatan}",
                        font=ctk.CTkFont(size=11),
                        text_color=("gray45", "gray62"),
                        anchor="w", wraplength=550
                    ).pack(fill="x")
