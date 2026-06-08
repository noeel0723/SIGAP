"""
Invoice-style Detail Laporan — shared layout builder.

Reusable by Admin Kota, Kecamatan, Kelurahan, and Warga dashboards.
This module builds:
  1. Header row  (← Kembali + title + breadcrumb + badge buttons)
  2. Main card   (top banner, two-column info, detail table, notes)

It does NOT build the Timeline or Action cards — those are dashboard-specific.
"""
import customtkinter as ctk
from views.components.status_badge import StatusBadge
from utils.helpers import format_tanggal, truncate_text
from config.settings import PRIORITAS_COLORS

# ── Palette ──
ACCENT      = "#2563EB"
NAVY        = "#1B2A4A"
SKY_BLUE    = "#87CEEB"
TEAL        = "#0D9488"
SECTION_CLR = "#2563EB"  # section header color


def build_detail_header(parent, laporan: dict, back_command,
                         title="Detail Laporan", breadcrumb=""):
    """Build the top header: ← Kembali | Title | Breadcrumb | Badges."""
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=30, pady=(25, 8))

    # Back button
    ctk.CTkButton(
        header, text="←  Kembali", height=34, corner_radius=8, width=120,
        font=ctk.CTkFont(size=13), fg_color="transparent",
        border_width=1, border_color=("gray72", "gray38"),
        text_color=("gray30", "gray80"),
        hover_color=("gray88", "gray25"),
        command=back_command
    ).pack(side="left")

    # Title + breadcrumb stack
    title_f = ctk.CTkFrame(header, fg_color="transparent")
    title_f.pack(side="left", padx=(16, 0))
    ctk.CTkLabel(title_f, text=title,
                 font=ctk.CTkFont(size=22, weight="bold"),
                 anchor="w").pack(anchor="w")
    if breadcrumb:
        ctk.CTkLabel(title_f, text=breadcrumb,
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60"), anchor="w"
                     ).pack(anchor="w")

    # Badges on the right
    badges_f = ctk.CTkFrame(header, fg_color="transparent")
    badges_f.pack(side="right")

    # Status pill
    StatusBadge(badges_f, status=laporan["status"]).pack(side="left", padx=(0, 6))

    # Prioritas pill
    pri = laporan.get("prioritas", "Rendah")
    pri_clr = PRIORITAS_COLORS.get(pri, "#66BB6A")
    pri_badge = ctk.CTkFrame(badges_f, fg_color=pri_clr, corner_radius=6)
    pri_badge.pack(side="left", padx=(0, 6))
    ctk.CTkLabel(pri_badge, text=f"⚡ {pri}",
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color="white").pack(padx=10, pady=3)

    # Dukungan count
    duk = laporan.get("jumlah_dukungan", 0)
    if duk > 0:
        duk_badge = ctk.CTkFrame(badges_f, fg_color=(ACCENT, ACCENT), corner_radius=6)
        duk_badge.pack(side="left")
        ctk.CTkLabel(duk_badge, text=f"👍 {duk}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="white").pack(padx=10, pady=3)

    return header


def build_detail_card(parent, laporan: dict, pelapor_display: str | None = None):
    """
    Build the main invoice-style card.
    Returns the card frame (so caller can add more below if needed).
    """
    card = ctk.CTkFrame(parent, corner_radius=14,
                        fg_color=("white", "gray17"),
                        border_width=1, border_color=("gray88", "gray28"))
    card.pack(fill="x", padx=30, pady=(10, 15))

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=30, pady=28)

    # ════════════════════════════════════
    # TOP BANNER:  "SIGAP" left  |  ID + status right
    # ════════════════════════════════════
    banner = ctk.CTkFrame(inner, fg_color="transparent")
    banner.pack(fill="x", pady=(0, 16))

    # Left: branding
    ctk.CTkLabel(banner, text="📋  SIGAP",
                 font=ctk.CTkFont(size=20, weight="bold"),
                 text_color=(NAVY, SKY_BLUE), anchor="w").pack(side="left")

    # Right: ID + status pill
    right_top = ctk.CTkFrame(banner, fg_color="transparent")
    right_top.pack(side="right")

    # Status pill
    st = laporan.get("status", "Menunggu")
    _pill_colors = {
        "Menunggu":           ("#FFF3E0", "#E65100"),
        "Diproses Kelurahan": ("#E3F2FD", "#1565C0"),
        "Diproses Kecamatan": ("#F3E5F5", "#7B1FA2"),
        "Diproses Kota":      ("#FBE9E7", "#D84315"),
        "Selesai":            ("#E8F5E9", "#2E7D32"),
        "Ditolak":            ("#FFEBEE", "#C62828"),
    }
    _pill_dark = {
        "Menunggu":           ("#3E2700", "#FFB74D"),
        "Diproses Kelurahan": ("#0D2137", "#64B5F6"),
        "Diproses Kecamatan": ("#2A0E3A", "#CE93D8"),
        "Diproses Kota":      ("#3E1400", "#FF8A65"),
        "Selesai":            ("#0E2E13", "#66BB6A"),
        "Ditolak":            ("#3E0000", "#EF5350"),
    }
    pl = _pill_colors.get(st, ("#F5F5F5", "#616161"))
    pd = _pill_dark.get(st, ("#333", "#BBB"))
    pill = ctk.CTkFrame(right_top, fg_color=(pl[0], pd[0]), corner_radius=6)
    pill.pack(side="left", padx=(0, 12))
    ctk.CTkLabel(pill, text=st, font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=(pl[1], pd[1])).pack(padx=10, pady=3)

    ctk.CTkLabel(right_top, text=f"LP{laporan['id']:06d}",
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=(NAVY, "gray80")).pack(side="left")

    # Thin separator
    ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(fill="x", pady=(0, 18))

    # ════════════════════════════════════
    # TWO-COLUMN INFO:  DATA PELAPOR  |  LOKASI LAPORAN
    # ════════════════════════════════════
    info_row = ctk.CTkFrame(inner, fg_color="transparent")
    info_row.pack(fill="x", pady=(0, 18))
    info_row.grid_columnconfigure(0, weight=1)
    info_row.grid_columnconfigure(1, weight=1)

    # ── Left: DATA PELAPOR ──
    left = ctk.CTkFrame(info_row, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 24))

    ctk.CTkLabel(left, text="DATA PELAPOR",
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=(SECTION_CLR, "#64B5F6"), anchor="w"
                 ).pack(anchor="w", pady=(0, 10))

    if pelapor_display is None:
        pelapor_display = laporan.get("nama_pelapor", "")

    left_items = [
        ("Kategori", laporan.get("kategori", "")),
        ("Prioritas", laporan.get("prioritas", "Rendah")),
        ("Dibuat", format_tanggal(laporan.get("created_at"))),
    ]

    # Pelapor name (bold, standalone)
    ctk.CTkLabel(left, text=pelapor_display,
                 font=ctk.CTkFont(size=13, weight="bold"),
                 anchor="w").pack(anchor="w")

    for lbl, val in left_items:
        rf = ctk.CTkFrame(left, fg_color="transparent")
        rf.pack(fill="x", pady=1)
        ctk.CTkLabel(rf, text=f"{lbl}:", width=80,
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60"), anchor="w").pack(side="left")
        ctk.CTkLabel(rf, text=val, font=ctk.CTkFont(size=11),
                     anchor="w").pack(side="left")

    # ── Right: LOKASI LAPORAN ──
    right = ctk.CTkFrame(info_row, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    ctk.CTkLabel(right, text="LOKASI LAPORAN",
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=(SECTION_CLR, "#64B5F6"), anchor="w"
                 ).pack(anchor="w", pady=(0, 10))

    right_items = [
        ("Lokasi", laporan.get("lokasi", "")),
        ("Kelurahan", laporan.get("kelurahan", "")),
        ("Kecamatan", laporan.get("kecamatan", "")),
        ("Diperbarui", format_tanggal(laporan.get("updated_at",
                                                    laporan.get("created_at")))),
    ]
    for lbl, val in right_items:
        rf = ctk.CTkFrame(right, fg_color="transparent")
        rf.pack(fill="x", pady=1)
        ctk.CTkLabel(rf, text=f"{lbl}:", width=90,
                     font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60"), anchor="w").pack(side="left")
        ctk.CTkLabel(rf, text=val, font=ctk.CTkFont(size=11),
                     anchor="w", wraplength=280).pack(side="left")

    # ════════════════════════════════════
    # DETAIL TABLE:  #  |  Field  |  Detail
    # ════════════════════════════════════
    ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(fill="x", pady=(0, 14))

    # Table header
    th = ctk.CTkFrame(inner, fg_color="transparent", height=32)
    th.pack(fill="x")
    th.pack_propagate(False)
    for col_lbl, w in [("#", 40), ("Deskripsi", 350), ("Detail", 260)]:
        ctk.CTkLabel(th, text=col_lbl, width=w,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=("gray50", "gray60"), anchor="w"
                     ).pack(side="left", padx=(14, 0))

    ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(fill="x", pady=(4, 0))

    # Table rows
    detail_rows = [
        ("Judul Laporan", laporan.get("judul", "")),
        ("Kategori", laporan.get("kategori", "")),
        ("Alamat Lokasi",
         f"{laporan.get('lokasi', '')} — Kel. {laporan.get('kelurahan', '')}, "
         f"Kec. {laporan.get('kecamatan', '')}"),
        ("Status Saat Ini", laporan.get("status", "")),
    ]
    for i, (field, value) in enumerate(detail_rows):
        row_bg = ("white", "gray17") if i % 2 == 0 else ("gray98", "gray15")
        tr = ctk.CTkFrame(inner, fg_color=row_bg, height=44, corner_radius=4)
        tr.pack(fill="x", pady=1)
        tr.pack_propagate(False)
        ctk.CTkLabel(tr, text=str(i + 1), width=40,
                     font=ctk.CTkFont(size=12),
                     text_color=("gray45", "gray60"), anchor="w"
                     ).pack(side="left", padx=(14, 0))
        ctk.CTkLabel(tr, text=field, width=350,
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
                     ).pack(side="left", padx=(14, 0))
        ctk.CTkLabel(tr, text=value, font=ctk.CTkFont(size=12),
                     anchor="w", wraplength=240
                     ).pack(side="left", padx=(14, 0))

    # ════════════════════════════════════
    # BOTTOM: Separator + Deskripsi as NOTES
    # ════════════════════════════════════
    ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(fill="x", pady=(14, 14))

    notes_row = ctk.CTkFrame(inner, fg_color="transparent")
    notes_row.pack(fill="x")

    # Left: DESKRIPSI
    notes_left = ctk.CTkFrame(notes_row, fg_color="transparent")
    notes_left.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(notes_left, text="DESKRIPSI",
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=(SECTION_CLR, "#64B5F6"), anchor="w"
                 ).pack(anchor="w", pady=(0, 4))

    desc = laporan.get("deskripsi", "")
    ctk.CTkLabel(notes_left, text=desc if desc else "Tidak ada deskripsi.",
                 font=ctk.CTkFont(size=11),
                 text_color=("gray40", "gray65"),
                 anchor="w", justify="left", wraplength=600
                 ).pack(anchor="w")

    # Right: ticket info
    notes_right = ctk.CTkFrame(notes_row, fg_color="transparent")
    notes_right.pack(side="right")

    ctk.CTkLabel(notes_right, text="Ticket ID",
                 font=ctk.CTkFont(size=10),
                 text_color=("gray50", "gray60"), anchor="e"
                 ).pack(anchor="e")
    ctk.CTkLabel(notes_right, text=f"#LP{laporan['id']:06d}",
                 font=ctk.CTkFont(size=12, weight="bold"),
                 text_color=(NAVY, SKY_BLUE), anchor="e"
                 ).pack(anchor="e")

    # ════════════════════════════════════
    # LAMPIRAN FOTO
    # ════════════════════════════════════
    foto_laporan = laporan.get("foto_laporan")
    foto_selesai = laporan.get("foto_selesai")

    if foto_laporan or foto_selesai:
        ctk.CTkFrame(inner, height=1, fg_color=("gray85", "gray28")).pack(fill="x", pady=(14, 14))
        
        foto_header = ctk.CTkFrame(inner, fg_color="transparent")
        foto_header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(foto_header, text="LAMPIRAN FOTO",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=(SECTION_CLR, "#64B5F6"), anchor="w").pack(anchor="w")

        foto_row_disp = ctk.CTkFrame(inner, fg_color="transparent")
        foto_row_disp.pack(fill="x")

        import os
        from PIL import Image

        def load_img(path, title):
            if path and os.path.exists(path):
                f = ctk.CTkFrame(foto_row_disp, fg_color="transparent")
                f.pack(side="left", padx=(0, 20))
                ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 5))
                try:
                    pil_img = Image.open(path)
                    # Resize proportionally to fit in max width 250
                    w, h = pil_img.size
                    max_w = 250
                    new_h = int((max_w / w) * h)
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(max_w, new_h))
                    lbl = ctk.CTkLabel(f, text="", image=ctk_img)
                    lbl.image = ctk_img  # Keep reference
                    lbl.pack(anchor="w")
                except Exception as e:
                    ctk.CTkLabel(f, text="[Gagal memuat gambar]").pack(anchor="w")

        if foto_laporan:
            load_img(foto_laporan, "Foto Laporan (Warga)")
        if foto_selesai:
            load_img(foto_selesai, "Foto Selesai (Admin)")

    return card
