"""Logika Certainty Factor untuk diagnosis karies gigi."""

# (kode, gejala, CF pakar)
GEJALA = [
    ("G01", "Adanya titik hitam dibagian email gigi", 0.4),
    ("G02", "Adanya lubang pada gigi", 1.0),
    ("G03", "Terasa denyut saat makan", 0.8),
    ("G04", "Nyeri saat kurang aktivitas", 0.6),
    ("G05", "Adanya karang gigi", 0.0),
    ("G06", "Ada bercak putih", 0.4),
    ("G07", "Bau mulut", 0.8),
    ("G08", "Adanya pembengkakan pada gusi", 1.0),
    ("G09", "Gigi terasa ngilu", 0.4),
    ("G10", "Abses gigi", 1.0),
]

# (label, nilai CF pasien)
PILIHAN = [
    ("Tidak (0)", 0.0),
    ("Tidak Yakin (0.2)", 0.2),
    ("Kurang Yakin (0.4)", 0.4),
    ("Cukup Yakin (0.6)", 0.6),
    ("Yakin (0.8)", 0.8),
    ("Sangat Yakin (1.0)", 1.0),
]

AMBANG = 0.5  # batas keputusan "terindikasi karies" (ubah sesuai pakar)

# Interpretasi persentase CF: (batas atas %, nama tingkat, saran, nada warna)
TINGKAT = [
    (0,   "Tidak ada keyakinan", "Tidak ada gejala yang mengarah ke karies dari isian ini. Tetap rutin menyikat gigi.", "aman"),
    (20,  "Sangat rendah", "Kemungkinan karies sangat kecil. Jaga kebersihan gigi dan periksa rutin tiap 6 bulan.", "aman"),
    (40,  "Rendah", "Kemungkinan karies rendah. Pantau gejala dan periksa ke dokter gigi bila bertambah.", "aman"),
    (60,  "Sedang (Superfisialis)", "Kemungkinan karies Superfisialis. Periksakan ke dokter gigi sebelum meluas.", "sedang"),
    (80,  "Tinggi (Media)", "Kemungkinan karies Media yang mencapai dentin. Segera periksa ke dokter gigi.", "bahaya"),
    (100, "Sangat tinggi (Profunda)", "Kemungkinan karies Profunda dekat saraf gigi. Segera ke dokter gigi sebelum parah.", "bahaya"),
]

def tingkat(persen):
    for batas, nama, saran, nada in TINGKAT:
        if persen <= batas:
            return nama, saran, nada
    return TINGKAT[-1][1:]

def hitung(nilai_pasien: dict) -> dict:
    """nilai_pasien: {"G01": 0.4, ...}. Mengembalikan rincian + persentase."""
    rincian, lama = [], None
    for kode, nama, cf_pakar in GEJALA:
        cf_e = float(nilai_pasien.get(kode, 0))
        if not 0 <= cf_e <= 1:
            raise ValueError(f"Nilai {kode} harus 0 sampai 1")
        cf_he = cf_pakar * cf_e                      # CF[H,E] = CF[H] * CF[E]
        lama = cf_he if lama is None else lama + cf_he * (1 - lama)  # kombinasi
        rincian.append({"kode": kode, "gejala": nama, "pakar": cf_pakar,
                        "pasien": cf_e, "cf_he": round(cf_he, 6),
                        "kombinasi": round(lama, 6)})
    persen = round(lama * 100, 2)
    nama_tingkat, saran, nada = tingkat(persen)
    return {"rincian": rincian, "persen": persen, "tingkat": nama_tingkat,
            "saran": saran, "nada": nada,
            "kesimpulan": f"{nama_tingkat}"}