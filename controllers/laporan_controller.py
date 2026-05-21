# controllers/laporan_controller.py
# Controller untuk logika manajemen laporan dan eskalasi

"""
Controller laporan yang menangani pembuatan laporan, perubahan status,
workflow eskalasi, dan pengambilan data sesuai scope admin.
"""

from models.laporan_model import LaporanModel
from config.database import DatabaseConnection
from config.wilayah import get_kecamatan_by_kelurahan


class LaporanController:
    """Controller untuk operasi manajemen laporan."""

    def __init__(self, db: DatabaseConnection):
        self.laporan_model = LaporanModel(db)
    
    # ──────────────────────────────────────
    # WARGA: BUAT LAPORAN
    # ──────────────────────────────────────

    def buat_laporan(self, user_id: int, judul: str, kategori: str,
                     deskripsi: str, lokasi: str, kelurahan: str) -> dict:
        """
        Buat laporan baru dari Warga.
        Kecamatan otomatis diisi berdasarkan kelurahan yang dipilih.
        """
        # Validasi input
        if not judul or not judul.strip():
            return {"success": False, "message": "Judul laporan wajib diisi."}
        if not kategori:
            return {"success": False, "message": "Kategori wajib dipilih."}
        if not deskripsi or not deskripsi.strip():
            return {"success": False, "message": "Deskripsi wajib diisi."}
        if not lokasi or not lokasi.strip():
            return {"success": False, "message": "Lokasi wajib diisi."}
        if not kelurahan:
            return {"success": False, "message": "Kelurahan wajib dipilih."}
        
        # Tentukan kecamatan dari kelurahan
        kecamatan = get_kecamatan_by_kelurahan(kelurahan)
        if kecamatan is None:
            return {"success": False, "message": "Kelurahan tidak valid."}
        
        try:
            laporan_id = self.laporan_model.create(
                user_id=user_id,
                judul=judul.strip(),
                kategori=kategori,
                deskripsi=deskripsi.strip(),
                lokasi=lokasi.strip(),
                kelurahan=kelurahan,
                kecamatan=kecamatan
            )
            return {
                "success": True,
                "message": f"Laporan #{laporan_id} berhasil dibuat!",
                "laporan_id": laporan_id
            }
        except Exception as e:
            return {"success": False, "message": f"Gagal membuat laporan: {e}"}

    # ──────────────────────────────────────
    # WARGA: LIHAT RIWAYAT
    # ──────────────────────────────────────

    def get_laporan_warga(self, user_id: int) -> list[dict]:
        """Ambil semua laporan milik warga tertentu."""
        return self.laporan_model.get_by_user(user_id)
    
    def get_detail_laporan(self, laporan_id: int) -> dict | None:
        """Ambil detail satu laporan termasuk data pelapor."""
        return self.laporan_model.get_by_id(laporan_id)
    
    def get_riwayat_laporan(self, laporan_id: int) -> list[dict]:
        """Ambil timeline riwayat status sebuah laporan."""
        return self.laporan_model.get_riwayat(laporan_id)

    # ──────────────────────────────────────
    # ADMIN: AMBIL LAPORAN SESUAI SCOPE
    # ──────────────────────────────────────

    def get_laporan_kelurahan(self, kelurahan: str,
                              status: str = None) -> list[dict]:
        """Ambil laporan di kelurahan tertentu (untuk Admin Kelurahan)."""
        return self.laporan_model.get_by_kelurahan(kelurahan, status)

    def get_laporan_kecamatan(self, kecamatan: str,
                              status: str = None) -> list[dict]:
        """Ambil laporan se-kecamatan (untuk Admin Kecamatan)."""
        return self.laporan_model.get_by_kecamatan(kecamatan, status)

    def get_laporan_kota(self, status: str = None) -> list[dict]:
        """Ambil semua laporan se-kota (untuk Admin Kota)."""
        return self.laporan_model.get_all(status)

    # ──────────────────────────────────────
    # ADMIN: PROSES / ESKALASI LAPORAN
    # ──────────────────────────────────────

    def proses_laporan(self, laporan_id: int, admin_id: int,
                       status_baru: str, catatan: str) -> dict:
        """
        Admin memproses laporan: ubah status & tambah catatan.
        Digunakan untuk semua aksi: proses, eskalasi, selesai, tolak.
        """
        if not catatan or not catatan.strip():
            return {"success": False, "message": "Catatan admin wajib diisi."}
        
        try:
            self.laporan_model.update_status(
                laporan_id=laporan_id,
                admin_id=admin_id,
                status_baru=status_baru,
                catatan=catatan.strip()
            )
            return {
                "success": True,
                "message": f"Status laporan #{laporan_id} diubah menjadi '{status_baru}'."
            }
        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"Gagal memproses laporan: {e}"}

    # ──────────────────────────────────────
    # ADMIN KOTA: STATISTIK
    # ──────────────────────────────────────

    def get_statistik(self) -> dict:
        """Ambil semua data statistik untuk dashboard Admin Kota."""
        return {
            "per_status": self.laporan_model.get_statistik_per_status(),
            "per_kategori": self.laporan_model.get_statistik_per_kategori(),
            "per_kecamatan": self.laporan_model.get_statistik_per_kecamatan(),
            "bulanan": self.laporan_model.get_statistik_bulanan(),
        }
