# config/wilayah.py
# Data hierarki wilayah: Kota -> Kecamatan -> Kelurahan

"""
Data statis wilayah untuk dropdown di form laporan dan 
penentuan scope akses admin.

Struktur: WILAYAH_DATA[kota][kecamatan] = [kelurahan, ...]

Catatan: Sesuaikan data ini dengan wilayah kota yang sebenarnya.
Data di bawah ini adalah contoh untuk Kota Manado.
"""

NAMA_KOTA = "Kota Manado"

WILAYAH_DATA = {
    "Wenang": [
        "Wenang Utara",
        "Wenang Selatan",
        "Pinaesaan",
        "Calaca",
        "Istiqlal",
        "Lawangirung",
        "Mahakeret Barat",
        "Mahakeret Timur",
        "Tikala Ares",
        "Teling Bawah",
    ],
    "Sario": [
        "Sario",
        "Sario Kotabaru",
        "Sario Tumpaan",
        "Sario Utara",
        "Titiwungen Selatan",
        "Titiwungen Utara",
    ],
    "Malalayang": [
        "Malalayang Satu",
        "Malalayang Satu Timur",
        "Malalayang Dua",
        "Bahu",
        "Kleak",
        "Winangun Satu",
        "Winangun Dua",
    ],
    "Wanea": [
        "Wanea",
        "Tanjung Batu",
        "Pakowa",
        "Ranotana",
        "Ranotana Weru",
        "Karombasan Utara",
        "Karombasan Selatan",
        "Teling Atas",
        "Tingkulu",
    ],
    "Tikala": [
        "Tikala Baru",
        "Tikala Kumaraka",
        "Taas",
        "Banjer",
        "Paal 4",
        "Perkamil",
    ],
    "Mapanget": [
        "Mapanget",
        "Kima Atas",
        "Kima Bawah",
        "Paniki Bawah",
        "Paniki Atas",
        "Lapangan",
        "Buha",
    ],
    "Singkil": [
        "Singkil Satu",
        "Singkil Dua",
        "Karame",
        "Wawonasa",
        "Ketang Baru",
        "Ternate Tanjung",
        "Ternate Baru",
    ],
    "Tuminting": [
        "Tuminting",
        "Sindulang Satu",
        "Sindulang Dua",
        "Bitung Karangria",
        "Maasing",
        "Sumompo",
        "Tumumpa Satu",
        "Tumumpa Dua",
        "Mahawu",
        "Islam",
    ],
    "Bunaken": [
        "Bunaken",
        "Molas",
        "Tongkeina",
        "Meras",
        "Bailang",
        "Pandu",
    ],
}


def get_semua_kecamatan() -> list[str]:
    """Mengembalikan daftar semua nama kecamatan."""
    return sorted(WILAYAH_DATA.keys())


def get_kelurahan_by_kecamatan(kecamatan: str) -> list[str]:
    """Mengembalikan daftar kelurahan berdasarkan nama kecamatan."""
    return sorted(WILAYAH_DATA.get(kecamatan, []))


def get_kecamatan_by_kelurahan(kelurahan: str) -> str | None:
    """Mengembalikan nama kecamatan dari sebuah kelurahan."""
    for kecamatan, daftar_kelurahan in WILAYAH_DATA.items():
        if kelurahan in daftar_kelurahan:
            return kecamatan
    return None
