# database/setup_db.py
# Script untuk membuat database dan tabel-tabel SIGAP

"""
Jalankan script ini sekali saat pertama kali setup:
    python database/setup_db.py

Script ini akan:
1. Membuat database 'sigap_db' jika belum ada
2. Membuat semua tabel yang diperlukan
3. Meng-insert data awal (seed) untuk admin default
"""

import mysql.connector
from mysql.connector import Error
import bcrypt
import sys
import os

# Tambahkan root project ke sys.path agar bisa import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DB_CONFIG


def create_database():
    """Buat database sigap_db jika belum ada."""
    config = DB_CONFIG.copy()
    db_name = config.pop("database")
    config.pop("charset", None)
    config.pop("collation", None)
    config.pop("autocommit", None)

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        print(f"[SETUP] Database '{db_name}' siap.")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"[SETUP] Gagal membuat database: {e}")
        sys.exit(1)


def create_tables():
    """Buat semua tabel yang diperlukan."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # ──────────────────────────────────────
        # TABEL: users
        # ──────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                nama_lengkap    VARCHAR(100)    NOT NULL,
                email           VARCHAR(100)    NOT NULL UNIQUE,
                password_hash   VARCHAR(255)    NOT NULL,
                no_telepon      VARCHAR(20)     DEFAULT NULL,
                role            ENUM('warga', 'admin_kelurahan', 'admin_kecamatan', 'admin_kota') 
                                NOT NULL DEFAULT 'warga',
                -- Wilayah (untuk admin, menentukan scope akses)
                kelurahan       VARCHAR(100)    DEFAULT NULL,
                kecamatan       VARCHAR(100)    DEFAULT NULL,
                -- Metadata
                is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
                created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP 
                                ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_role (role),
                INDEX idx_kelurahan (kelurahan),
                INDEX idx_kecamatan (kecamatan)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("[SETUP] Tabel 'users' dibuat.")

        # ──────────────────────────────────────
        # TABEL: laporan
        # ──────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS laporan (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                user_id         INT             NOT NULL,
                judul           VARCHAR(200)    NOT NULL,
                kategori        VARCHAR(100)    NOT NULL,
                deskripsi       TEXT            NOT NULL,
                lokasi          VARCHAR(255)    NOT NULL,
                kelurahan       VARCHAR(100)    NOT NULL,
                kecamatan       VARCHAR(100)    NOT NULL,
                status          ENUM(
                                    'Menunggu', 
                                    'Diproses Kelurahan', 
                                    'Diproses Kecamatan', 
                                    'Diproses Kota', 
                                    'Selesai', 
                                    'Ditolak'
                                ) NOT NULL DEFAULT 'Menunggu',
                -- Fitur: Laporan Anonim
                is_anonymous    TINYINT(1)      NOT NULL DEFAULT 0,
                -- Fitur: Prioritas Otomatis
                prioritas       ENUM('Rendah', 'Sedang', 'Tinggi')
                                NOT NULL DEFAULT 'Rendah',
                -- Metadata
                created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP 
                                ON UPDATE CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_status (status),
                INDEX idx_kelurahan (kelurahan),
                INDEX idx_kecamatan (kecamatan),
                INDEX idx_kategori (kategori),
                INDEX idx_created (created_at),
                INDEX idx_prioritas (prioritas)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("[SETUP] Tabel 'laporan' dibuat.")

        # ──────────────────────────────────────
        # TABEL: riwayat_status (log setiap perubahan status)
        # ──────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS riwayat_status (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                laporan_id      INT             NOT NULL,
                admin_id        INT             DEFAULT NULL,
                status_lama     VARCHAR(50)     NOT NULL,
                status_baru     VARCHAR(50)     NOT NULL,
                catatan_admin   TEXT            DEFAULT NULL,
                created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (laporan_id) REFERENCES laporan(id) ON DELETE CASCADE,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_laporan (laporan_id),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("[SETUP] Tabel 'riwayat_status' dibuat.")

        # ──────────────────────────────────────
        # TABEL: dukungan_laporan (upvote / support)
        # ──────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dukungan_laporan (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                laporan_id      INT             NOT NULL,
                user_id         INT             NOT NULL,
                created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (laporan_id) REFERENCES laporan(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY uq_dukungan (laporan_id, user_id),
                INDEX idx_laporan (laporan_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("[SETUP] Tabel 'dukungan_laporan' dibuat.")

        conn.commit()
        cursor.close()
        conn.close()
        print("[SETUP] Semua tabel berhasil dibuat!")

    except Error as e:
        print(f"[SETUP] Gagal membuat tabel: {e}")
        sys.exit(1)


def seed_admin_defaults():
    """Insert akun admin default untuk setiap level."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        default_password = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())

        admin_data = [
            # (nama, email, role, kelurahan, kecamatan)
            ("Admin Kelurahan Wenang Utara", "admin.wenangutara@sigap.id",
             "admin_kelurahan", "Wenang Utara", "Wenang"),
            ("Admin Kelurahan Sario", "admin.sario@sigap.id",
             "admin_kelurahan", "Sario", "Sario"),
            ("Admin Kecamatan Wenang", "admin.kec.wenang@sigap.id",
             "admin_kecamatan", None, "Wenang"),
            ("Admin Kecamatan Sario", "admin.kec.sario@sigap.id",
             "admin_kecamatan", None, "Sario"),
            ("Admin Kota Manado", "admin.kota@sigap.id",
             "admin_kota", None, None),
        ]

        for nama, email, role, kelurahan, kecamatan in admin_data:
            cursor.execute(
                "SELECT id FROM users WHERE email = %s", (email,)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """INSERT INTO users 
                       (nama_lengkap, email, password_hash, role, kelurahan, kecamatan)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (nama, email, default_password.decode("utf-8"),
                     role, kelurahan, kecamatan)
                )
                print(f"[SEED] Admin '{nama}' ({email}) ditambahkan.")
            else:
                print(f"[SEED] Admin '{email}' sudah ada, dilewati.")

        conn.commit()
        cursor.close()
        conn.close()
        print("[SEED] Seeding admin default selesai!")

    except Error as e:
        print(f"[SEED] Gagal seeding: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("  SIGAP - Database Setup")
    print("=" * 50)
    create_database()
    create_tables()
    seed_admin_defaults()
    print("\n[DONE] Setup database selesai!")
    print("  Default admin password: admin123")
    print("  Silakan ubah password setelah login pertama.")
