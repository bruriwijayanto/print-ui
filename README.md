# CUPS Print Manager

Web UI dan REST API untuk mengelola printer yang terhubung ke server Linux melalui CUPS.

Status implementasi saat ini: **Phase 6 — Production Docker selesai** (image backend
dioptimasi jadi multi-stage, 443MB → 194MB), di atas Phase 1-5 (health check, print, job
management, frontend, authentication + security). Phase 7 (dokumentasi Cloudflare Tunnel
mandiri — sebagian sudah ada di `DEPLOY.md`) masih menyusul.

Untuk langkah deploy lengkap ke STB target, lihat [DEPLOY.md](DEPLOY.md).

## Requirements

- Docker
- Docker Compose

Tidak dibutuhkan instalasi Node.js/Python/pip di host — semua dependency ada di dalam container.

## Environment

```bash
cp .env.example .env
```

Sesuaikan `CUPS_SERVER` agar mengarah ke hostname container CUPS yang sudah ada (lihat bagian berikut).

## Menghubungkan ke CUPS existing (`cups-test`)

Aplikasi ini **tidak** membuat container CUPS baru. Ia terhubung ke container CUPS yang sudah berjalan (`cups-test`) melalui Docker network bersama.

```bash
docker network create cups-network
docker network connect cups-network cups-test
```

Backend membaca alamat CUPS dari environment variable, bukan hardcode:

```env
CUPS_SERVER=http://cups-test:631
```

## Start

```bash
docker compose up -d --build
```

## Check

```bash
docker compose ps
```

## Logs

```bash
docker compose logs -f backend
```

## Access

- Web UI: `http://STB-IP:8080` (Nginx serve React build + proxy `/api/*` ke backend)
- API langsung (untuk debugging): `http://STB-IP:8000/api/health`, `http://STB-IP:8000/api/printers`
- Docs: `http://STB-IP:8000/docs`

Browser sehari-hari cukup akses port `8080` — backend port `8000` tetap terbuka di LAN
untuk kebutuhan debugging langsung (curl, Swagger UI), tidak wajib dipublish untuk
end-user.

## Authentication

`/api/printers`, `/api/print`, dan `/api/jobs` sekarang mewajibkan header:

```text
Authorization: Bearer <PRINT_API_KEY>
```

(`PRINT_API_KEY` dari `.env` backend.) `/api/health` tetap terbuka tanpa auth (dipakai
Docker `HEALTHCHECK` dan monitoring). Web UI menanyakan key ini sekali lewat halaman
Login lalu menyimpannya di `localStorage` browser — tidak dikirim ke server lain, dan
tidak pernah ditampilkan di log.

## Rate limiting & secure headers

Semua `/api/*` dibatasi **180 request/menit per IP** (in-memory, per proses backend —
tidak butuh Redis). Ini bukan mekanisme lockout percobaan login khusus (API key 32-byte
acak sudah cukup aman dari brute force), melainkan pengaman umum dari client yang salah
konfigurasi/spam request. Kalau terlampaui, dapat `429 {"code": "RATE_LIMITED"}`.

Nginx (frontend) menambahkan header keamanan berikut ke semua response:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: same-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; ...
```

CSP dibuat ketat (tanpa `unsafe-inline`) karena build React ini tidak punya
`<script>`/`<style>` inline sama sekali — kalau nanti ada perubahan yang butuh resource
eksternal (CDN font, dsb), CSP ini perlu disesuaikan atau build akan gagal diam-diam di
browser (cek DevTools Console untuk violation report kalau ada halaman yang terasa rusak
setelah update).

## Test print

```bash
curl -X POST \
  https://printer.ora.my.id/api/print \
  -H "Authorization: Bearer <PRINT_API_KEY>" \
  -F "file=@test.pdf" \
  -F "printer=Canon-G2030" \
  -F "copies=1"
```

Format didukung saat ini: PDF, PNG, JPG/JPEG, TXT (divalidasi lewat magic bytes, bukan
cuma ekstensi nama file). Response sukses:

```json
{"success": true, "job_id": 42, "printer": "Canon-G2030", "filename": "test.pdf", "status": "queued"}
```

Cek hasilnya benar-benar tercetak dengan `docker exec cups-test lpstat -W completed -o` atau
lewat web UI CUPS di `cups-test`.

## Job management

```bash
curl -H "Authorization: Bearer <PRINT_API_KEY>" https://printer.ora.my.id/api/jobs
curl -H "Authorization: Bearer <PRINT_API_KEY>" https://printer.ora.my.id/api/jobs/3
curl -H "Authorization: Bearer <PRINT_API_KEY>" https://printer.ora.my.id/api/printers/Canon-G2030/jobs
curl -X DELETE -H "Authorization: Bearer <PRINT_API_KEY>" https://printer.ora.my.id/api/jobs/3
```

`GET /api/jobs` menampilkan seluruh history job (bukan cuma yang aktif). Status
(`PENDING`/`PROCESSING`/`COMPLETED`/`CANCELED`/`FAILED`) berasal langsung dari
`job-state` IPP milik CUPS, bukan asumsi. `DELETE` hanya berhasil untuk job yang belum
mencapai status akhir (`COMPLETED`/`CANCELED`/`FAILED`) — job yang sudah selesai akan
ditolak dengan `409 JOB_NOT_CANCELABLE`, dan tidak pernah dihapus dari history.

## Frontend

Halaman yang tersedia: Dashboard, Printers, Printer Detail (dengan action
pause/resume/enable/disable), Print (upload + preview + opsi cetak sesuai capability
printer), Jobs (list + cancel), Job Detail (timeline status), Settings (status koneksi).

Frontend berbicara ke backend lewat path relatif `/api/...` (same-origin, di-proxy oleh
Nginx) — bukan cross-origin — jadi `CORS_ORIGINS` di `.env` backend hanya relevan untuk
klien lain yang mengakses API langsung dari origin berbeda (mis. Postman/curl dari
domain lain), bukan untuk Web UI ini sendiri.

Polling: printers setiap 5 detik, jobs setiap 4 detik (TanStack Query `refetchInterval`),
sesuai batasan resource STB — tidak menggunakan WebSocket.

## Ukuran Docker image (Phase 6)

Backend pakai multi-stage build: stage `builder` install `gcc` + `libcups2-dev` untuk
kompilasi `pycups`, stage final cuma install `libcups2` (runtime saja, tanpa compiler/
header) lewat virtualenv yang di-copy dari stage builder.

```text
backend  : 443MB -> 194MB  (-56%)
frontend : 63MB            (sudah multi-stage sejak awal, tidak berubah)
```

Tervalidasi: 60 test lolos di image baru, dan build ARM64 (`docker buildx build
--platform linux/arm64`) tetap sukses dengan hasil yang sama (220MB) — pengurangan
ukuran konsisten di kedua arsitektur.

## Troubleshooting

Jika `/api/health` mengembalikan `{"status": "degraded", "cups": "disconnected"}`:

1. Pastikan container `cups-test` berjalan: `docker ps`
2. Pastikan `cups-test` sudah di-connect ke network `cups-network`.
3. Pastikan `CUPS_SERVER` di `.env` sesuai nama container CUPS.
4. Cek log backend: `docker compose logs -f backend`

Ada dua jenis "Unauthorized" yang berbeda sumbernya — jangan tertukar:

- **`401 {"code": "UNAUTHORIZED"}`** dari `/api/printers`, `/api/print`, `/api/jobs` →
  ini dari aplikasi kita sendiri: header `Authorization: Bearer <PRINT_API_KEY>` tidak
  ada/salah. Cek `.env` backend, atau login ulang di Web UI.
- Error otorisasi yang **berasal dari CUPS** (biasanya `502 CUPS_ERROR`/`PRINT_FAILED`
  dengan pesan IPP `client-error-not-authorized`) untuk operasi admin
  (pause/resume/enable/disable/cancel): CUPS sendiri mensyaratkan autentikasi untuk
  operasi tersebut. Buat user pada `cups-test` yang tergabung di grup `lpadmin`, lalu
  isi `CUPS_USER`/`CUPS_PASSWORD` di `.env`. Endpoint read-only (printer list/detail)
  tidak memerlukan ini.

Jika container backend tidak pernah menjawab request setelah start (hang setelah log
"Application startup complete" tanpa baris "Uvicorn running on..."): ini pola yang terlihat
saat build/run di-emulasi QEMU (misal build ARM64 di mesin dev x86) akibat `uvloop`. Di
hardware ARM64 asli (STB) seharusnya tidak terjadi karena tidak ada emulasi instruksi. Jika
tetap terjadi di STB, override CMD container dengan `--loop asyncio` untuk memastikan.

### `cups-test` gagal start / job stuck "Waiting for printer to become available"

Container `cups-test` (image `manuelklaer/cups-canon`) mendeklarasikan `/etc/cups` sebagai
**Docker volume** (anonymous jika tidak di-bind eksplisit). Kalau printer USB mati/lepas
saat container ini di-restart, `docker restart`/`docker start` akan **gagal total**
(`error gathering device information ... no such file or directory` untuk device
`/dev/usb/lp0`) karena device mapping-nya tidak bisa dipenuhi. Kalau ini terjadi, job yang
sedang aktif akan macet di status "Waiting for printer to become available" (bukan
completed) sampai printer menyala kembali.

Cara pulihkan:

1. **Jangan** `docker rm` tanpa cek dulu — config asli (`printers.conf`, PPD) ada di
   anonymous volume container itu, bukan di layer image, dan `docker rm` tanpa `-v`
   (default) **tidak** menghapus volume-nya, jadi masih bisa direcover.
2. Cek volume yang menggantung: `docker volume ls` (biasanya nama hash acak, dangling
   sejak container lama dihapus).
3. Intip isinya sebelum dipakai: `docker run --rm -v <VOLUME>:/data:ro alpine ls -la /data`
   — cari yang punya `printers.conf` dan `ppd/Canon-G2030.ppd`.
4. Recreate dengan volume itu ter-mount ke `/etc/cups`, plus device USB yang sekarang
   sudah tersedia lagi:
   ```bash
   docker rm -f cups-test
   docker run -d --name cups-test --restart always -p 631:631 \
     --device /dev/bus/usb:/dev/bus/usb \
     --device /dev/usb/lp0:/dev/usb/lp0 \
     -v <VOLUME-YANG-BENAR>:/etc/cups \
     -e TZ=Asia/Jakarta -e ADMIN_PASSWORD=<password-anda> \
     manuelklaer/cups-canon:latest
   docker network connect cups-network cups-test
   ```
5. Verifikasi: `docker exec cups-test lpstat -p Canon-G2030 -l` harus menunjukkan `idle`,
   bukan lagi "waiting for printer to become available".

Untuk mencegah ini di masa depan, pertimbangkan mem-bind `/etc/cups` ke path host yang
jelas (mis. `-v /opt/cups-config:/etc/cups`) alih-alih membiarkannya jadi anonymous
volume — supaya lebih mudah di-backup dan tidak bergantung pada "menemukan" volume hash
yang tepat lagi di kemudian hari.

## Backup

Yang perlu di-backup secara berkala:

- Konfigurasi CUPS pada container `cups-test` (`/etc/cups/`, PPD di `/etc/cups/ppd/`)
- File `.env` (simpan di tempat aman, **jangan** commit ke Git)
- Docker volumes terkait CUPS, jika ada

`.env` sudah masuk `.gitignore` — jangan pernah commit secret ke repository.
