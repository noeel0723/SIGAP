# models/laporan_model.py
# Model untuk operasi CRUD tabel laporan & riwayat_status

"""
Modul data access layer untuk entitas Laporan dan Riwayat Status.
Menangani CRUD laporan, perubahan status, eskalasi, dukungan (upvote),
klasifikasi prioritas, dan query berdasarkan scope.
"""

from config.database import DatabaseConnection


class LaporanModel:
    """Data Access Object untuk tabel laporan, riwayat_status, dan dukungan_laporan."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    # ──────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────

    def create(self, user_id: int, judul: str, kategori: str,
               deskripsi: str, lokasi: str, kelurahan: str,
               kecamatan: str, is_anonymous: bool = False,
               prioritas: str = "Rendah") -> int:
        """
        Buat laporan baru dari Warga. Status default: 'Menunggu'.
        Returns: ID laporan yang baru dibuat.
        """
        laporan_id = self.db.execute(
            """INSERT INTO laporan 
               (user_id, judul, kategori, deskripsi, lokasi, kelurahan, kecamatan,
                is_anonymous, prioritas)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, judul, kategori, deskripsi, lokasi, kelurahan, kecamatan,
             1 if is_anonymous else 0, prioritas)
        )
        
        # Catat di riwayat status
        self.db.execute(
            """INSERT INTO riwayat_status 
               (laporan_id, admin_id, status_lama, status_baru, catatan_admin)
               VALUES (%s, NULL, '', 'Menunggu', 'Laporan baru dibuat oleh warga.')""",
            (laporan_id,)
        )
        
        return laporan_id

    # ──────────────────────────────────────
    # UPDATE STATUS (WORKFLOW ESKALASI)
    # ──────────────────────────────────────

    def update_status(self, laporan_id: int, admin_id: int,
                      status_baru: str, catatan: str) -> int:
        """
        Ubah status laporan dan catat riwayatnya.
        Digunakan oleh admin untuk memproses/eskalasi/menyelesaikan laporan.
        """
        # Ambil status lama
        laporan = self.get_by_id(laporan_id)
        if laporan is None:
            raise ValueError(f"Laporan ID {laporan_id} tidak ditemukan.")
        
        status_lama = laporan["status"]
        
        # Update status di tabel laporan
        self.db.execute(
            "UPDATE laporan SET status = %s WHERE id = %s",
            (status_baru, laporan_id)
        )
        
        # Catat di riwayat
        self.db.execute(
            """INSERT INTO riwayat_status 
               (laporan_id, admin_id, status_lama, status_baru, catatan_admin)
               VALUES (%s, %s, %s, %s, %s)""",
            (laporan_id, admin_id, status_lama, status_baru, catatan)
        )
        
        return laporan_id

    def update_prioritas(self, laporan_id: int, prioritas: str) -> int:
        """Update prioritas laporan (ditentukan oleh admin)."""
        return self.db.execute(
            "UPDATE laporan SET prioritas = %s WHERE id = %s",
            (prioritas, laporan_id)
        )

    # ──────────────────────────────────────
    # QUERY: BERDASARKAN SCOPE
    # ──────────────────────────────────────

    def get_by_id(self, laporan_id: int) -> dict | None:
        """Ambil detail satu laporan berdasarkan ID."""
        return self.db.fetch_one(
            """SELECT l.*, u.nama_lengkap AS nama_pelapor, u.email AS email_pelapor,
                      (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
               FROM laporan l
               JOIN users u ON l.user_id = u.id
               WHERE l.id = %s""",
            (laporan_id,)
        )

    def get_by_user(self, user_id: int) -> list[dict]:
        """Ambil semua laporan milik seorang warga (untuk tracking)."""
        return self.db.fetch_all(
            """SELECT l.*,
                      (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
               FROM laporan l
               WHERE l.user_id = %s 
               ORDER BY l.created_at DESC""",
            (user_id,)
        )

    def get_by_kelurahan(self, kelurahan: str, status: str = None) -> list[dict]:
        """Ambil laporan berdasarkan kelurahan (scope Admin Kelurahan)."""
        if status:
            return self.db.fetch_all(
                """SELECT l.*,
                          CASE WHEN l.is_anonymous = 1 THEN 'Anonim' ELSE u.nama_lengkap END AS nama_pelapor,
                          (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
                   FROM laporan l JOIN users u ON l.user_id = u.id
                   WHERE l.kelurahan = %s AND l.status = %s
                   ORDER BY l.created_at DESC""",
                (kelurahan, status)
            )
        return self.db.fetch_all(
            """SELECT l.*,
                      CASE WHEN l.is_anonymous = 1 THEN 'Anonim' ELSE u.nama_lengkap END AS nama_pelapor,
                      (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
               FROM laporan l JOIN users u ON l.user_id = u.id
               WHERE l.kelurahan = %s
               ORDER BY l.created_at DESC""",
            (kelurahan,)
        )

    def get_by_kecamatan(self, kecamatan: str, status: str = None) -> list[dict]:
        """Ambil laporan berdasarkan kecamatan (scope Admin Kecamatan)."""
        if status:
            return self.db.fetch_all(
                """SELECT l.*,
                          CASE WHEN l.is_anonymous = 1 THEN 'Anonim' ELSE u.nama_lengkap END AS nama_pelapor,
                          (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
                   FROM laporan l JOIN users u ON l.user_id = u.id
                   WHERE l.kecamatan = %s AND l.status = %s
                   ORDER BY l.created_at DESC""",
                (kecamatan, status)
            )
        return self.db.fetch_all(
            """SELECT l.*,
                      CASE WHEN l.is_anonymous = 1 THEN 'Anonim' ELSE u.nama_lengkap END AS nama_pelapor,
                      (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
               FROM laporan l JOIN users u ON l.user_id = u.id
               WHERE l.kecamatan = %s
               ORDER BY l.created_at DESC""",
            (kecamatan,)
        )

    def get_all(self, status: str = None) -> list[dict]:
        """
        Ambil semua laporan se-kota (scope Admin Kota).
        Admin Kota bisa melihat identitas asli pelapor, tapi ditandai jika anonim.
        """
        if status:
            return self.db.fetch_all(
                """SELECT l.*, u.nama_lengkap AS nama_pelapor,
                          (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
                   FROM laporan l JOIN users u ON l.user_id = u.id
                   WHERE l.status = %s
                   ORDER BY l.created_at DESC""",
                (status,)
            )
        return self.db.fetch_all(
            """SELECT l.*, u.nama_lengkap AS nama_pelapor,
                      (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
               FROM laporan l JOIN users u ON l.user_id = u.id
               ORDER BY l.created_at DESC"""
        )

    # ──────────────────────────────────────
    # RIWAYAT STATUS (TRACKING)
    # ──────────────────────────────────────

    def get_riwayat(self, laporan_id: int) -> list[dict]:
        """Ambil riwayat perubahan status sebuah laporan (untuk timeline tracking)."""
        return self.db.fetch_all(
            """SELECT rs.*, u.nama_lengkap AS nama_admin
               FROM riwayat_status rs
               LEFT JOIN users u ON rs.admin_id = u.id
               WHERE rs.laporan_id = %s
               ORDER BY rs.created_at ASC""",
            (laporan_id,)
        )

    # ──────────────────────────────────────
    # DUKUNGAN / UPVOTE
    # ──────────────────────────────────────

    def toggle_dukungan(self, laporan_id: int, user_id: int) -> bool:
        """
        Toggle dukungan: jika belum mendukung → insert, jika sudah → delete.
        Returns: True jika sekarang mendukung, False jika dukungan dicabut.
        """
        existing = self.db.fetch_one(
            "SELECT id FROM dukungan_laporan WHERE laporan_id = %s AND user_id = %s",
            (laporan_id, user_id)
        )
        
        if existing:
            self.db.execute(
                "DELETE FROM dukungan_laporan WHERE laporan_id = %s AND user_id = %s",
                (laporan_id, user_id)
            )
            return False
        else:
            self.db.execute(
                "INSERT INTO dukungan_laporan (laporan_id, user_id) VALUES (%s, %s)",
                (laporan_id, user_id)
            )
            return True

    def count_dukungan(self, laporan_id: int) -> int:
        """Hitung total dukungan untuk sebuah laporan."""
        result = self.db.fetch_one(
            "SELECT COUNT(*) AS total FROM dukungan_laporan WHERE laporan_id = %s",
            (laporan_id,)
        )
        return result["total"] if result else 0

    def has_user_dukungan(self, laporan_id: int, user_id: int) -> bool:
        """Cek apakah user sudah mendukung laporan tertentu."""
        result = self.db.fetch_one(
            "SELECT id FROM dukungan_laporan WHERE laporan_id = %s AND user_id = %s",
            (laporan_id, user_id)
        )
        return result is not None

    # ──────────────────────────────────────
    # LAPORAN PUBLIK (ASPIRASI SEKITAR)
    # ──────────────────────────────────────

    def get_laporan_publik(self, kelurahan: str, exclude_user_id: int = None) -> list[dict]:
        """
        Ambil laporan publik aktif (bukan Selesai/Ditolak) di kelurahan tertentu.
        Diurutkan berdasarkan jumlah dukungan terbanyak.
        Nama pelapor di-anonymize jika is_anonymous = 1.
        """
        query = """
            SELECT l.*,
                   CASE WHEN l.is_anonymous = 1 THEN 'Anonim' ELSE u.nama_lengkap END AS nama_pelapor,
                   (SELECT COUNT(*) FROM dukungan_laporan dl WHERE dl.laporan_id = l.id) AS jumlah_dukungan
            FROM laporan l
            JOIN users u ON l.user_id = u.id
            WHERE l.kelurahan = %s
              AND l.status NOT IN ('Selesai', 'Ditolak')
            ORDER BY jumlah_dukungan DESC, l.created_at DESC
        """
        return self.db.fetch_all(query, (kelurahan,))

    # ──────────────────────────────────────
    # STATISTIK (UNTUK DASHBOARD ADMIN KOTA)
    # ──────────────────────────────────────

    def get_statistik_per_status(self) -> list[dict]:
        """Hitung jumlah laporan per status (untuk pie chart)."""
        return self.db.fetch_all(
            """SELECT status, COUNT(*) AS jumlah 
               FROM laporan GROUP BY status"""
        )

    def get_statistik_per_kategori(self) -> list[dict]:
        """Hitung jumlah laporan per kategori (untuk bar chart)."""
        return self.db.fetch_all(
            """SELECT kategori, COUNT(*) AS jumlah 
               FROM laporan GROUP BY kategori ORDER BY jumlah DESC"""
        )

    def get_statistik_per_kecamatan(self) -> list[dict]:
        """Hitung jumlah laporan per kecamatan (untuk bar chart)."""
        return self.db.fetch_all(
            """SELECT kecamatan, COUNT(*) AS jumlah 
               FROM laporan GROUP BY kecamatan ORDER BY jumlah DESC"""
        )

    def get_statistik_bulanan(self, tahun: int = None) -> list[dict]:
        """Hitung jumlah laporan per bulan di tahun tertentu."""
        if tahun is None:
            return self.db.fetch_all(
                """SELECT MONTH(created_at) AS bulan, COUNT(*) AS jumlah
                   FROM laporan 
                   GROUP BY MONTH(created_at)
                   ORDER BY bulan"""
            )
        return self.db.fetch_all(
            """SELECT MONTH(created_at) AS bulan, COUNT(*) AS jumlah
               FROM laporan 
               WHERE YEAR(created_at) = %s
               GROUP BY MONTH(created_at)
               ORDER BY bulan""",
            (tahun,)
        )
