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

Dari mesin development:

```bash
rsync -avz --exclude '.env' --exclude '.git' \
  /Volumes/Data/www/htdocs7.4/print-ui/ \
  user@STB-IP:/opt/cups-print-manager/
```

Atau via `git clone`/`scp`, sesuai preferensi Anda. Jangan ikut menyalin file `.env`
(mengandung secret) — buat baru langsung di STB pada langkah 3.

Login ke STB:

```bash
ssh user@STB-IP
cd /opt/cups-print-manager
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
