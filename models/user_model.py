# models/user_model.py
# Model untuk operasi CRUD tabel users

"""
Modul data access layer untuk entitas User.
Semua interaksi dengan tabel 'users' dipusatkan di sini.
"""

import bcrypt
from config.database import DatabaseConnection


class UserModel:
    """Data Access Object untuk tabel users."""

    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    # ──────────────────────────────────────
    # AUTENTIKASI
    # ──────────────────────────────────────

    def register(self, nama: str, email: str, password: str,
                 no_telepon: str = None, kelurahan: str = None,
                 kecamatan: str = None) -> int:
        """
        Registrasi user baru (role default: warga).
        Returns: ID user yang baru dibuat.
        Raises: Exception jika email sudah terdaftar.
        """
        # Cek duplikasi email
        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE email = %s", (email,)
        )
        if existing:
            raise ValueError("Email sudah terdaftar.")
        
        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        
        return self.db.execute(
            """INSERT INTO users 
               (nama_lengkap, email, password_hash, no_telepon, role, kelurahan, kecamatan)
               VALUES (%s, %s, %s, %s, 'warga', %s, %s)""",
            (nama, email, password_hash, no_telepon, kelurahan, kecamatan)
        )
    
    def authenticate(self, email: str, password: str) -> dict | None:
        """
        Autentikasi user berdasarkan email dan password.
        Returns: dict data user jika berhasil, None jika gagal.
        """
        user = self.db.fetch_one(
            """SELECT id, nama_lengkap, email, password_hash, no_telepon,
                      role, kelurahan, kecamatan, is_active
               FROM users WHERE email = %s""",
            (email,)
        )
        
        if user is None:
            return None
        
        if not user["is_active"]:
            return None
        
        # Verifikasi password
        if bcrypt.checkpw(password.encode("utf-8"),
                          user["password_hash"].encode("utf-8")):
            # Hapus hash dari data yang dikembalikan
            del user["password_hash"]
            return user
        
        return None

    # ──────────────────────────────────────
    # QUERY
    # ──────────────────────────────────────
    
    def get_by_id(self, user_id: int) -> dict | None:
        """Ambil data user berdasarkan ID."""
        return self.db.fetch_one(
            """SELECT id, nama_lengkap, email, no_telepon, 
                      role, kelurahan, kecamatan, is_active, created_at
               FROM users WHERE id = %s""",
            (user_id,)
        )
    
    def get_by_email(self, email: str) -> dict | None:
        """Ambil data user berdasarkan email."""
        return self.db.fetch_one(
            """SELECT id, nama_lengkap, email, no_telepon, 
                      role, kelurahan, kecamatan, is_active, created_at
               FROM users WHERE email = %s""",
            (email,)
        )
    
    def update_profile(self, user_id: int, nama: str = None,
                       no_telepon: str = None) -> int:
        """Update profil user."""
        fields = []
        values = []
        
        if nama:
            fields.append("nama_lengkap = %s")
            values.append(nama)
        if no_telepon:
            fields.append("no_telepon = %s")
            values.append(no_telepon)
        
        if not fields:
            return 0
        
        values.append(user_id)
        return self.db.execute(
            f"UPDATE users SET {', '.join(fields)} WHERE id = %s",
            tuple(values)
        )
    
    def change_password(self, user_id: int, old_password: str,
                        new_password: str) -> bool:
        """Ubah password user. Returns True jika berhasil."""
        user = self.db.fetch_one(
            "SELECT password_hash FROM users WHERE id = %s", (user_id,)
        )
        
        if user is None:
            return False
        
        if not bcrypt.checkpw(old_password.encode("utf-8"),
                              user["password_hash"].encode("utf-8")):
            return False
        
        new_hash = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        
        self.db.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, user_id)
        )
        return True
