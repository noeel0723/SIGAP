# views/admin_kelurahan/dashboard_kelurahan.py
# Dashboard untuk Admin Kelurahan — with warga-style detail page

import customtkinter as ctk
from tkinter import messagebox
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.settings import PRIORITAS_COLORS

# ── Palette ──
NAVY     = "#2F4156"
TEAL     = "#567C8D"
SKY_BLUE = "#87CEEB"
BEIGE    = "#C8D9E6"

STATUS_DOT_COLORS = {
    "Menunggu": "#FFA726", "Diproses Kelurahan": "#42A5F5",
    "Diproses Kecamatan": "#AB47BC", "Diproses Kota": "#FF7043",
    "Selesai": "#66BB6A", "Ditolak": "#EF5350",
}


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
            {"icon": "🏠", "label": "Dashboard", "command": lambda: self._show_main()},
        ])
        sidebar.grid(row=0, column=0, sticky="nsw")

        # ── Content (scrollable) ──
        self.content = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=("gray78", "gray30")
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        self._show_main()

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()
        self.selected_laporan = None

    # ══════════════════════════════════════════
    # MAIN PAGE
    # ══════════════════════════════════════════

    def _show_main(self):
        self._clear()
        c = self.content
        data = self.laporan_ctrl.get_laporan_kelurahan(self.kelurahan)

        # Header
        ctk.CTkLabel(
            c, text=f"📋  Dashboard Kelurahan {self.kelurahan}",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w"
        ).pack(fill="x", padx=30, pady=(25, 15))

        # ── Summary Cards ──
        cards_frame = ctk.CTkFrame(c, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30, pady=(0, 15))
        for i in range(5):
            cards_frame.grid_columnconfigure(i, weight=1)

        total = len(data)
        menunggu = sum(1 for d in data if d["status"] == "Menunggu")
        diproses = sum(1 for d in data if "Diproses" in d.get("status", ""))
        selesai = sum(1 for d in data if d["status"] == "Selesai")
        ditolak = sum(1 for d in data if d["status"] == "Ditolak")

        card_defs = [
            ("Total", total, TEAL), ("Menunggu", menunggu, "#FFA726"),
            ("Diproses", diproses, SKY_BLUE), ("Selesai", selesai, "#66BB6A"),
            ("Ditolak", ditolak, "#EF5350"),
        ]
        for i, (lbl, val, clr) in enumerate(card_defs):
            card = ctk.CTkFrame(cards_frame, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray85", "gray28"))
            card.grid(row=0, column=i, sticky="ew", padx=4)
            ctk.CTkLabel(card, text=str(val),
                         font=ctk.CTkFont(size=24, weight="bold"),
                         text_color=clr).pack(padx=14, pady=(12, 2))
            ctk.CTkLabel(card, text=lbl, font=ctk.CTkFont(size=10),
                         text_color=("gray50", "gray60")).pack(padx=14, pady=(0, 10))

        # ── Filter ──
        self.filter_var = ctk.StringVar(value="Semua")
        filter_frame = ctk.CTkSegmentedButton(
            c, values=["Semua", "Menunggu", "Diproses Kelurahan", "Selesai", "Ditolak"],
            variable=self.filter_var, command=self._filter,
            font=ctk.CTkFont(size=12), corner_radius=8
        )
        filter_frame.pack(fill="x", padx=30, pady=(0, 10))

        # ── Table ──
        self._data = data
        self._build_table(data)

    def _build_table(self, data):
        """Build laporan table rows."""
        # Remove old table if exists
        if hasattr(self, '_table_frame'):
            self._table_frame.destroy()

        self._table_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self._table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        # Header
        th = ctk.CTkFrame(self._table_frame, fg_color=("gray94", "gray20"),
                          corner_radius=6, height=36)
        th.pack(fill="x")
        th.pack_propagate(False)

        cols = [("#", 40), ("Judul", 160), ("Pelapor", 110),
                ("Kategori", 110), ("Prioritas", 80), ("Status", 130), ("Duk.", 50), ("Tanggal", 110)]
        for lbl, w in cols:
            ctk.CTkLabel(th, text=lbl, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=("gray45", "gray65"), anchor="w"
                         ).pack(side="left", padx=(8, 0), pady=8)

        # Scrollable rows area
        self._table_scroll = ctk.CTkScrollableFrame(
            self._table_frame, fg_color="transparent", height=400,
            scrollbar_button_color=("gray78", "gray30")
        )
        self._table_scroll.pack(fill="both", expand=True, pady=(4, 0))

        if not data:
            ctk.CTkLabel(self._table_scroll, text="Tidak ada laporan.",
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(pady=20)
            return

        for idx, lap in enumerate(data):
            row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
            rr = ctk.CTkFrame(self._table_scroll, fg_color=row_bg,
                              height=40, corner_radius=4)
            rr.pack(fill="x", pady=1)
            rr.pack_propagate(False)

            # Cell exact widths (matches header)
            c0 = ctk.CTkFrame(rr, fg_color="transparent", width=40, height=40)
            c0.pack(side="left", padx=(8, 0))
            c0.pack_propagate(False)
            ctk.CTkLabel(c0, text=f"#{lap['id']}", font=ctk.CTkFont(size=12), text_color=(TEAL, SKY_BLUE), anchor="w").pack(side="left")

            c1 = ctk.CTkFrame(rr, fg_color="transparent", width=160, height=40)
            c1.pack(side="left", padx=(8, 0))
            c1.pack_propagate(False)
            ctk.CTkLabel(c1, text=truncate_text(lap.get("judul", ""), 20), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

            c2 = ctk.CTkFrame(rr, fg_color="transparent", width=110, height=40)
            c2.pack(side="left", padx=(8, 0))
            c2.pack_propagate(False)
            ctk.CTkLabel(c2, text=truncate_text(lap.get("nama_pelapor", ""), 14), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

            c3 = ctk.CTkFrame(rr, fg_color="transparent", width=110, height=40)
            c3.pack(side="left", padx=(8, 0))
            c3.pack_propagate(False)
            ctk.CTkLabel(c3, text=truncate_text(lap.get("kategori", ""), 14), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

            c4 = ctk.CTkFrame(rr, fg_color="transparent", width=80, height=40)
            c4.pack(side="left", padx=(8, 0))
            c4.pack_propagate(False)
            pri = lap.get("prioritas", "Rendah")
            pri_clr = PRIORITAS_COLORS.get(pri, "#66BB6A")
            pri_f = ctk.CTkFrame(c4, fg_color=pri_clr, corner_radius=4)
            pri_f.pack(side="left")
            ctk.CTkLabel(pri_f, text=pri, font=ctk.CTkFont(size=9, weight="bold"), text_color="white").pack(padx=4, pady=2)

            c5 = ctk.CTkFrame(rr, fg_color="transparent", width=130, height=40)
            c5.pack(side="left", padx=(8, 0))
            c5.pack_propagate(False)
            st_clr = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
            ctk.CTkLabel(c5, text=f"● {lap['status']}", font=ctk.CTkFont(size=11), text_color=st_clr, anchor="w").pack(side="left")

            c6 = ctk.CTkFrame(rr, fg_color="transparent", width=50, height=40)
            c6.pack(side="left", padx=(8, 0))
            c6.pack_propagate(False)
            duk = lap.get("jumlah_dukungan", 0)
            ctk.CTkLabel(c6, text=f"👍 {duk}", font=ctk.CTkFont(size=11), text_color=(TEAL, SKY_BLUE), anchor="w").pack(side="left")

            c7 = ctk.CTkFrame(rr, fg_color="transparent", width=110, height=40)
            c7.pack(side="left", padx=(8, 0))
            c7.pack_propagate(False)
            ctk.CTkLabel(c7, text=format_tanggal(lap.get("created_at")), font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"), anchor="w").pack(side="left")

            # Click → detail page
            def _bind(widget, d=lap):
                widget.bind("<Button-1>", lambda e: self._show_detail_page(d))
                if hasattr(widget, "winfo_children"):
                    for ch in widget.winfo_children():
                        _bind(ch, d)
            _bind(rr)
            rr.bind("<Enter>", lambda e, r=rr: r.configure(fg_color=("gray92", "gray22")))
            rr.bind("<Leave>", lambda e, r=rr, b=row_bg: r.configure(fg_color=b))

    def _filter(self, status: str):
        if status == "Semua":
            data = self.laporan_ctrl.get_laporan_kelurahan(self.kelurahan)
        else:
            data = self.laporan_ctrl.get_laporan_kelurahan(self.kelurahan, status)
        self._build_table(data)

    # ══════════════════════════════════════════
    # DETAIL PAGE  (Warga-style)
    # ══════════════════════════════════════════

    def _show_detail_page(self, laporan: dict):
        """Halaman detail laporan terpisah — mirip warga detail."""
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
            command=self._show_main
        ).pack(side="left")

        ctk.CTkLabel(header, text="Laporan",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=(20, 0))

        # Badges: status + prioritas
        badges_f = ctk.CTkFrame(header, fg_color="transparent")
        badges_f.pack(side="right")
        StatusBadge(badges_f, status=laporan["status"]).pack(side="left", padx=(0, 6))
        pri = laporan.get("prioritas", "Rendah")
        pri_color = PRIORITAS_COLORS.get(pri, "#66BB6A")
        pri_badge = ctk.CTkFrame(badges_f, fg_color=pri_color, corner_radius=6)
        pri_badge.pack(side="left")
        ctk.CTkLabel(pri_badge, text=f"⚡ {pri}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="white").pack(padx=10, pady=3)

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
            ("Pelapor", laporan.get("nama_pelapor", "")),
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
            ("Diperbarui", format_tanggal(laporan.get("updated_at", laporan.get("created_at")))),
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

        # ── Action Card ──
        action_card = ctk.CTkFrame(c, corner_radius=12,
                                    fg_color=("white", "gray17"),
                                    border_width=1, border_color=("gray88", "gray28"))
        action_card.pack(fill="x", padx=30, pady=(0, 15))

        af = ctk.CTkFrame(action_card, fg_color="transparent")
        af.pack(fill="x", padx=28, pady=20)

        ctk.CTkLabel(af, text="⚡  Aksi Admin",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=(NAVY, SKY_BLUE), anchor="w").pack(fill="x", pady=(0, 10))

        # Prioritas selector
        pri_row = ctk.CTkFrame(af, fg_color="transparent")
        pri_row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(pri_row, text="Prioritas Laporan",
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=(0, 10))
        
        current_pri = laporan.get("prioritas", "Rendah")
        self.prioritas_var = ctk.StringVar(value=current_pri)
        self.prioritas_combo = ctk.CTkComboBox(
            pri_row, values=["Rendah", "Sedang", "Tinggi"],
            variable=self.prioritas_var,
            width=140, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12), state="readonly"
        )
        self.prioritas_combo.pack(side="left")

        ctk.CTkLabel(af, text="Catatan Admin *",
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        self.catatan_text = ctk.CTkTextbox(
            af, height=60, corner_radius=8, font=ctk.CTkFont(size=12),
            border_width=1, border_color=("gray70", "gray35"))
        self.catatan_text.pack(fill="x", pady=(3, 12))

        btn_f = ctk.CTkFrame(af, fg_color="transparent")
        btn_f.pack(fill="x")
        actions = [
            ("✅ Proses", "Diproses Kelurahan", "#1E88E5"),
            ("🏁 Selesai", "Selesai", "#43A047"),
            ("❌ Tolak", "Ditolak", "#E53935"),
            ("⬆️ Eskalasi Kecamatan", "Diproses Kecamatan", "#7B1FA2"),
        ]
        for text, status, color in actions:
            ctk.CTkButton(
                btn_f, text=text, height=36, corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=color, hover_color=color,
                command=lambda s=status: self._proses(s)
            ).pack(side="left", padx=(0, 6))

        # ── Timeline ──
        tl_card = ctk.CTkFrame(c, corner_radius=12,
                                fg_color=("white", "gray17"),
                                border_width=1, border_color=("gray88", "gray28"))
        tl_card.pack(fill="x", padx=30, pady=(0, 20))

        tc = ctk.CTkFrame(tl_card, fg_color="transparent")
        tc.pack(fill="x", padx=28, pady=20)
        ctk.CTkLabel(tc, text="📌  Timeline Status",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=(NAVY, SKY_BLUE), anchor="w").pack(fill="x", pady=(0, 12))

        riwayat = self.laporan_ctrl.get_riwayat_laporan(laporan["id"])
        if not riwayat:
            ctk.CTkLabel(tc, text="Belum ada riwayat.",
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

    def _proses(self, status_baru: str):
        if not self.selected_laporan:
            return
        catatan = self.catatan_text.get("1.0", "end-1c")
        prioritas = self.prioritas_var.get() if hasattr(self, 'prioritas_var') else None
        result = self.laporan_ctrl.proses_laporan(
            laporan_id=self.selected_laporan["id"],
            admin_id=self.app.current_user["id"],
            status_baru=status_baru, catatan=catatan,
            prioritas=prioritas
        )
        if result["success"]:
            messagebox.showinfo("Berhasil", result["message"])
            self._show_main()
        else:
            messagebox.showerror("Gagal", result["message"])
