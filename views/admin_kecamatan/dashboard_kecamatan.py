# views/admin_kecamatan/dashboard_kecamatan.py
# Dashboard untuk Admin Kecamatan — matching kelurahan style with detail page

import customtkinter as ctk
from views.components.confirmation_dialog import ConfirmationDialog, ResultDialog
from controllers.laporan_controller import LaporanController
from views.components.sidebar import Sidebar
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.wilayah import get_kelurahan_by_kecamatan
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
        # Default: hanya tampilkan laporan yang masuk ke Kecamatan (status Diproses Kecamatan)
        data = self.laporan_ctrl.get_laporan_kecamatan(self.kecamatan, "Diproses Kecamatan")

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
        self.status_filter_var = ctk.StringVar(value="Diproses Kecamatan")
        ctk.CTkComboBox(
            filter_bar, values=["Semua", "Diproses Kecamatan", "Diproses Kota", "Selesai", "Ditolak"],
            variable=self.status_filter_var,
            width=180, height=32, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._apply_filter(), state="readonly"
        ).pack(side="left")

        ctk.CTkLabel(filter_bar, text="Dari:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(15, 5))
        self.date_from_var = ctk.StringVar(value="")
        self.date_from_entry = ctk.CTkEntry(
            filter_bar, textvariable=self.date_from_var,
            width=110, height=32, corner_radius=8,
            placeholder_text="YYYY-MM-DD", font=ctk.CTkFont(size=11),
            state="readonly"
        )
        self.date_from_entry.pack(side="left", padx=(0, 2))
        ctk.CTkButton(
            filter_bar, text="📅", width=32, height=32, corner_radius=8,
            font=ctk.CTkFont(size=14), fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"), text_color=("gray30", "gray80"),
            command=lambda: self._show_date_picker(self.date_from_var)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(filter_bar, text="Sampai:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        self.date_to_var = ctk.StringVar(value="")
        self.date_to_entry = ctk.CTkEntry(
            filter_bar, textvariable=self.date_to_var,
            width=110, height=32, corner_radius=8,
            placeholder_text="YYYY-MM-DD", font=ctk.CTkFont(size=11),
            state="readonly"
        )
        self.date_to_entry.pack(side="left", padx=(0, 2))
        ctk.CTkButton(
            filter_bar, text="📅", width=32, height=32, corner_radius=8,
            font=ctk.CTkFont(size=14), fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"), text_color=("gray30", "gray80"),
            command=lambda: self._show_date_picker(self.date_to_var)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            filter_bar, text="🔍", width=36, height=32, corner_radius=8,
            font=ctk.CTkFont(size=14),
            fg_color=(TEAL, TEAL), hover_color=(NAVY, NAVY),
            command=lambda: self._apply_filter()
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            filter_bar, text="Reset", width=55, height=32, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            border_color=("gray72", "gray38"),
            text_color=("gray30", "gray80"),
            hover_color=("gray88", "gray25"),
            command=self._reset_filter
        ).pack(side="left")

        # ── Table ──
        self._all_data = data
        self._build_table(data)

    def _build_table(self, data):
        if hasattr(self, '_table_frame'):
            self._table_frame.destroy()

        self._table_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self._table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        th = ctk.CTkFrame(self._table_frame, fg_color=("gray94", "gray20"),
                          corner_radius=6, height=36)
        th.pack(fill="x")
        th.pack_propagate(False)

        cols = [("#", 40), ("Judul", 145), ("Pelapor", 100), ("Kelurahan", 100),
                ("Kategori", 100), ("Prioritas", 75), ("Status", 120), ("Duk.", 45), ("Tanggal", 100)]
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

            c0 = ctk.CTkFrame(rr, fg_color="transparent", width=40, height=40)
            c0.pack(side="left", padx=(8, 0))
            c0.pack_propagate(False)
            ctk.CTkLabel(c0, text=f"#{lap['id']}", font=ctk.CTkFont(size=12), text_color=(TEAL, SKY_BLUE), anchor="w").pack(side="left")

            c1 = ctk.CTkFrame(rr, fg_color="transparent", width=145, height=40)
            c1.pack(side="left", padx=(8, 0))
            c1.pack_propagate(False)
            ctk.CTkLabel(c1, text=truncate_text(lap.get("judul", ""), 18), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

            c2 = ctk.CTkFrame(rr, fg_color="transparent", width=100, height=40)
            c2.pack(side="left", padx=(8, 0))
            c2.pack_propagate(False)
            ctk.CTkLabel(c2, text=truncate_text(lap.get("nama_pelapor", ""), 12), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

            c3 = ctk.CTkFrame(rr, fg_color="transparent", width=100, height=40)
            c3.pack(side="left", padx=(8, 0))
            c3.pack_propagate(False)
            ctk.CTkLabel(c3, text=truncate_text(lap.get("kelurahan", ""), 12), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

            c4 = ctk.CTkFrame(rr, fg_color="transparent", width=100, height=40)
            c4.pack(side="left", padx=(8, 0))
            c4.pack_propagate(False)
            ctk.CTkLabel(c4, text=truncate_text(lap.get("kategori", ""), 12), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

            c5 = ctk.CTkFrame(rr, fg_color="transparent", width=75, height=40)
            c5.pack(side="left", padx=(8, 0))
            c5.pack_propagate(False)
            pri = lap.get("prioritas", "Rendah")
            pri_clr = PRIORITAS_COLORS.get(pri, "#66BB6A")
            pri_f = ctk.CTkFrame(c5, fg_color=pri_clr, corner_radius=4)
            pri_f.pack(side="left")
            ctk.CTkLabel(pri_f, text=pri, font=ctk.CTkFont(size=9, weight="bold"), text_color="white").pack(padx=4, pady=2)

            c6 = ctk.CTkFrame(rr, fg_color="transparent", width=120, height=40)
            c6.pack(side="left", padx=(8, 0))
            c6.pack_propagate(False)
            st_clr = STATUS_DOT_COLORS.get(lap["status"], "#95a5a6")
            ctk.CTkLabel(c6, text=f"● {lap['status']}", font=ctk.CTkFont(size=11), text_color=st_clr, anchor="w").pack(side="left")

            c7 = ctk.CTkFrame(rr, fg_color="transparent", width=45, height=40)
            c7.pack(side="left", padx=(8, 0))
            c7.pack_propagate(False)
            duk = lap.get("jumlah_dukungan", 0)
            ctk.CTkLabel(c7, text=f"👍 {duk}", font=ctk.CTkFont(size=11), text_color=(TEAL, SKY_BLUE), anchor="w").pack(side="left")

            c8 = ctk.CTkFrame(rr, fg_color="transparent", width=100, height=40)
            c8.pack(side="left", padx=(8, 0))
            c8.pack_propagate(False)
            ctk.CTkLabel(c8, text=format_tanggal(lap.get("created_at")), font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"), anchor="w").pack(side="left")

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
            # "Semua" = ambil seluruh laporan se-kecamatan
            data = self.laporan_ctrl.get_laporan_kecamatan(self.kecamatan)

        if kel and kel != "Semua":
            data = [d for d in data if d.get("kelurahan") == kel]

        # Apply date filter
        date_from = self.date_from_var.get().strip() if hasattr(self, 'date_from_var') else ""
        date_to = self.date_to_var.get().strip() if hasattr(self, 'date_to_var') else ""
        if date_from:
            data = [d for d in data if str(d.get("created_at", ""))[:10] >= date_from]
        if date_to:
            data = [d for d in data if str(d.get("created_at", ""))[:10] <= date_to]

        self._build_table(data)

    def _reset_filter(self):
        self.kel_filter_var.set("Semua")
        self.status_filter_var.set("Semua")
        if hasattr(self, 'date_from_var'):
            self.date_from_var.set("")
        if hasattr(self, 'date_to_var'):
            self.date_to_var.set("")
        self._apply_filter()

    def _show_date_picker(self, target_var):
        """Show a date picker popup using tkcalendar."""
        try:
            from tkcalendar import Calendar
        except ImportError:
            return
        
        picker = ctk.CTkToplevel(self)
        picker.title("Pilih Tanggal")
        picker.geometry("300x300")
        picker.resizable(False, False)
        picker.configure(fg_color=("white", "gray17"))
        
        picker.update_idletasks()
        x = (picker.winfo_screenwidth() // 2) - 150
        y = (picker.winfo_screenheight() // 2) - 150
        picker.geometry(f"+{x}+{y}")
        
        picker.transient(self.winfo_toplevel())
        picker.grab_set()
        
        import datetime
        today = datetime.date.today()
        
        cal = Calendar(
            picker, selectmode='day',
            year=today.year, month=today.month, day=today.day,
            date_pattern='yyyy-mm-dd'
        )
        cal.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        def pick():
            target_var.set(cal.get_date())
            picker.grab_release()
            picker.destroy()
            self._apply_filter()
        
        ctk.CTkButton(
            picker, text="Pilih", height=34, corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=(TEAL, TEAL), hover_color=(NAVY, NAVY),
            command=pick
        ).pack(fill="x", padx=10, pady=(0, 10))
        
        picker.protocol("WM_DELETE_WINDOW", lambda: (picker.grab_release(), picker.destroy()))

    # ══════════════════════════════════════════
    # DETAIL PAGE  (Warga-style)
    # ══════════════════════════════════════════

    def _show_detail_page(self, laporan: dict):
        """Halaman detail laporan — invoice style."""
        from views.components.detail_invoice import build_detail_header, build_detail_card
        self._clear()
        c = self.content
        self.selected_laporan = laporan

        # ── Invoice-style Header ──
        build_detail_header(
            c, laporan, back_command=self._show_main,
            title="Detail Laporan",
            breadcrumb="Dashboard Kecamatan  ›  Detail"
        )

        # ── Invoice-style Main Card ──
        build_detail_card(c, laporan)

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

        # Tentukan apakah laporan masih bisa diaksi oleh Kecamatan
        ACTIONABLE_STATUSES = {"Diproses Kecamatan"}
        status_saat_ini = laporan.get("status", "")
        is_actionable = status_saat_ini in ACTIONABLE_STATUSES

        if not is_actionable:
            # ── READ-ONLY NOTICE ──
            notice_bg = ("#FFF8E1", "#3E2E00")
            notice_border = ("#FFD54F", "#B8860B")
            notice = ctk.CTkFrame(af, fg_color=notice_bg, corner_radius=8,
                                  border_width=1, border_color=notice_border)
            notice.pack(fill="x", pady=(0, 6))
            status_labels = {
                "Diproses Kota": "diteruskan ke Kota",
                "Selesai":       "dinyatakan Selesai",
                "Ditolak":       "ditolak",
            }
            keterangan = status_labels.get(status_saat_ini, f"berstatus '{status_saat_ini}'")
            ctk.CTkLabel(
                notice,
                text=f"⚠️  Laporan ini sudah {keterangan}. Tidak dapat diubah dari level Kecamatan.",
                font=ctk.CTkFont(size=12),
                text_color=("#795548", "#FFD54F"),
                wraplength=700, anchor="w", justify="left"
            ).pack(padx=14, pady=10)
        else:
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

            # Lampiran foto opsional
            foto_row = ctk.CTkFrame(af, fg_color="transparent")
            foto_row.pack(fill="x", pady=(10, 10))
            ctk.CTkLabel(foto_row, text="Foto Selesai (Opsional)",
                         font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=(0, 10))
            
            self.admin_foto_path = None
            self.lbl_admin_foto = ctk.CTkLabel(
                foto_row, text="Tidak ada file",
                font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")
            )
            ctk.CTkButton(
                foto_row, text="Pilih Foto", height=28, width=80, corner_radius=6,
                font=ctk.CTkFont(size=11), fg_color=("gray85", "gray25"), text_color=("gray20", "gray85"),
                command=self._pilih_foto_admin
            ).pack(side="left", padx=(0, 10))
            self.lbl_admin_foto.pack(side="left")

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
        
        action_labels = {
            'Diproses Kecamatan': 'memproses laporan ini di tingkat Kecamatan',
            'Selesai': 'menandai laporan ini sebagai SELESAI',
            'Ditolak': 'MENOLAK laporan ini',
            'Diproses Kota': 'mengeskalasi laporan ini ke tingkat Kota',
        }
        action_icons = {
            'Diproses Kecamatan': '🔄',
            'Selesai': '✅',
            'Ditolak': '❌',
            'Diproses Kota': '⬆️',
        }
        action_colors = {
            'Diproses Kecamatan': '#1E88E5',
            'Selesai': '#43A047',
            'Ditolak': '#E53935',
            'Diproses Kota': '#7B1FA2',
        }
        
        label = action_labels.get(status_baru, status_baru)
        icon = action_icons.get(status_baru, '⚡')
        color = action_colors.get(status_baru, '#1E88E5')
        
        def do_action():
            catatan = self.catatan_text.get("1.0", "end-1c")
            prioritas = self.prioritas_var.get() if hasattr(self, 'prioritas_var') else None
            result = self.laporan_ctrl.proses_laporan(
                laporan_id=self.selected_laporan["id"],
                admin_id=self.app.current_user["id"],
                status_baru=status_baru, catatan=catatan,
                prioritas=prioritas,
                foto_selesai_path=self.admin_foto_path
            )
            if result["success"]:
                ResultDialog(self, success=True, message=result["message"],
                             on_close=self._show_main)
            else:
                ResultDialog(self, success=False, message=result["message"])
        
        ConfirmationDialog(
            self,
            title="Konfirmasi Tindakan",
            message=f"Apakah Anda yakin ingin {label}?",
            icon_text=icon,
            confirm_text="Ya, Lanjutkan",
            confirm_color=color,
            on_confirm=do_action
        )

    def _pilih_foto_admin(self):
        import tkinter.filedialog as fd
        import os
        filepath = fd.askopenfilename(
            title="Pilih Lampiran Foto",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if filepath:
            self.admin_foto_path = filepath
            filename = os.path.basename(filepath)
            from utils.helpers import truncate_text
            self.lbl_admin_foto.configure(text=truncate_text(filename, 20), text_color=("black", "white"))
