# views/components/data_table.py
# Komponen tabel data kustom

import customtkinter as ctk
from utils.helpers import truncate_text, format_tanggal
from datetime import datetime


class DataTable(ctk.CTkFrame):
    """Tabel data scrollable dengan header, zebra stripe, dan klik handler."""

    def __init__(self, parent, columns: list[dict], on_row_click=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.columns = columns
        self.on_row_click = on_row_click
        self.rows_data = []
        self.row_frames = []
        self.selected_index = -1

        # ── Header ──
        self.header_frame = ctk.CTkFrame(self, fg_color=("gray82", "gray22"),
                                         corner_radius=8, height=40)
        self.header_frame.pack(fill="x", padx=2, pady=(0, 2))
        self.header_frame.pack_propagate(False)

        for i, col in enumerate(columns):
            lbl = ctk.CTkLabel(
                self.header_frame,
                text=col["label"],
                font=ctk.CTkFont(size=12, weight="bold"),
                width=col.get("width", 120),
                anchor="w"
            )
            lbl.pack(side="left", padx=(15 if i == 0 else 8, 8), pady=8)

        # ── Scrollable Body ──
        self.body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=("gray75", "gray30")
        )
        self.body.pack(fill="both", expand=True, padx=2)

    def set_data(self, data: list[dict]):
        """Populate tabel dengan data baru."""
        self.clear()
        self.rows_data = data

        for idx, row_data in enumerate(data):
            is_even = idx % 2 == 0
            bg = ("gray95", "gray18") if is_even else ("gray90", "gray16")

            row_frame = ctk.CTkFrame(self.body, fg_color=bg,
                                     corner_radius=6, height=38)
            row_frame.pack(fill="x", pady=1)
            row_frame.pack_propagate(False)

            for i, col in enumerate(self.columns):
                key = col["key"]
                value = row_data.get(key, "")

                # Format datetime
                if isinstance(value, datetime):
                    value = format_tanggal(value)

                # Truncate long text
                max_len = col.get("max_len", 40)
                display = truncate_text(str(value), max_len)

                lbl = ctk.CTkLabel(
                    row_frame,
                    text=display,
                    font=ctk.CTkFont(size=12),
                    width=col.get("width", 120),
                    anchor="w"
                )
                lbl.pack(side="left", padx=(15 if i == 0 else 8, 8), pady=6)
                lbl.bind("<Button-1>", lambda e, d=row_data, ix=idx: self._on_click(d, ix))

            row_frame.bind("<Button-1>", lambda e, d=row_data, ix=idx: self._on_click(d, ix))

            # Hover effect
            row_frame.bind("<Enter>", lambda e, f=row_frame: f.configure(
                fg_color=("gray85", "gray25")))
            row_frame.bind("<Leave>", lambda e, f=row_frame, b=bg: f.configure(
                fg_color=b))

            self.row_frames.append(row_frame)

    def _on_click(self, row_data: dict, index: int):
        """Handle klik pada baris."""
        # Highlight baris terpilih
        for i, frame in enumerate(self.row_frames):
            if i == index:
                frame.configure(fg_color=("#BBDEFB", "#1A237E"))
            else:
                bg = ("gray95", "gray18") if i % 2 == 0 else ("gray90", "gray16")
                frame.configure(fg_color=bg)

        self.selected_index = index
        if self.on_row_click:
            self.on_row_click(row_data)

    def clear(self):
        """Hapus semua baris."""
        for widget in self.body.winfo_children():
            widget.destroy()
        self.row_frames = []
        self.rows_data = []
        self.selected_index = -1

    def get_selected(self) -> dict | None:
        """Ambil data baris yang sedang terpilih."""
        if 0 <= self.selected_index < len(self.rows_data):
            return self.rows_data[self.selected_index]
        return None
