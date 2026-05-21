# views/warga/dashboard_warga.py
# Dashboard Warga — Redesign mengikuti gaya HexSupport/Ticket System

import customtkinter as ctk
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.settings import KATEGORI_LAPORAN, STATUS_LAPORAN
from config.wilayah import get_semua_kecamatan, get_kelurahan_by_kecamatan


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
    """Dashboard Warga dengan page switching: Dashboard / Buat Laporan."""

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
    # PAGE 1 : DASHBOARD  (Gambar referensi 1)
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
            fg_color=("#6C5CE7", "#7C6CF7"),
            hover_color=("#5A4BD1", "#6B5BE6"),
            command=self._show_form_page
        ).pack(side="right")

        # ── Stat Cards Row ──
        cards_f = ctk.CTkFrame(c, fg_color="transparent")
        cards_f.pack(fill="x", padx=30, pady=(0, 20))
        for i in range(4):
            cards_f.grid_columnconfigure(i, weight=1)

        data = self.all_laporan
        card_defs = [
            ("Total Laporan",  len(data), "#6C5CE7", "📋"),
            ("Menunggu", sum(1 for d in data if d["status"] == "Menunggu"), "#FFA726", "⏳"),
            ("Diproses", sum(1 for d in data if "Diproses" in d.get("status", "")), "#42A5F5", "🔄"),
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
            fg_color=("#6C5CE7", "#7C6CF7"),
            hover_color=("#5A4BD1", "#6B5BE6"),
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

        # ── Detail Panel (hidden) ──
        self.detail_frame = ctk.CTkFrame(
            c, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )

        self._render_rows()

    # ── Table rows render ──
    def _render_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()
        self.detail_frame.pack_forget()

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

            # ── Click binding ──
            def _bind_click(widget, data=lap):
                widget.bind("<Button-1>", lambda e: self._show_detail(data))
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

    # ── Detail panel ──
    def _show_detail(self, laporan: dict):
        self.selected_laporan = laporan
        for w in self.detail_frame.winfo_children():
            w.destroy()
        self.detail_frame.pack(fill="x", padx=30, pady=(12, 5))

        inner = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=18)

        # Header
        hdr = ctk.CTkFrame(inner, fg_color="transparent")
        hdr.pack(fill="x")

        ctk.CTkLabel(
            hdr, text=f"Detail Laporan  #{laporan['id']}",
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        ).pack(side="left")

        StatusBadge(hdr, status=laporan["status"]).pack(side="right")

        ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(
            fill="x", pady=(10, 12))

        # Info grid
        info_items = [
            ("Judul",       laporan.get("judul", "")),
            ("Kategori",    laporan.get("kategori", "")),
            ("Deskripsi",   laporan.get("deskripsi", "")),
            ("Lokasi",      f"{laporan.get('lokasi', '')} — Kel. {laporan.get('kelurahan', '')}, Kec. {laporan.get('kecamatan', '')}"),
            ("Tanggal",     format_tanggal(laporan.get("created_at"))),
        ]
        for label, value in info_items:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row, text=f"{label}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                width=85, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=value,
                font=ctk.CTkFont(size=12),
                anchor="w", wraplength=600
            ).pack(side="left", fill="x")

        # Timeline
        ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(
            fill="x", pady=(12, 10))

        ctk.CTkLabel(
            inner, text="📌  Timeline Status",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x", pady=(0, 6))

        riwayat = self.laporan_ctrl.get_riwayat_laporan(laporan["id"])
        tl_frame = ctk.CTkFrame(inner, fg_color="transparent")
        tl_frame.pack(fill="x")

        for j, rw in enumerate(riwayat):
            is_last = (j == len(riwayat) - 1)
            item = ctk.CTkFrame(tl_frame, fg_color="transparent")
            item.pack(fill="x")

            dot_f = ctk.CTkFrame(item, fg_color="transparent", width=30)
            dot_f.pack(side="left", anchor="n")
            dot_f.pack_propagate(False)

            dot_col = "#6C5CE7" if is_last else ("gray60", "gray50")
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

    # ══════════════════════════════════════════
    # PAGE 2 : BUAT LAPORAN  (Gambar referensi 2)
    # ══════════════════════════════════════════

    def _show_form_page(self):
        self._clear_content()
        self._load_data()
        c = self.content

        # ── Header ──
        header = ctk.CTkFrame(c, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 20))

        ctk.CTkLabel(
            header, text="Buat Laporan",
            font=ctk.CTkFont(size=24, weight="bold"), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Sampaikan keluhan atau aspirasi Anda kepada pemerintah",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60")
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
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            fi, text="Isi semua informasi di bawah, lalu klik tombol kirim",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 18))

        # ── Row 1 : 4 kolom ──
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

        # ── Row 2 : 2 kolom ──
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
            fg_color=("#6C5CE7", "#7C6CF7"),
            hover_color=("#5A4BD1", "#6B5BE6"),
            command=self._submit_form
        )
        self.submit_btn.pack(anchor="w", pady=(4, 0))

        # ── Riwayat Laporan Terbaru ──
        hist_card = ctk.CTkFrame(
            c, corner_radius=12,
            fg_color=("white", "gray17"),
            border_width=1, border_color=("gray88", "gray28")
        )
        hist_card.pack(fill="x", padx=30, pady=(0, 20))

        hi = ctk.CTkFrame(hist_card, fg_color="transparent")
        hi.pack(fill="x", padx=28, pady=20)

        ctk.CTkLabel(
            hi, text="Riwayat Laporan Terbaru",
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            hi, text="5 laporan terakhir yang Anda buat",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(anchor="w", pady=(2, 14))

        # Table header
        ht = ctk.CTkFrame(hi, fg_color=("gray94", "gray20"),
                          corner_radius=6, height=34)
        ht.pack(fill="x")
        ht.pack_propagate(False)

        hist_cols = [
            ("No. Laporan", 130), ("Judul", 200),
            ("Kategori", 160), ("Tanggal", 130), ("Status", 150),
        ]
        for label, w in hist_cols:
            ctk.CTkLabel(
                ht, text=label, width=w,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray45", "gray65"), anchor="w"
            ).pack(side="left", padx=(12, 4), pady=6)

        # Table rows (last 5)
        recent = self.all_laporan[:5]
        if not recent:
            ctk.CTkLabel(
                hi, text="Belum ada laporan.",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60")
            ).pack(pady=20)
        else:
            for lap in recent:
                rr = ctk.CTkFrame(hi, fg_color="transparent", height=40)
                rr.pack(fill="x", pady=1)
                rr.pack_propagate(False)

                ctk.CTkLabel(
                    rr, text=f"LP#{lap['id']:06d}",
                    width=130, font=ctk.CTkFont(size=12),
                    text_color=("#6C5CE7", "#7C6CF7"),
                    anchor="w"
                ).pack(side="left", padx=(12, 4), pady=6)

                ctk.CTkLabel(
                    rr, text=truncate_text(lap.get("judul", ""), 28),
                    width=200, font=ctk.CTkFont(size=12), anchor="w"
                ).pack(side="left", padx=4, pady=6)

                ctk.CTkLabel(
                    rr, text=truncate_text(lap.get("kategori", ""), 20),
                    width=160, font=ctk.CTkFont(size=12), anchor="w"
                ).pack(side="left", padx=4, pady=6)

                ctk.CTkLabel(
                    rr, text=format_tanggal(lap.get("created_at")),
                    width=130, font=ctk.CTkFont(size=12),
                    text_color=("gray50", "gray60"), anchor="w"
                ).pack(side="left", padx=4, pady=6)

                st_color = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
                st_label = ctk.CTkLabel(
                    rr, text=lap["status"],
                    width=150, font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=st_color, anchor="w"
                )
                st_label.pack(side="left", padx=4, pady=6)

                # Separator
                ctk.CTkFrame(hi, height=1,
                             fg_color=("gray90", "gray25")).pack(fill="x")

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
