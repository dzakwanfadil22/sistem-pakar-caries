from flask import Flask, jsonify, render_template, request
import cf, storage
import cf, storage, evaluasi

app = Flask(__name__, static_folder="public/static")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

@app.get("/")
def index():
    return render_template("index.html", gejala=cf.GEJALA, pilihan=cf.PILIHAN)


@app.post("/api/diagnosa")
def diagnosa():
    d = request.get_json(force=True)
    nama = (d.get("nama") or "").strip()
    if not nama:
        return jsonify(error="Nama pasien wajib diisi."), 400
    try:
        umur = int(d.get("umur"))
        if not 1 <= umur <= 120:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="Umur wajib diisi."), 400
    nilai = {k: float(v) for k, v in (d.get("nilai") or {}).items()}
    try:
        hasil = cf.hitung(nilai)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    try:
        hasil["disimpan_di"] = storage.simpan(nama, umur, nilai, hasil)
        hasil["simpan_ok"] = True
    except Exception as e:  # jangan gagalkan diagnosis bila penyimpanan error
        hasil["simpan_ok"] = False
        hasil["simpan_error"] = str(e)
    hasil["nama"] = nama
    return jsonify(hasil)


@app.get("/riwayat")
def riwayat():
    header, baris = storage.riwayat()
    return render_template("riwayat.html", header=header, baris=baris)


@app.errorhandler(413)
def terlalu_besar(e):
    return jsonify(error="Ukuran file maksimal 5 MB."), 413

@app.get("/evaluasi")
def halaman_evaluasi():
    return render_template("evaluasi.html")

@app.post("/api/evaluasi")
def api_evaluasi():
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".csv"):
        return jsonify(error="Pilih file berformat CSV."), 400
    try:
        th = float(request.form.get("threshold", "0.5").replace(",", "."))
        return jsonify(evaluasi.evaluasi(f.read(), th))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception:
        return jsonify(error="File tidak dapat dibaca. Periksa format CSV-nya."), 400

@app.get("/pakar")
def pakar():
    skala, bawah = [], 0
    for batas, nama, _saran, _nada in cf.TINGKAT:
        skala.append(("0%" if batas == 0 else f"{bawah + 1}–{batas}%", nama))
        bawah = batas
    return render_template("pakar.html", gejala=cf.GEJALA, skala=skala)

if __name__ == "__main__":
    app.run(debug=True)
