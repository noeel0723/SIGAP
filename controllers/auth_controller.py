# controllers/auth_controller.py
# Controller untuk logika autentikasi (login, register, logout)

"""
Controller autentikasi yang menjembatani Views dan Models.
Menangani validasi input, business logic, dan error handling.
"""

from models.user_model import UserModel
from config.database import DatabaseConnection
from datetime import datetime, timedelta


class AuthController:
    """Controller untuk operasi autentikasi."""

    # Rate limiting: track failed login attempts per email
    _login_attempts = {}  # {email: {"count": int, "locked_until": datetime|None}}

    def __init__(self, db: DatabaseConnection):
        self.user_model = UserModel(db)
    
    def login(self, email: str, password: str) -> dict:
        """
        Proses login user dengan rate limiting.
        Returns: {"success": bool, "message": str, "user": dict|None,
                  "locked": bool, "locked_seconds": int}
        """
        # Validasi input
        if not email or not email.strip():
            return {"success": False, "message": "Email wajib diisi.", "user": None,
                    "locked": False, "locked_seconds": 0}
        if not password:
            return {"success": False, "message": "Password wajib diisi.", "user": None,
                    "locked": False, "locked_seconds": 0}
        
        email = email.strip().lower()
        
        # Check rate limit
        is_locked, remaining = self._check_rate_limit(email)
        if is_locked:
            return {
                "success": False,
                "message": f"Terlalu banyak percobaan gagal. Coba lagi dalam {remaining} detik.",
                "user": None,
                "locked": True,
                "locked_seconds": remaining
            }
        
        # Autentikasi
        user = self.user_model.authenticate(email, password)
        
        if user is None:
            self._record_failed_attempt(email)
            attempts_info = self._login_attempts.get(email, {})
            count = attempts_info.get("count", 0)
            remaining_attempts = 5 - (count % 5)
            if remaining_attempts == 0:
                remaining_attempts = 5
            
            msg = "Email atau password salah."
            if count >= 3:
                msg += f" ({remaining_attempts} percobaan tersisa)"
            
            return {
                "success": False,
                "message": msg,
                "user": None,
                "locked": False,
                "locked_seconds": 0
            }
        
        # Reset attempts on success
        self._reset_attempts(email)
        
        return {
            "success": True,
            "message": f"Selamat datang, {user['nama_lengkap']}!",
            "user": user,
            "locked": False,
            "locked_seconds": 0
        }
    
    def _check_rate_limit(self, email: str) -> tuple:
        """Check if email is rate limited. Returns (is_locked, remaining_seconds)."""
        info = self._login_attempts.get(email)
        if not info:
            return False, 0
        
        locked_until = info.get("locked_until")
        if locked_until and datetime.now() < locked_until:
            remaining = int((locked_until - datetime.now()).total_seconds())
            return True, max(remaining, 1)
        elif locked_until and datetime.now() >= locked_until:
            # Unlock but keep count
            info["locked_until"] = None
        
        return False, 0
    
    def _record_failed_attempt(self, email: str):
        """Record a failed login attempt and lock if threshold reached."""
        if email not in self._login_attempts:
            self._login_attempts[email] = {"count": 0, "locked_until": None}
        
        info = self._login_attempts[email]
        info["count"] += 1
        
        # Lock after every 5 failed attempts
        if info["count"] % 5 == 0:
            # Accumulated freeze: 1 min per 5 attempts (1min, 2min, 3min...)
            freeze_minutes = info["count"] // 5
            info["locked_until"] = datetime.now() + timedelta(minutes=freeze_minutes)
    
    def _reset_attempts(self, email: str):
        """Reset login attempts after successful login."""
        if email in self._login_attempts:
            del self._login_attempts[email]
    
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

    def change_password(self, user_id: int, old_password: str,
                        new_password: str, confirm_password: str) -> dict:
        """
        Ubah password user.
        Returns: {"success": bool, "message": str}
        """
        if not old_password:
            return {"success": False, "message": "Password lama wajib diisi."}
        if not new_password:
            return {"success": False, "message": "Password baru wajib diisi."}
        if len(new_password) < 6:
            return {"success": False, "message": "Password baru minimal 6 karakter."}
        if new_password != confirm_password:
            return {"success": False, "message": "Konfirmasi password tidak cocok."}
        
        success = self.user_model.change_password(user_id, old_password, new_password)
        if success:
            return {"success": True, "message": "Password berhasil diubah!"}
        return {"success": False, "message": "Password lama tidak benar."}
