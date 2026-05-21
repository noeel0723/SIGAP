# config/database.py
# Modul koneksi database MySQL

"""
Mengelola koneksi ke database MySQL menggunakan mysql-connector-python.
Menyediakan connection pooling dan helper method untuk query.
"""

import mysql.connector
from mysql.connector import Error, pooling
from config.settings import DB_CONFIG


class DatabaseConnection:
    """
    Wrapper koneksi database MySQL dengan connection pooling.
    
    Usage:
        db = DatabaseConnection()
        results = db.fetch_all("SELECT * FROM users WHERE role = %s", ("warga",))
        db.execute("INSERT INTO users (nama, email) VALUES (%s, %s)", ("Andi", "andi@mail.com"))
    """

    def __init__(self):
        self.pool = None
        self._create_pool()
    
    def _create_pool(self):
        """Buat connection pool ke MySQL."""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="sigap_pool",
                pool_size=5,
                pool_reset_session=True,
                **DB_CONFIG
            )
            print("[DB] Connection pool berhasil dibuat.")
        except Error as e:
            print(f"[DB] Gagal membuat connection pool: {e}")
            raise
    
    def get_connection(self):
        """Ambil satu koneksi dari pool."""
        try:
            return self.pool.get_connection()
        except Error as e:
            print(f"[DB] Gagal mengambil koneksi: {e}")
            raise
    
    def execute(self, query: str, params: tuple = None) -> int:
        """
        Eksekusi query INSERT/UPDATE/DELETE.
        Returns: lastrowid untuk INSERT, rowcount untuk lainnya.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        except Error as e:
            conn.rollback()
            print(f"[DB] Gagal eksekusi query: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def fetch_one(self, query: str, params: tuple = None) -> dict | None:
        """Ambil satu baris hasil query sebagai dictionary."""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            print(f"[DB] Gagal fetch_one: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def fetch_all(self, query: str, params: tuple = None) -> list[dict]:
        """Ambil semua baris hasil query sebagai list of dictionary."""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            print(f"[DB] Gagal fetch_all: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def close(self):
        """Tutup semua koneksi di pool (dipanggil saat app exit)."""
        # mysql-connector pool tidak punya close() eksplisit,
        # koneksi individual ditutup setelah digunakan.
        print("[DB] Database connection pool ditutup.")
