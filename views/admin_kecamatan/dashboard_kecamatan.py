# views/admin_kecamatan/dashboard_kecamatan.py
# Dashboard untuk Admin Kecamatan — matching kelurahan style with detail page

import customtkinter as ctk
from tkinter import messagebox
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.wilayah import get_kelurahan_by_kecamatan

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


class DashboardKecamatan(ctk.CTkFrame):
    """Dashboard Admin Kecamatan: melihat laporan se-kecamatan, proses eskalasi."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=("gray95", "gray12"), **kwargs)
        self.app = app
        self.laporan_ctrl = LaporanController(app.db)
        self.kecamatan = app.current_user.get("kecamatan", "")
        self.selected_laporan = None

        # ── Layout ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = Sidebar(self, app=app, menu_items=[
            {"icon": "🏠", "label": "Dashboard", "command": self._show_main},
        ])
        sidebar.grid(row=0, column=0, sticky="nsw")

        # ── Content ──
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
        data = self.laporan_ctrl.get_laporan_kecamatan(self.kecamatan)

        # Header
        ctk.CTkLabel(
            c, text=f"📋  Dashboard Kecamatan {self.kecamatan}",
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

        # ── Filter Bar ──
        filter_bar = ctk.CTkFrame(c, fg_color="transparent")
        filter_bar.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(filter_bar, text="Kelurahan:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        kelurahan_list = ["Semua"] + get_kelurahan_by_kecamatan(self.kecamatan)
        self.kel_filter_var = ctk.StringVar(value="Semua")
        ctk.CTkComboBox(
            filter_bar, values=kelurahan_list,
            variable=self.kel_filter_var,
            width=180, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_filter(), state="readonly"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(filter_bar, text="Status:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        self.status_filter_var = ctk.StringVar(value="Semua")
        ctk.CTkComboBox(
            filter_bar, values=["Semua", "Menunggu", "Diproses Kelurahan",
                                "Diproses Kecamatan", "Selesai", "Ditolak"],
            variable=self.status_filter_var,
            width=180, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_filter(), state="readonly"
        ).pack(side="left")

        # ── Table ──
        self._all_data = data
        self._build_table(data)

    def _build_table(self, data):
        if hasattr(self, '_table_frame'):
            self._table_frame.destroy()

        self._table_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self._table_frame.pack(fill="x", padx=30, pady=(0, 15))

        th = ctk.CTkFrame(self._table_frame, fg_color=("gray94", "gray20"),
                          corner_radius=6, height=36)
        th.pack(fill="x")
        th.pack_propagate(False)

        cols = [("#", 45), ("Judul", 170), ("Pelapor", 120), ("Kelurahan", 120),
                ("Kategori", 120), ("Status", 140), ("Tanggal", 120)]
        for lbl, w in cols:
            ctk.CTkLabel(th, text=lbl, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=("gray45", "gray65"), anchor="w"
                         ).pack(side="left", padx=(10, 0), pady=8)

        if not data:
            ctk.CTkLabel(self._table_frame, text="Tidak ada laporan.",
                         font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(pady=20)
            return

        for idx, lap in enumerate(data):
            row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
            rr = ctk.CTkFrame(self._table_frame, fg_color=row_bg,
                              height=40, corner_radius=4)
            rr.pack(fill="x", pady=1)
            rr.pack_propagate(False)

            ctk.CTkLabel(rr, text=f"#{lap['id']}", width=45,
                         font=ctk.CTkFont(size=12),
                         text_color=(TEAL, SKY_BLUE), anchor="w"
                         ).pack(side="left", padx=(10, 0))
            ctk.CTkLabel(rr, text=truncate_text(lap.get("judul", ""), 22),
                         width=170, font=ctk.CTkFont(size=12),
                         anchor="w").pack(side="left")
            ctk.CTkLabel(rr, text=truncate_text(lap.get("nama_pelapor", ""), 16),
                         width=120, font=ctk.CTkFont(size=12),
                         anchor="w").pack(side="left")
            ctk.CTkLabel(rr, text=truncate_text(lap.get("kelurahan", ""), 16),
                         width=120, font=ctk.CTkFont(size=12),
                         anchor="w").pack(side="left")
            ctk.CTkLabel(rr, text=truncate_text(lap.get("kategori", ""), 14),
                         width=120, font=ctk.CTkFont(size=12),
                         anchor="w").pack(side="left")

            st_clr = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
            ctk.CTkLabel(rr, text=f"● {lap['status']}", width=140,
                         font=ctk.CTkFont(size=11), text_color=st_clr,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(rr, text=format_tanggal(lap.get("created_at")),
                         width=120, font=ctk.CTkFont(size=11),
                         text_color=("gray50", "gray60"), anchor="w"
                         ).pack(side="left")

            def _bind(widget, d=lap):
                widget.bind("<Button-1>", lambda e: self._show_detail_page(d))
                if hasattr(widget, "winfo_children"):
                    for ch in widget.winfo_children():
                        _bind(ch, d)
            _bind(rr)
            rr.bind("<Enter>", lambda e, r=rr: r.configure(fg_color=("gray92", "gray22")))
            rr.bind("<Leave>", lambda e, r=rr, b=row_bg: r.configure(fg_color=b))

    def _apply_filter(self, status=None):
        kel = self.kel_filter_var.get()
        st = status or self.status_filter_var.get()

        if st and st != "Semua":
            data = self.laporan_ctrl.get_laporan_kecamatan(self.kecamatan, st)
        else:
            data = self.laporan_ctrl.get_laporan_kecamatan(self.kecamatan)

        if kel and kel != "Semua":
            data = [d for d in data if d.get("kelurahan") == kel]

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

        ctk.CTkLabel(af, text="Catatan Admin *",
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        self.catatan_text = ctk.CTkTextbox(
            af, height=60, corner_radius=8, font=ctk.CTkFont(size=12),
            border_width=1, border_color=("gray70", "gray35"))
        self.catatan_text.pack(fill="x", pady=(3, 12))

        btn_f = ctk.CTkFrame(af, fg_color="transparent")
        btn_f.pack(fill="x")
        for text, status, color in [
            ("✅ Proses", "Diproses Kecamatan", "#1E88E5"),
            ("🏁 Selesai", "Selesai", "#43A047"),
            ("❌ Tolak", "Ditolak", "#E53935"),
            ("⬆️ Eskalasi ke Kota", "Diproses Kota", "#7B1FA2"),
        ]:
            ctk.CTkButton(btn_f, text=text, height=36, corner_radius=8,
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
        result = self.laporan_ctrl.proses_laporan(
            laporan_id=self.selected_laporan["id"],
            admin_id=self.app.current_user["id"],
            status_baru=status_baru, catatan=catatan
        )
        if result["success"]:
            messagebox.showinfo("Berhasil", result["message"])
            self._show_main()
        else:
            messagebox.showerror("Gagal", result["message"])
