# CUPS Print Manager

Web UI dan REST API untuk mengelola printer yang terhubung ke server Linux melalui CUPS.

Status implementasi saat ini: **Phase 4 — Frontend** selesai, ditambah **autentikasi
API Key** (bagian dari Phase 5) untuk `/api/printers`, `/api/print`, `/api/jobs`
(di atas Phase 1: health check, Phase 2: `POST /api/print`, Phase 3: Job Management).
Item Phase 5 lain (rate limiting, secure headers tambahan) masih menyusul.

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

## Backup

Yang perlu di-backup secara berkala:

- Konfigurasi CUPS pada container `cups-test` (`/etc/cups/`, PPD di `/etc/cups/ppd/`)
- File `.env` (simpan di tempat aman, **jangan** commit ke Git)
- Docker volumes terkait CUPS, jika ada

`.env` sudah masuk `.gitignore` — jangan pernah commit secret ke repository.
