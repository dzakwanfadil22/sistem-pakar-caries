"""Membaca PDF gejala pasien dan mengubahnya menjadi nilai CF pasien.

Format yang dikenali (per baris):
    Nama: Budi Santoso
    Umur: 25
    G01 ... : 0.6          (angka 0 sampai 1)
    G02 ... : Yakin         (atau label: Tidak, Tidak Tahu, Kurang Yakin, ...)
"""
import io, re
from pypdf import PdfReader
import cf

ANGKA = re.compile(r"(?<![\w.,])([01](?:[.,]\d+)?)(?![\w])")
POLA_KODE = re.compile(r"\bG\d{2}\b", re.I)


def _norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()


def _terdekat(v):
    return min((n for _, n in cf.PILIHAN), key=lambda n: abs(n - v))


def _label(v):
    for lab, n in cf.PILIHAN:
        if abs(n - v) < 1e-9:
            return lab
    return ""


def _cari_nilai(sisa):
    """Cari label dulu (yang terpanjang), baru angka.
    Label dicocokkan tanpa "(angka)" di belakangnya, mis. "Cukup Yakin (0.6)" -> "cukup yakin"."""
    s = _norm(sisa)
    opsi = [(re.sub(r"\s*\(.*?\)\s*$", "", lab).strip().lower(), n) for lab, n in cf.PILIHAN]
    for dasar, n in sorted(opsi, key=lambda x: -len(x[0])):
        if dasar and re.search(rf"(?<![a-z]){re.escape(dasar)}(?![a-z])", s):
            return n
    m = ANGKA.search(sisa)
    if m:
        v = float(m.group(1).replace(",", "."))
        if 0 <= v <= 1:
            return _terdekat(v)
    return None


def baca_pdf(data: bytes) -> dict:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError("PDF terkunci kata sandi. Gunakan PDF yang tidak dikunci.")
    teks = "\n".join((p.extract_text() or "") for p in reader.pages)
    if not teks.strip():
        raise ValueError("Tidak ada teks di PDF ini (kemungkinan hasil scan atau foto). "
                         "Gunakan PDF yang teksnya bisa diblok/disalin.")
    baris = [b.strip() for b in teks.splitlines() if b.strip()]

    nama, umur = "", ""
    for b in baris:
        if not nama:
            m = re.match(r"^nama(?:\s+pasien)?\s*[:\-–]\s*(.+)$", b, re.I)
            if m:
                nama = m.group(1).strip()
        if not umur:
            m = re.match(r"^umur\s*[:\-–]?\s*(\d{1,3})", b, re.I)
            if m and 1 <= int(m.group(1)) <= 120:
                umur = m.group(1)

    nilai, rincian, hilang = {}, [], []
    for kode, nm, _ in cf.GEJALA:
        v = None
        for i, b in enumerate(baris):
            m = re.search(rf"\b{kode}\b", b, re.I)
            if not m:
                continue
            sisa = b[m.end():]
            sisa = re.sub(re.escape(nm), "", sisa, flags=re.I)
            v = _cari_nilai(sisa)
            if v is None and i + 1 < len(baris) and not POLA_KODE.search(baris[i + 1]):
                v = _cari_nilai(baris[i + 1])   # nilai bisa pindah ke baris berikutnya
            break
        ketemu = v is not None
        if not ketemu:
            hilang.append(kode)
            v = 0.0
        nilai[kode] = v
        rincian.append({"kode": kode, "gejala": nm, "nilai": v,
                        "label": _label(v), "ditemukan": ketemu})
    return {"nama": nama, "umur": umur, "nilai": nilai,
            "rincian": rincian, "tidak_ditemukan": hilang}
