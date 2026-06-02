# views/warga/dashboard_warga.py
# Dashboard Warga — Redesign Sky Blue palette + Invoice-style form + Detail Page

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

# ── Warna dot per-status (untuk tampilan tabel) ──
STATUS_DOT_COLORS = {
    "Menunggu": "#FFA726",
    "Diproses Kelurahan": "#42A5F5",
    "Diproses Kecamatan": "#AB47BC",
    "Diproses Kota": "#FF7043",
    "Selesai": "#66BB6A",
    "Ditolak": "#EF5350",
}


class DashboardWarga(ctk.CTkFrame):
    """Dashboard Warga dengan page switching: Dashboard / Buat Laporan / Detail."""

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

        # ── Scrollable Content Area ──
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
    # PAGE 1 : DASHBOARD
    # ══════════════════════════════════════════

    def _show_dashboard_page(self):
        self._clear_content()
        self._load_data()
        c = self.content

        # ── Header ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 20))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")

        name = self.app.current_user.get("nama_lengkap", "User")
        ctk.CTkLabel(
            left, text=f"Halo, {name}",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Berikut ringkasan pengaduan dan aspirasi Anda",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            header, text="＋  Buat Laporan Baru",
            height=38, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=(TEAL, TEAL),
            hover_color=(NAVY, NAVY),
            command=self._show_form_page
        ).pack(side="right")

        # ── Stat Cards Row ──
        cards_f = ctk.CTkFrame(c, fg_color="transparent")
        cards_f.pack(fill="x", padx=30, pady=(0, 20))
        for i in range(4):
            cards_f.grid_columnconfigure(i, weight=1)

        data = self.all_laporan
        card_defs = [
            ("Total Laporan",  len(data), TEAL, "📋"),
            ("Menunggu", sum(1 for d in data if d["status"] == "Menunggu"), "#FFA726", "⏳"),
            ("Diproses", sum(1 for d in data if "Diproses" in d.get("status", "")), SKY_BLUE, "🔄"),
            ("Selesai",  sum(1 for d in data if d["status"] == "Selesai"), "#66BB6A", "✅"),
        ]

        self._card_labels = {}
        for i, (label, val, color, icon) in enumerate(card_defs):
            card = ctk.CTkFrame(
                cards_f, corner_radius=12,
                fg_color=("white", "gray17"),
                border_width=1, border_color=("gray88", "gray28")
            )
            card.grid(row=0, column=i, sticky="ew", padx=6)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=20, pady=18)

            ctk.CTkLabel(
                inner, text=label,
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60")
            ).pack(anchor="w")

            num_row = ctk.CTkFrame(inner, fg_color="transparent")
            num_row.pack(fill="x", pady=(6, 0))

            vl = ctk.CTkLabel(
                num_row, text=f"{val:02d}",
                font=ctk.CTkFont(size=34, weight="bold"),
                text_color=color
            )
            vl.pack(side="left")
            self._card_labels[label] = vl

            ctk.CTkLabel(
                num_row, text=icon,
                font=ctk.CTkFont(size=26),
                text_color=("gray82", "gray32")
            ).pack(side="right")

        # ── Filter Bar ──
        filter_card = ctk.CTkFrame(
            c, corner_radius=10,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        filter_card.pack(fill="x", padx=30, pady=(0, 15))

        fi = ctk.CTkFrame(filter_card, fg_color="transparent")
        fi.pack(fill="x", padx=20, pady=12)

        # Status
        ctk.CTkLabel(fi, text="Status", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(side="left", padx=(0, 4))
        self.f_status = ctk.CTkComboBox(
            fi, values=["Semua"] + STATUS_LAPORAN,
            width=165, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_filters(), state="readonly"
        )
        self.f_status.pack(side="left", padx=(0, 18))
        self.f_status.set("Semua")

        # Kategori
        ctk.CTkLabel(fi, text="Kategori", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(side="left", padx=(0, 4))
        self.f_kategori = ctk.CTkComboBox(
            fi, values=["Semua"] + KATEGORI_LAPORAN,
            width=175, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_filters(), state="readonly"
        )
        self.f_kategori.pack(side="left", padx=(0, 18))
        self.f_kategori.set("Semua")

        # Reset
        ctk.CTkButton(
            fi, text="Reset Filter",
            height=32, corner_radius=8, width=105,
            font=ctk.CTkFont(size=12),
            fg_color=(TEAL, TEAL),
            hover_color=(NAVY, NAVY),
            command=self._reset_filters
        ).pack(side="right")

        # ── Table Header ──
        th = ctk.CTkFrame(c, fg_color="transparent", height=30)
        th.pack(fill="x", padx=36, pady=(5, 0))
        th.pack_propagate(False)

        col_defs = [
            ("Judul Laporan", 270), ("Status", 150),
            ("Kategori", 145), ("Kelurahan", 130),
            ("Diperbarui", 110), ("Dibuat", 110),
        ]
        for label, w in col_defs:
            ctk.CTkLabel(
                th, text=label, width=w,
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60"),
                anchor="w"
            ).pack(side="left", padx=4)

        # ── Separator ──
        ctk.CTkFrame(c, height=1, fg_color=("gray85", "gray25")).pack(
            fill="x", padx=30, pady=(2, 0))

        # ── Table Body ──
        self.rows_frame = ctk.CTkFrame(c, fg_color="transparent")
        self.rows_frame.pack(fill="x", padx=30)

        self._render_rows()

    # ── Table rows render ──
    def _render_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()

        if not self.filtered_laporan:
            ctk.CTkLabel(
                self.rows_frame,
                text="Belum ada laporan. Klik \"Buat Laporan Baru\" untuk memulai.",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60")
            ).pack(pady=40)
            return

        for i, lap in enumerate(self.filtered_laporan):
            is_even = i % 2 == 0
            bg = ("white", "gray17") if is_even else ("gray98", "gray15")

            row = ctk.CTkFrame(
                self.rows_frame, fg_color=bg,
                corner_radius=8, height=72
            )
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=6)

            # ── Col: Judul + Deskripsi ──
            title_f = ctk.CTkFrame(inner, fg_color="transparent", width=270)
            title_f.pack(side="left", padx=4)
            title_f.pack_propagate(False)

            judul = truncate_text(lap.get("judul", ""), 30)
            ctk.CTkLabel(
                title_f,
                text=f"{judul}  #{lap['id']}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            ).pack(anchor="w")

            desc = truncate_text(lap.get("deskripsi", ""), 42)
            ctk.CTkLabel(
                title_f, text=desc,
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60"),
                anchor="w"
            ).pack(anchor="w")

            # ── Col: Status (dot + text) ──
            st_f = ctk.CTkFrame(inner, fg_color="transparent", width=150)
            st_f.pack(side="left", padx=4)
            st_f.pack_propagate(False)

            st_inner = ctk.CTkFrame(st_f, fg_color="transparent")
            st_inner.pack(anchor="w", pady=12)

            dot_color = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
            ctk.CTkLabel(
                st_inner, text="●  ",
                font=ctk.CTkFont(size=10),
                text_color=dot_color
            ).pack(side="left")
            ctk.CTkLabel(
                st_inner, text=lap["status"],
                font=ctk.CTkFont(size=12), anchor="w"
            ).pack(side="left")

            # ── Col: Kategori ──
            kat_f = ctk.CTkFrame(inner, fg_color="transparent", width=145)
            kat_f.pack(side="left", padx=4)
            kat_f.pack_propagate(False)

            kat_badge = ctk.CTkLabel(
                kat_f,
                text=f" {truncate_text(lap.get('kategori', ''), 18)} ",
                font=ctk.CTkFont(size=11),
                fg_color=("gray88", "gray28"),
                corner_radius=5,
                text_color=("gray30", "gray80")
            )
            kat_badge.pack(anchor="w", pady=14)

            # ── Col: Kelurahan ──
            kel_f = ctk.CTkFrame(inner, fg_color="transparent", width=130)
            kel_f.pack(side="left", padx=4)
            kel_f.pack_propagate(False)
            ctk.CTkLabel(
                kel_f,
                text=truncate_text(lap.get("kelurahan", ""), 16),
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(anchor="w", pady=14)

            # ── Col: Diperbarui ──
            upd_f = ctk.CTkFrame(inner, fg_color="transparent", width=110)
            upd_f.pack(side="left", padx=4)
            upd_f.pack_propagate(False)
            updated = format_tanggal(lap.get("updated_at", lap.get("created_at")))
            ctk.CTkLabel(
                upd_f, text=f"🕐 {updated}",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60"), anchor="w"
            ).pack(anchor="w", pady=14)

            # ── Col: Dibuat ──
            crt_f = ctk.CTkFrame(inner, fg_color="transparent", width=110)
            crt_f.pack(side="left", padx=4)
            crt_f.pack_propagate(False)
            created = format_tanggal(lap.get("created_at"))
            ctk.CTkLabel(
                crt_f, text=f"🕐 {created}",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60"), anchor="w"
            ).pack(anchor="w", pady=14)

            # ── Click binding → open detail PAGE ──
            def _bind_click(widget, data=lap):
                widget.bind("<Button-1>", lambda e: self._show_detail_page(data))
                if hasattr(widget, "winfo_children"):
                    for child in widget.winfo_children():
                        _bind_click(child, data)

            _bind_click(row)

            # ── Hover ──
            row.bind("<Enter>", lambda e, r=row: r.configure(
                fg_color=("gray92", "gray22")))
            row.bind("<Leave>", lambda e, r=row, b=bg: r.configure(fg_color=b))

    # ── Filter logic ──
    def _apply_filters(self):
        st = self.f_status.get()
        kt = self.f_kategori.get()

        data = list(self.all_laporan)
        if st != "Semua":
            data = [d for d in data if d["status"] == st]
        if kt != "Semua":
            data = [d for d in data if d.get("kategori") == kt]

        self.filtered_laporan = data
        self._render_rows()

    def _reset_filters(self):
        self.f_status.set("Semua")
        self.f_kategori.set("Semua")
        self.filtered_laporan = list(self.all_laporan)
        self._render_rows()

    # ══════════════════════════════════════════
    # PAGE 2 : BUAT LAPORAN (Invoice-style 2-panel)
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
            font=ctk.CTkFont(size=24, weight="bold"), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            left_hdr, text="Sampaikan keluhan atau aspirasi Anda kepada pemerintah",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 0))

        # Header buttons
        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row, text="🔍  Simpan Draft",
            height=38, corner_radius=8, width=140,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=1,
            border_color=(TEAL, TEAL),
            text_color=(TEAL, SKY_BLUE),
            hover_color=("gray90", "gray25"),
            command=lambda: None  # placeholder
        ).pack(side="left", padx=(0, 10))

        self.submit_btn = ctk.CTkButton(
            btn_row, text="📤  Kirim Laporan",
            height=38, corner_radius=8, width=160,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=(TEAL, TEAL),
            hover_color=(NAVY, NAVY),
            command=self._submit_form
        )
        self.submit_btn.pack(side="left")

        # ── Two-panel layout ──
        panels = ctk.CTkFrame(c, fg_color="transparent")
        panels.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        panels.grid_columnconfigure(0, weight=3)
        panels.grid_columnconfigure(1, weight=2)

        # ═════════════════════════════
        # LEFT PANEL — Form Input
        # ═════════════════════════════
        left_card = ctk.CTkFrame(
            panels, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        lf = ctk.CTkFrame(left_card, fg_color="transparent")
        lf.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            lf, text="Detail Pengaduan",
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            lf, text="Isi semua informasi di bawah ini",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 18))

        # ── Section: Informasi Dasar ──
        sec1_header = ctk.CTkFrame(lf, fg_color="transparent")
        sec1_header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            sec1_header, text="📋  Informasi Dasar",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=(NAVY, SKY_BLUE)
        ).pack(anchor="w")

        # Kategori + Judul row
        row1 = ctk.CTkFrame(lf, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 14))
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=2)

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

        f2 = ctk.CTkFrame(row1, fg_color="transparent")
        f2.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(f2, text="Judul Laporan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_judul = ctk.CTkEntry(
            f2, height=36, corner_radius=8,
            placeholder_text="Ringkasan masalah",
            font=ctk.CTkFont(size=13)
        )
        self.form_judul.pack(fill="x", pady=(3, 0))

        # ── Separator ──
        ctk.CTkFrame(lf, height=1, fg_color=("gray88", "gray28")).pack(
            fill="x", pady=(4, 14))

        # ── Section: Lokasi ──
        sec2_header = ctk.CTkFrame(lf, fg_color="transparent")
        sec2_header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            sec2_header, text="📍  Lokasi Pengaduan",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=(NAVY, SKY_BLUE)
        ).pack(anchor="w")

        # Kecamatan + Kelurahan row
        row2 = ctk.CTkFrame(lf, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))
        row2.grid_columnconfigure(0, weight=1)
        row2.grid_columnconfigure(1, weight=1)

        f3 = ctk.CTkFrame(row2, fg_color="transparent")
        f3.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(f3, text="Kecamatan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kecamatan = ctk.CTkComboBox(
            f3, values=get_semua_kecamatan(),
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            command=self._on_kecamatan_changed, state="readonly"
        )
        self.form_kecamatan.pack(fill="x", pady=(3, 0))
        self.form_kecamatan.set("Pilih Kecamatan")

        f4 = ctk.CTkFrame(row2, fg_color="transparent")
        f4.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(f4, text="Kelurahan *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_kelurahan = ctk.CTkComboBox(
            f4, values=["Pilih kecamatan dahulu"],
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            state="readonly"
        )
        self.form_kelurahan.pack(fill="x", pady=(3, 0))
        self.form_kelurahan.set("Pilih kecamatan dahulu")

        # Lokasi spesifik
        fl = ctk.CTkFrame(lf, fg_color="transparent")
        fl.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(fl, text="Alamat Spesifik *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_lokasi = ctk.CTkEntry(
            fl, height=36, corner_radius=8,
            placeholder_text="Contoh: Jl. Sam Ratulangi No. 12",
            font=ctk.CTkFont(size=13)
        )
        self.form_lokasi.pack(fill="x", pady=(3, 0))

        # ── Separator ──
        ctk.CTkFrame(lf, height=1, fg_color=("gray88", "gray28")).pack(
            fill="x", pady=(4, 14))

        # ── Section: Deskripsi ──
        sec3_header = ctk.CTkFrame(lf, fg_color="transparent")
        sec3_header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            sec3_header, text="📝  Deskripsi",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=(NAVY, SKY_BLUE)
        ).pack(anchor="w")

        ctk.CTkLabel(lf, text="Deskripsi Detail *", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60")).pack(anchor="w")
        self.form_deskripsi = ctk.CTkTextbox(
            lf, height=120, corner_radius=8,
            font=ctk.CTkFont(size=13),
            border_width=1, border_color=("gray72", "gray35")
        )
        self.form_deskripsi.pack(fill="x", pady=(3, 0))

        # ═════════════════════════════
        # RIGHT PANEL — Preview
        # ═════════════════════════════
        right_card = ctk.CTkFrame(
            panels, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        right_card.grid(row=0, column=1, sticky="nsew")

        rf = ctk.CTkFrame(right_card, fg_color="transparent")
        rf.pack(fill="both", expand=True, padx=24, pady=24)

        # Preview header with icon
        preview_hdr = ctk.CTkFrame(rf, fg_color="transparent")
        preview_hdr.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            preview_hdr, text="📄",
            font=ctk.CTkFont(size=32)
        ).pack(anchor="center")
        ctk.CTkLabel(
            preview_hdr, text="Preview Laporan",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=(NAVY, SKY_BLUE)
        ).pack(anchor="center", pady=(4, 0))

        ctk.CTkFrame(rf, height=1, fg_color=("gray85", "gray28")).pack(
            fill="x", pady=(10, 14))

        # ── Pelapor Info ──
        user = self.app.current_user
        ctk.CTkLabel(
            rf, text="Pelapor",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack(anchor="w")
        ctk.CTkLabel(
            rf, text=user.get("nama_lengkap", "User"),
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            rf, text=user.get("email", ""),
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkFrame(rf, height=1, fg_color=("gray88", "gray28")).pack(
            fill="x", pady=(0, 12))

        # ── Preview fields (will update live) ──
        preview_fields = [
            ("Kategori",  "kategori"),
            ("Judul",     "judul"),
            ("Kecamatan", "kecamatan"),
            ("Kelurahan", "kelurahan"),
            ("Lokasi",    "lokasi"),
        ]
        self._preview_labels = {}
        for label_text, key in preview_fields:
            ctk.CTkLabel(
                rf, text=label_text,
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60")
            ).pack(anchor="w")
            pv_lbl = ctk.CTkLabel(
                rf, text="—",
                font=ctk.CTkFont(size=12),
                anchor="w", wraplength=250
            )
            pv_lbl.pack(anchor="w", pady=(2, 8))
            self._preview_labels[key] = pv_lbl

        ctk.CTkFrame(rf, height=1, fg_color=("gray88", "gray28")).pack(
            fill="x", pady=(4, 12))

        ctk.CTkLabel(
            rf, text="Deskripsi",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        ).pack(anchor="w")
        self._preview_desc = ctk.CTkLabel(
            rf, text="—",
            font=ctk.CTkFont(size=12),
            anchor="w", wraplength=250,
            justify="left"
        )
        self._preview_desc.pack(anchor="w", pady=(2, 0))

        # ── Setup live preview bindings ──
        self._setup_preview_bindings()

    def _setup_preview_bindings(self):
        """Bind form fields to update preview in real-time."""
        def update_preview(*args):
            try:
                kategori = self.form_kategori.get()
                if kategori.startswith("Pilih"):
                    kategori = "—"
                self._preview_labels["kategori"].configure(text=kategori)

                judul = self.form_judul.get() or "—"
                self._preview_labels["judul"].configure(text=judul)

                kecamatan = self.form_kecamatan.get()
                if kecamatan.startswith("Pilih"):
                    kecamatan = "—"
                self._preview_labels["kecamatan"].configure(text=kecamatan)

                kelurahan = self.form_kelurahan.get()
                if kelurahan.startswith("Pilih") or kelurahan == "Tidak ada data":
                    kelurahan = "—"
                self._preview_labels["kelurahan"].configure(text=kelurahan)

                lokasi = self.form_lokasi.get() or "—"
                self._preview_labels["lokasi"].configure(text=lokasi)

                deskripsi = self.form_deskripsi.get("1.0", "end-1c").strip() or "—"
                self._preview_desc.configure(text=truncate_text(deskripsi, 200))
            except Exception:
                pass

        # Bind key release for text fields
        self.form_judul.bind("<KeyRelease>", update_preview)
        self.form_lokasi.bind("<KeyRelease>", update_preview)
        self.form_deskripsi.bind("<KeyRelease>", update_preview)

        # Bind combobox changes
        orig_kec_cmd = self._on_kecamatan_changed
        def kec_wrapper(val):
            orig_kec_cmd(val)
            update_preview()
        self.form_kecamatan.configure(command=kec_wrapper)
        self.form_kategori.configure(command=lambda v: update_preview())
        self.form_kelurahan.configure(command=lambda v: update_preview())

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
        """Tampilkan halaman detail laporan terpisah (invoice-detail style)."""
        self._clear_content()
        c = self.content
        self.selected_laporan = laporan

        # ── Header with Back button ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 20))

        ctk.CTkButton(
            header, text="←  Kembali",
            height=34, corner_radius=8, width=120,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=1,
            border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._show_dashboard_page
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Laporan",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=(20, 0))

        # Status badge in header
        StatusBadge(header, status=laporan["status"]).pack(side="right")

        # ── Main card ──
        main_card = ctk.CTkFrame(
            c, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        main_card.pack(fill="x", padx=30, pady=(0, 15))

        mc = ctk.CTkFrame(main_card, fg_color="transparent")
        mc.pack(fill="x", padx=28, pady=24)

        # ── Two-column info section ──
        info_row = ctk.CTkFrame(mc, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 16))
        info_row.grid_columnconfigure(0, weight=1)
        info_row.grid_columnconfigure(1, weight=1)

        # Left column: Pelapor info
        left_info = ctk.CTkFrame(info_row, fg_color="transparent")
        left_info.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        ctk.CTkLabel(
            left_info, text=f"Laporan #{laporan['id']:06d}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=(NAVY, SKY_BLUE)
        ).pack(anchor="w")

        ctk.CTkFrame(left_info, height=1, fg_color=("gray88", "gray28")).pack(
            fill="x", pady=(8, 10))

        info_left_items = [
            ("Status", laporan.get("status", "")),
            ("Kategori", laporan.get("kategori", "")),
            ("Pelapor", laporan.get("nama_pelapor", self.app.current_user.get("nama_lengkap", ""))),
        ]
        for label, value in info_left_items:
            row_f = ctk.CTkFrame(left_info, fg_color="transparent")
            row_f.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row_f, text=f"{label}:",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60"),
                width=85, anchor="w"
            ).pack(side="left")
            if label == "Status":
                StatusBadge(row_f, status=value).pack(side="left")
            else:
                ctk.CTkLabel(
                    row_f, text=value,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w"
                ).pack(side="left")

        # Right column: Lokasi & tanggal
        right_info = ctk.CTkFrame(info_row, fg_color="transparent")
        right_info.grid(row=0, column=1, sticky="nsew")

        # Illustration / icon
        illust_frame = ctk.CTkFrame(right_info, fg_color="transparent")
        illust_frame.pack(anchor="e", pady=(0, 10))
        ctk.CTkLabel(
            illust_frame, text="📋",
            font=ctk.CTkFont(size=48),
            text_color=("gray85", "gray30")
        ).pack()

        info_right_items = [
            ("Tanggal Dibuat", format_tanggal(laporan.get("created_at"))),
            ("Diperbarui", format_tanggal(laporan.get("updated_at", laporan.get("created_at")))),
            ("Lokasi", f"{laporan.get('lokasi', '')}"),
            ("Wilayah", f"Kel. {laporan.get('kelurahan', '')}, Kec. {laporan.get('kecamatan', '')}"),
        ]
        for label, value in info_right_items:
            row_f = ctk.CTkFrame(right_info, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row_f, text=f"{label}:",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60"),
                width=110, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                row_f, text=value,
                font=ctk.CTkFont(size=12),
                anchor="w", wraplength=300
            ).pack(side="left")

        # ── Detail Table (invoice items style) ──
        ctk.CTkFrame(mc, height=1, fg_color=("gray85", "gray28")).pack(
            fill="x", pady=(8, 14))

        ctk.CTkLabel(
            mc, text="📄  Detail Laporan",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=(NAVY, SKY_BLUE), anchor="w"
        ).pack(fill="x", pady=(0, 8))

        # Table header
        tbl_header = ctk.CTkFrame(mc, fg_color=(BEIGE, "gray22"),
                                   corner_radius=6, height=36)
        tbl_header.pack(fill="x")
        tbl_header.pack_propagate(False)

        tbl_cols = [("FIELD", 150), ("DETAIL", 500)]
        for col_label, w in tbl_cols:
            ctk.CTkLabel(
                tbl_header, text=col_label, width=w,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray45", "gray65"), anchor="w"
            ).pack(side="left", padx=(16, 0), pady=8)

        # Table rows
        detail_items = [
            ("Judul", laporan.get("judul", "")),
            ("Kategori", laporan.get("kategori", "")),
            ("Lokasi Lengkap", f"{laporan.get('lokasi', '')} — Kel. {laporan.get('kelurahan', '')}, Kec. {laporan.get('kecamatan', '')}"),
            ("Deskripsi", laporan.get("deskripsi", "")),
        ]
        for idx, (field, value) in enumerate(detail_items):
            row_bg = ("white", "gray17") if idx % 2 == 0 else ("gray98", "gray15")
            tbl_row = ctk.CTkFrame(mc, fg_color=row_bg, height=42,
                                    corner_radius=4)
            tbl_row.pack(fill="x", pady=1)
            tbl_row.pack_propagate(False)

            ctk.CTkLabel(
                tbl_row, text=field, width=150,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("gray40", "gray70"), anchor="w"
            ).pack(side="left", padx=(16, 0), pady=6)
            ctk.CTkLabel(
                tbl_row, text=value,
                font=ctk.CTkFont(size=12), anchor="w",
                wraplength=480
            ).pack(side="left", padx=(0, 16), pady=6, fill="x")

        # ── Timeline Section ──
        timeline_card = ctk.CTkFrame(
            c, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        timeline_card.pack(fill="x", padx=30, pady=(0, 20))

        tc = ctk.CTkFrame(timeline_card, fg_color="transparent")
        tc.pack(fill="x", padx=28, pady=20)

        ctk.CTkLabel(
            tc, text="📌  Timeline Status",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=(NAVY, SKY_BLUE), anchor="w"
        ).pack(fill="x", pady=(0, 12))

        riwayat = self.laporan_ctrl.get_riwayat_laporan(laporan["id"])

        if not riwayat:
            ctk.CTkLabel(
                tc, text="Belum ada riwayat perubahan status.",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60")
            ).pack(pady=10)
        else:
            tl_frame = ctk.CTkFrame(tc, fg_color="transparent")
            tl_frame.pack(fill="x")

            for j, rw in enumerate(riwayat):
                is_last = (j == len(riwayat) - 1)
                item = ctk.CTkFrame(tl_frame, fg_color="transparent")
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

                st_text = rw.get("status_baru", "")
                time_text = format_tanggal(rw.get("created_at"))
                ctk.CTkLabel(
                    cf, text=f"{st_text}  •  {time_text}",
                    font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
                ).pack(fill="x")

                catatan = rw.get("catatan_admin", "")
                if catatan:
                    admin_name = rw.get("nama_admin", "Sistem")
                    ctk.CTkLabel(
                        cf, text=f"oleh {admin_name}: {catatan}",
                        font=ctk.CTkFont(size=11),
                        text_color=("gray45", "gray62"),
                        anchor="w", wraplength=550
                    ).pack(fill="x")
