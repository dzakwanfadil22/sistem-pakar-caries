"""Evaluasi sistem pakar: confusion matrix, accuracy, precision, recall, F1-score.

Data uji = file CSV. Tiap baris satu pasien: nilai keyakinan G01..G10 dan
diagnosis sebenarnya (label dari dokter): Positif / Negatif.
"""
import csv, io
import cf
import pdf_reader

THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
POSITIF = {"positif", "1", "ya", "yes", "true", "karies"}
NEGATIF = {"negatif", "0", "tidak", "no", "false", "sehat"}
KOLOM_LABEL = ("label", "kelas", "aktual", "actual", "sebenarnya", "diagnosis_dokter", "diagnosis dokter")


def _nilai(sel, no, kode):
    s = str(sel).strip()
    if s == "":
        return 0.0
    try:
        v = float(s.replace(",", "."))
    except ValueError:
        v = pdf_reader._cari_nilai(s)      # boleh berupa label, mis. "Cukup Yakin"
        if v is None:
            raise ValueError(f"Baris {no}: nilai {kode} '{s}' tidak dikenali.")
        return v
    if not 0 <= v <= 1:
        raise ValueError(f"Baris {no}: nilai {kode} = {s} harus antara 0 dan 1.")
    return v


def _baca(data: bytes):
    try:
        teks = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        teks = data.decode("latin-1")
    baris1 = teks.splitlines()[0] if teks.strip() else ""
    delim = ";" if baris1.count(";") > baris1.count(",") else ","
    pembaca = csv.DictReader(io.StringIO(teks), delimiter=delim)
    if not pembaca.fieldnames:
        raise ValueError("File CSV kosong.")
    kolom = {(k or "").strip().lower(): k for k in pembaca.fieldnames}
    k_label = next((kolom[x] for x in KOLOM_LABEL if x in kolom), None)
    if not k_label:
        raise ValueError("Kolom label tidak ditemukan. Beri nama kolomnya 'label' (isi: Positif / Negatif).")
    hilang = [g[0] for g in cf.GEJALA if g[0].lower() not in kolom]
    if hilang:
        raise ValueError("Kolom gejala tidak lengkap, kurang: " + ", ".join(hilang))
    k_nama = kolom.get("nama")

    hasil = []
    for no, r in enumerate(pembaca, start=1):
        if not any((v or "").strip() for v in r.values()):
            continue
        lab = str(r[k_label]).strip().lower()
        if lab in POSITIF:
            aktual = 1
        elif lab in NEGATIF:
            aktual = 0
        else:
            raise ValueError(f"Baris {no}: label '{r[k_label]}' tidak dikenali (pakai Positif atau Negatif).")
        nilai = {g[0]: _nilai(r[kolom[g[0].lower()]], no, g[0]) for g in cf.GEJALA}
        cfv = cf.hitung(nilai)["rincian"][-1]["kombinasi"]     # CF akhir 0..1
        hasil.append({"no": no, "nama": (r[k_nama].strip() if k_nama else "") or f"Data {no}",
                      "cf": cfv, "aktual": aktual})
    if not hasil:
        raise ValueError("Tidak ada baris data di file.")
    return hasil


def _metrik(baris, th):
    tp = tn = fp = fn = 0
    for b in baris:
        pred = 1 if b["cf"] >= th else 0
        if pred and b["aktual"]: tp += 1
        elif not pred and not b["aktual"]: tn += 1
        elif pred and not b["aktual"]: fp += 1
        else: fn += 1
    bagi = lambda a, b: a / b if b else 0.0
    acc = bagi(tp + tn, tp + tn + fp + fn)
    prec = bagi(tp, tp + fp)
    rec = bagi(tp, tp + fn)
    f1 = bagi(2 * prec * rec, prec + rec)
    return {"threshold": th, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "accuracy": acc, "precision": prec, "recall": rec, "f1": f1}


def evaluasi(data: bytes, threshold: float = 0.5) -> dict:
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold harus antara 0 dan 1.")
    baris = _baca(data)
    ths = sorted(set(THRESHOLDS + [threshold]))
    detail = [{"no": b["no"], "nama": b["nama"], "persen": round(b["cf"] * 100, 2),
               "prediksi": 1 if b["cf"] >= threshold else 0, "aktual": b["aktual"],
               "benar": (b["cf"] >= threshold) == bool(b["aktual"])} for b in baris]
    return {"n": len(baris),
            "positif": sum(b["aktual"] for b in baris),
            "negatif": sum(1 - b["aktual"] for b in baris),
            "threshold": threshold,
            "metrik": _metrik(baris, threshold),
            "perbandingan": [_metrik(baris, t) for t in ths],
            "detail": detail}
