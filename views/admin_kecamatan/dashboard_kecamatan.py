# views/admin_kecamatan/dashboard_kecamatan.py
# Dashboard untuk Admin Kecamatan — dengan detail page terpisah

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
    # DETAIL PAGE
    # ══════════════════════════════════════════

    def _show_detail_page(self, laporan: dict):
        self._clear()
        c = self.content
        self.selected_laporan = laporan

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
        ctk.CTkLabel(header, text=f"Detail Laporan #{laporan['id']}",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left", padx=(20, 0))
        StatusBadge(header, status=laporan["status"]).pack(side="right")

        # Info Card
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
            ctk.CTkLabel(rf, text=val, font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w", wraplength=300).pack(side="left")

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
            ctk.CTkLabel(rf, text=val, font=ctk.CTkFont(size=12),
                         anchor="w").pack(side="left")

        ctk.CTkFrame(ic, height=1, fg_color=("gray88", "gray28")).pack(fill="x", pady=(14, 10))
        ctk.CTkLabel(ic, text="Deskripsi:", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(ic, text=laporan.get("deskripsi", ""), font=ctk.CTkFont(size=12),
                     anchor="w", wraplength=650, justify="left").pack(fill="x", pady=(4, 0))

        # Action Card
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
        self.catatan_text = ctk.CTkTextbox(af, height=60, corner_radius=8,
                                            font=ctk.CTkFont(size=12),
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

        # Timeline
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
            ctk.CTkLabel(tc, text="Belum ada riwayat.", font=ctk.CTkFont(size=12),
                         text_color=("gray50", "gray60")).pack(pady=10)
        else:
            for j, rw in enumerate(riwayat):
                is_last = j == len(riwayat) - 1
                item = ctk.CTkFrame(tc, fg_color="transparent")
                item.pack(fill="x")
                dot_f = ctk.CTkFrame(item, fg_color="transparent", width=30)
                dot_f.pack(side="left", anchor="n")
                dot_f.pack_propagate(False)
                ctk.CTkLabel(dot_f, text="●",
                             text_color=TEAL if is_last else ("gray60", "gray50"),
                             font=ctk.CTkFont(size=14)).pack(pady=(3, 0))
                if not is_last:
                    ctk.CTkFrame(dot_f, width=2, height=28,
                                 fg_color=("gray75", "gray38")).pack()
                cf = ctk.CTkFrame(item, fg_color="transparent")
                cf.pack(side="left", fill="x", expand=True, padx=(4, 0))
                ctk.CTkLabel(cf, text=f"{rw.get('status_baru', '')}  •  {format_tanggal(rw.get('created_at'))}",
                             font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
                cat = rw.get("catatan_admin", "")
                if cat:
                    ctk.CTkLabel(cf, text=f"oleh {rw.get('nama_admin', 'Sistem')}: {cat}",
                                 font=ctk.CTkFont(size=11), text_color=("gray45", "gray62"),
                                 anchor="w", wraplength=550).pack(fill="x")

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
