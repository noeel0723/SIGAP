# SIGAP - Sistem Informasi Pengaduan dan Aspirasi Publik

Aplikasi desktop native berbasis Python untuk manajemen pengaduan fasilitas publik terpadu
yang menghubungkan Warga dengan aparatur pemerintah secara berjenjang.

## Stack Teknologi

- **UI Framework**: Python 3 + CustomTkinter
- **Database**: MySQL (via Laragon)
- **Driver**: mysql-connector-python
- **Keamanan**: bcrypt
- **Visualisasi**: matplotlib
- **Packaging**: PyInstaller + Inno Setup

## Aktor Sistem

| Aktor | Hak Akses |
|---|---|
| Warga | Registrasi, login, buat laporan, lacak status |
| Admin Kelurahan | Proses laporan kelurahan, eskalasi ke kecamatan |
| Admin Kecamatan | Proses eskalasi, eskalasi ke kota |
| Admin Kota | Master dashboard, analitik, proses laporan akhir |

## Cara Menjalankan

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database (pastikan MySQL Laragon sudah berjalan)
python database/setup_db.py

# 3. Jalankan aplikasi
python main.py
```
