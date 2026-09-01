# Deployment Guide — CUPS Print Manager

Panduan ini untuk deploy ke **STB target** (Linux Armbian, ARM64/aarch64) yang sudah
menjalankan container CUPS existing (`cups-test`) dengan printer Canon G2030.

> **Status implementasi saat ini: Phase 1** — hanya backend read-only
> (`/api/health`, `/api/printers`, `/api/printers/{name}`). Belum ada `POST /api/print`,
> job management, frontend, atau autentikasi API. Panduan ini akan diperbarui setiap
> phase baru selesai.

---

## 0. Prasyarat di STB

Cek dulu sebelum mulai:

```bash
docker --version
docker compose version
docker ps          # pastikan container `cups-test` ada dan statusnya Up
```

Host STB **tidak perlu** Node.js, Python, pip, atau npm — semua dependency ada di
dalam image Docker.

Referensi environment STB aktual (hasil `docker ps` per 2026-09-01):

```text
cups-test   image: manuelklaer/cups-canon:latest   ports: 0.0.0.0:631->631/tcp, [::]:631->631/tcp
```

STB ini juga menjalankan service lain (n8n:5678, mysql:13306, postgres:35432,
waha:3200, gowa/whatsapp:3000). Port `8000` (backend) dan `8080` (frontend, Phase 4)
saat ini tidak bentrok dengan daftar di atas — tetap jalankan `docker ps` sebelum
`docker compose up` untuk memastikan belum ada yang berubah.

> ⚠️ **Peringatan keamanan**: `cups-test` saat ini mem-publish port `631` ke
> `0.0.0.0` dan `[::]` (semua interface, termasuk yang berpotensi terjangkau dari
> luar LAN jika STB punya port-forwarding/tunnel apa pun ke Internet). Ini
> melanggar aturan "CUPS tidak boleh diekspos ke Internet". Backend aplikasi ini
> menjangkau CUPS lewat **Docker network internal** (`cups-network`), jadi publish
> port host `631` sebenarnya **tidak diperlukan** lagi setelah Phase 1 berjalan.
>
> Rekomendasi: pada compose file yang menjalankan `cups-test`, hapus/comment baris
> `ports: - "631:631"` (dan variannya), lalu `docker compose up -d` ulang container
> tersebut. Setelah itu CUPS hanya bisa diakses dari container lain yang
> tergabung di network yang sama — persis seperti arsitektur yang ditargetkan.
> Jangan lakukan ini tanpa konfirmasi jika ada perangkat/skrip lain yang memang
> sengaja mengakses `http://STB-IP:631` langsung dari LAN.

---

## 1. Salin project ke STB

Login ke STB, lalu clone repository langsung dari GitHub:

```bash
ssh user@STB-IP
mkdir -p /opt/cups-print-manager
git clone https://github.com/bruriwijayanto/print-ui.git /opt/cups-print-manager
cd /opt/cups-print-manager
```

`.env` sengaja tidak ikut ter-clone (masuk `.gitignore`) — dibuat baru langsung di
STB pada langkah 3, jangan pernah commit secret ke Git.

Untuk update ke commit terbaru di kemudian hari:

```bash
cd /opt/cups-print-manager
git pull
docker compose up -d --build
```

---

## 2. Hubungkan network ke CUPS existing

Aplikasi ini **tidak** membuat container CUPS baru — ia harus join network yang sama
dengan `cups-test` yang sudah berjalan.

```bash
docker network create cups-network
docker network connect cups-network cups-test
```

Perintah ini aman dijalankan berkali-kali; jika network/koneksi sudah ada, Docker akan
menampilkan error yang bisa diabaikan (`network already exists` / `already connected`).

Verifikasi `cups-test` benar-benar tergabung:

```bash
docker network inspect cups-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

Harus muncul `cups-test` dalam daftar.

---

## 3. Buat file environment

```bash
cp .env.example .env
nano .env   # atau editor lain
```

Minimal yang wajib disesuaikan:

```env
CUPS_SERVER=http://cups-test:631
PRINT_API_KEY=<ganti-dengan-key-acak-yang-kuat>
BACKEND_PORT=8000
```

`CUPS_USER` / `CUPS_PASSWORD` **boleh dikosongkan** untuk Phase 1 (endpoint read-only
tidak butuh autentikasi CUPS). Baru diperlukan saat Phase 2/3 (print & admin job)
jika `cups-test` mensyaratkan auth untuk operasi tersebut.

Jangan commit `.env` ke Git — sudah masuk `.gitignore`.

---

## 4. Build & jalankan

```bash
docker compose up -d --build
```

Build pertama kali akan lebih lama karena `pycups` dikompilasi dari source
(butuh `gcc` + `libcups2-dev`, sudah otomatis di-install di dalam Dockerfile).

---

## 5. Verifikasi

```bash
docker compose ps
```

Pastikan `cups-print-backend` berstatus `Up` dan (setelah healthcheck interval
pertama, ~30 detik) `healthy`.

```bash
curl http://localhost:8000/api/health
```

Hasil yang diharapkan jika koneksi ke CUPS berhasil:

```json
{"status": "ok", "cups": "connected", "printers": 1}
```

Jika muncul `{"status": "degraded", "cups": "disconnected"}` (HTTP 503) — **jangan
lanjut** sebelum ini teratasi. Lihat bagian Troubleshooting di README.md.

```bash
curl http://localhost:8000/api/printers
```

Harus menampilkan `Canon-G2030` dengan data asli dari CUPS (state, description,
device_uri, dll) — bukan data hardcode.

```bash
curl http://localhost:8000/api/printers/Canon-G2030
```

Harus menampilkan detail lengkap termasuk `capabilities` (media, color, duplex,
resolution) sesuai kapabilitas asli PPD `canong2030.ppd`.

Dokumentasi API interaktif:

```text
http://STB-IP:8000/docs
http://STB-IP:8000/openapi.json
```

---

## 6. Logs & debugging

```bash
docker compose logs -f backend
```

Restart setelah mengubah `.env`:

```bash
docker compose up -d --force-recreate backend
```

---

## 7. Akses dari LAN

Selama belum ada frontend/Nginx (Phase 4), akses backend langsung:

```text
http://STB-IP:8000/docs
```

Port `631` (CUPS) **tidak boleh** dipublish ke Internet. Saat ini `cups-test`
(image `manuelklaer/cups-canon:latest`) mem-publish `631` ke `0.0.0.0` — lihat
peringatan keamanan di bagian 0. Idealnya, setelah backend berjalan lewat
`cups-network`, publish port host `631` tersebut dilepas.

---

## 7b. Mengarahkan domain via Cloudflare Tunnel

`cloudflared` di server ini jalan sebagai systemd service dengan tunnel
`oramyid-ssh` (UUID `bd875309-e855-4b38-999c-06031dc7163b`) di domain `ora.my.id`.

> **Penting — tunnel ini remotely-managed (dikelola dari dashboard).**
> `/etc/cloudflared/config.yml` di server ini punya bagian `ingress:` lokal, tapi
> bagian itu **diabaikan** oleh cloudflared. Terbukti dari
> `journalctl -u cloudflared`: konfigurasi ingress yang benar-benar dipakai saat
> runtime (baris log `Updated to new configuration config=...`) berisi hostname
> (`waha.ora.my.id`, `lib.ora.my.id`, `chat.ora.my.id`, dst) dan port (mis. `gowa`
> ke `http://localhost:8011`) yang **tidak sama** dengan isi file lokal — artinya
> routing sebenarnya ditarik dari Cloudflare Zero Trust dashboard, bukan dari
> file di server. Menambah entri `ingress` di file lokal untuk tunnel ini
> **tidak berpengaruh apa pun**, walau `cloudflared tunnel route dns` (membuat
> CNAME) tetap berhasil dan perlu dijalankan.
>
> File lokal tetap dipakai untuk `tunnel:` dan `credentials-file:` (identitas
> tunnel), hanya bagian `ingress:`-nya yang mati untuk kasus ini.

### Langkah yang benar: tambahkan Public Hostname di dashboard

1. Buka **https://one.dash.cloudflare.com** (login akun Cloudflare yang sama).
2. **Networks** → **Tunnels** → pilih tunnel **`oramyid-ssh`**.
3. Tab **Public Hostname** → **Add a public hostname**.
4. Isi:
   - Subdomain: `printer`
   - Domain: `ora.my.id`
   - Path: kosongkan
   - Service → Type: `HTTP`, URL: `localhost:8000` (Phase 1, langsung ke backend;
     ganti ke `localhost:8080` setelah frontend/Nginx Phase 4 selesai)
5. **Save**.

Perubahan aktif dalam hitungan detik — **tidak perlu** `systemctl restart cloudflared`
untuk tunnel dashboard-managed.

Kalau DNS record `printer.ora.my.id` belum ada (biasanya otomatis dibuat saat Save di
langkah 4), pastikan dengan:

```bash
sudo cloudflared tunnel route dns oramyid-ssh printer.ora.my.id
```

> ⚠️ **Jangan pernah** menambahkan public hostname yang mengarah ke `localhost:631`
> (CUPS).

### Verifikasi

```bash
curl -sS -w '\nHTTP_CODE:%{http_code}\n' https://printer.ora.my.id/api/health
```

Harus mengembalikan response yang sama seperti `curl http://localhost:8000/api/health`
di langkah 5, tapi sekarang lewat HTTPS publik via Cloudflare. Kalau masih 404, cek
lagi apakah hostname benar-benar tersimpan di tab Public Hostname; kalau 502, berarti
hostname sudah kebaca tapi backend belum jalan di `localhost:8000` (jalankan langkah 4).

> Catatan non-mendesak: `cloudflared tunnel list` melaporkan versi terpasang
> (`2025.7.0`) sudah outdated, direkomendasikan upgrade ke `2026.8.3` — tidak
> menghalangi langkah di atas, bisa dijadwalkan terpisah.

---

## 8. Uninstall / rollback

```bash
docker compose down
```

Ini tidak menyentuh container `cups-test` — hanya menghentikan
`cups-print-backend`. Untuk melepas `cups-test` dari network aplikasi (opsional):

```bash
docker network disconnect cups-network cups-test
```

---

## Checklist acceptance Phase 1

```text
[ ] docker compose up -d --build berhasil tanpa error
[ ] docker compose ps menunjukkan backend healthy
[ ] /api/health mengembalikan status "ok", cups "connected"
[ ] /api/printers menampilkan Canon-G2030 dengan data asli
[ ] /api/printers/Canon-G2030 menampilkan detail & capabilities asli
[ ] /docs dan /openapi.json dapat diakses
[ ] Port 631 (CUPS) tidak terekspos ke Internet
```

Jika semua tercentang, laporkan hasilnya (terutama output `/api/printers`) agar
implementasi dapat lanjut ke **Phase 2 — Print API**.
