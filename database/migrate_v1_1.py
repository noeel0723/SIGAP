# database/migrate_v1_1.py
# Script migrasi database v1.0 → v1.1
# Menambahkan fitur: Laporan Anonim, Prioritas Otomatis, Dukungan Laporan

"""
Jalankan script ini untuk memigrasikan database yang sudah ada:
    python database/migrate_v1_1.py

Script ini akan:
1. Menambahkan kolom 'is_anonymous' ke tabel 'laporan'
2. Menambahkan kolom 'prioritas' ke tabel 'laporan'
3. Membuat tabel baru 'dukungan_laporan'

Aman dijalankan berulang kali (idempotent).
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_CONFIG


def migrate():
    """Jalankan migrasi v1.1."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # ──────────────────────────────────────
        # 1. Tambahkan kolom is_anonymous
        # ──────────────────────────────────────
        try:
            cursor.execute("""
                ALTER TABLE laporan 
                ADD COLUMN is_anonymous TINYINT(1) NOT NULL DEFAULT 0
                AFTER status
            """)
            print("[MIGRATE] Kolom 'is_anonymous' ditambahkan ke tabel 'laporan'.")
        except Error as e:
            if e.errno == 1060:  # Duplicate column name
                print("[MIGRATE] Kolom 'is_anonymous' sudah ada, dilewati.")
            else:
                raise

        # ──────────────────────────────────────
        # 2. Tambahkan kolom prioritas
        # ──────────────────────────────────────
        try:
            cursor.execute("""
                ALTER TABLE laporan 
                ADD COLUMN prioritas ENUM('Rendah', 'Sedang', 'Tinggi') 
                NOT NULL DEFAULT 'Rendah'
                AFTER is_anonymous
            """)
            print("[MIGRATE] Kolom 'prioritas' ditambahkan ke tabel 'laporan'.")
        except Error as e:
            if e.errno == 1060:  # Duplicate column name
                print("[MIGRATE] Kolom 'prioritas' sudah ada, dilewati.")
            else:
                raise

        # ──────────────────────────────────────
        # 3. Tambahkan index prioritas
        # ──────────────────────────────────────
        try:
            cursor.execute("""
                ALTER TABLE laporan ADD INDEX idx_prioritas (prioritas)
            """)
            print("[MIGRATE] Index 'idx_prioritas' ditambahkan.")
        except Error as e:
            if e.errno == 1061:  # Duplicate key name
                print("[MIGRATE] Index 'idx_prioritas' sudah ada, dilewati.")
            else:
                raise

        # ──────────────────────────────────────
        # 4. Buat tabel dukungan_laporan
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
        print("[MIGRATE] Tabel 'dukungan_laporan' siap.")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[DONE] Migrasi v1.1 selesai!")

    except Error as e:
        print(f"[MIGRATE] Gagal migrasi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("  SIGAP -- Migrasi Database v1.0 -> v1.1")
    print("  Fitur: Anonim, Prioritas, Dukungan")
    print("=" * 50)
    migrate()
