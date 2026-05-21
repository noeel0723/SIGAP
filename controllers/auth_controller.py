# controllers/auth_controller.py
# Controller untuk logika autentikasi (login, register, logout)

"""
Controller autentikasi yang menjembatani Views dan Models.
Menangani validasi input, business logic, dan error handling.
"""

from models.user_model import UserModel
from config.database import DatabaseConnection


class AuthController:
    """Controller untuk operasi autentikasi."""

    def __init__(self, db: DatabaseConnection):
        self.user_model = UserModel(db)
    
    def login(self, email: str, password: str) -> dict:
        """
        Proses login user.
        Returns: {"success": bool, "message": str, "user": dict|None}
        """
        # Validasi input
        if not email or not email.strip():
            return {"success": False, "message": "Email wajib diisi.", "user": None}
        if not password:
            return {"success": False, "message": "Password wajib diisi.", "user": None}
        
        email = email.strip().lower()
        
        # Autentikasi
        user = self.user_model.authenticate(email, password)
        
        if user is None:
            return {
                "success": False,
                "message": "Email atau password salah.",
                "user": None
            }
        
        return {
            "success": True,
            "message": f"Selamat datang, {user['nama_lengkap']}!",
            "user": user
        }
    
    def register(self, nama: str, email: str, password: str,
                 konfirmasi_password: str, no_telepon: str = None) -> dict:
        """
        Proses registrasi warga baru.
        Returns: {"success": bool, "message": str}
        """
        # Validasi input
        if not nama or not nama.strip():
            return {"success": False, "message": "Nama lengkap wajib diisi."}
        if not email or not email.strip():
            return {"success": False, "message": "Email wajib diisi."}
        if not password:
            return {"success": False, "message": "Password wajib diisi."}
        if len(password) < 6:
            return {"success": False, "message": "Password minimal 6 karakter."}
        if password != konfirmasi_password:
            return {"success": False, "message": "Konfirmasi password tidak cocok."}
        
        # Validasi format email sederhana
        if "@" not in email or "." not in email:
            return {"success": False, "message": "Format email tidak valid."}
        
        try:
            self.user_model.register(
                nama=nama.strip(),
                email=email.strip().lower(),
                password=password,
                no_telepon=no_telepon.strip() if no_telepon else None
            )
            return {
                "success": True,
                "message": "Registrasi berhasil! Silakan login."
            }
        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"Terjadi kesalahan: {e}"}
