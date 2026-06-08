# database/migrate_v1_2_foto.py
import mysql.connector
import sys
import os

# Tambahkan root project ke sys.path agar bisa import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DB_CONFIG

def migrate():
    print("[MIGRASI V1.2] Menambahkan fitur lampiran foto pada tabel laporan...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Tambahkan kolom foto_laporan
        try:
            cursor.execute("ALTER TABLE laporan ADD COLUMN foto_laporan VARCHAR(255) DEFAULT NULL")
            print("  - Kolom 'foto_laporan' berhasil ditambahkan.")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Duplicate column name
                print("  - Kolom 'foto_laporan' sudah ada.")
            else:
                raise err

        # Tambahkan kolom foto_selesai
        try:
            cursor.execute("ALTER TABLE laporan ADD COLUMN foto_selesai VARCHAR(255) DEFAULT NULL")
            print("  - Kolom 'foto_selesai' berhasil ditambahkan.")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Duplicate column name
                print("  - Kolom 'foto_selesai' sudah ada.")
            else:
                raise err

        conn.commit()
        print("[MIGRASI V1.2] Selesai!")

    except mysql.connector.Error as e:
        print(f"[ERROR] Migrasi gagal: {e}")
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    migrate()
