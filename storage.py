"""Penyimpanan ke Google Sheets (seperti database). Jika belum dikonfigurasi,
otomatis disimpan ke data/riwayat.csv sebagai cadangan lokal."""
import csv, json, os
from datetime import datetime
from cf import GEJALA

KREDENSIAL = os.environ.get("GOOGLE_CREDENTIALS", "credentials.json")
SHEET_ID = os.environ.get("SPREADSHEET_ID") or "17fB893tiwW6OF3v1Ej6v1dzjxJYl9EL3JTndGNYJRnE"
KREDENSIAL_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
NAMA_SHEET = "Diagnosis"
CSV_PATH = os.path.join("data", "riwayat.csv")
HEADER = ["Waktu", "Nama", "Umur"] + [g[0] for g in GEJALA] + ["Persentase", "Kesimpulan"]


def _worksheet():
    import gspread
    if KREDENSIAL_JSON:
        gc = gspread.service_account_from_dict(json.loads(KREDENSIAL_JSON))
    else:
        gc = gspread.service_account(filename=KREDENSIAL)
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(NAMA_SHEET)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(NAMA_SHEET, rows=1000, cols=len(HEADER))
    if not ws.row_values(1):
        ws.append_row(HEADER)
    return ws


def _pakai_sheets():
    ada_kunci = bool(KREDENSIAL_JSON) or os.path.exists(KREDENSIAL)
    return bool(SHEET_ID) and not SHEET_ID.startswith("TEMPEL") and ada_kunci


def simpan(nama, umur, nilai, hasil):
    baris = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nama, umur] + \
            [nilai.get(g[0], 0) for g in GEJALA] + [hasil["persen"], hasil["kesimpulan"]]
    if _pakai_sheets():
        _worksheet().append_row(baris, value_input_option="USER_ENTERED")
        return "Google Sheets"
    os.makedirs("data", exist_ok=True)
    baru = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if baru:
            w.writerow(HEADER)
        w.writerow(baris)
    return "file lokal (data/riwayat.csv)"


def riwayat():
    if _pakai_sheets():
        data = _worksheet().get_all_values()
    elif os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8-sig") as f:
            data = list(csv.reader(f))
    else:
        return HEADER, []
    if not data:
        return HEADER, []
    return data[0], data[1:][::-1]  # terbaru di atas
