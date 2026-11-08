const $ = (s) => document.querySelector(s);
const form = $("#form"),
  hasil = $("#hasil");
const C = 2 * Math.PI * 52;
$("#arc").style.strokeDasharray = C;
$("#arc").style.strokeDashoffset = C;

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#err").textContent = "";
  const fd = new FormData(form);
  const nilai = {};
  for (const [k, v] of fd.entries()) if (/^G\d+$/.test(k)) nilai[k] = v;
  const btn = form.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Menghitung...";
  try {
    const r = await fetch("/api/diagnosa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nama: fd.get("nama"),
        umur: fd.get("umur"),
        nilai,
      }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "Terjadi kesalahan");
    tampil(d, fd.get("umur"));
  } catch (err) {
    $("#err").textContent = err.message;
  }
  btn.disabled = false;
  btn.textContent = "Hitung diagnosis";
});

function tampil(d, umur) {
  $("#persen").textContent = d.persen.toFixed(2);
  $("#arc").style.strokeDashoffset = C * (1 - Math.min(d.persen, 100) / 100);
  hasil.classList.remove("sedang", "danger");
  if (d.nada === "sedang") hasil.classList.add("sedang");
  if (d.nada === "bahaya") hasil.classList.add("danger");
  $("#meta").textContent =
    `${d.nama}${umur ? ", " + umur + " tahun" : ""} · ` +
    new Date().toLocaleString("id-ID");
  $("#vonis").textContent = d.kesimpulan;
  $("#saran").textContent = d.saran;
  const s = $("#simpan");
  s.className = "badge " + (d.simpan_ok ? "ok" : "bad") + " noprint";
  s.textContent = d.simpan_ok
    ? "Tersimpan di " + d.disimpan_di
    : "Gagal menyimpan: " + d.simpan_error;
  const f = (x) => +x.toFixed(4);
  $("#rincian").innerHTML = d.rincian
    .map(
      (r) =>
        `<tr><td>${r.kode}</td><td>${r.gejala}</td><td>${r.pakar}</td><td>${r.pasien}</td>
     <td>${f(r.cf_he)}</td><td>${f(r.kombinasi)}</td></tr>`,
    )
    .join("");
  hasil.hidden = false;
  hasil.scrollIntoView({ behavior: "smooth", block: "start" });
}

$("#cetak").addEventListener("click", () => window.print());
$("#reset").addEventListener("click", () => {
  hasil.hidden = true;
});