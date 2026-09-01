# CUPS Print Manager

Web UI dan REST API untuk mengelola printer yang terhubung ke server Linux melalui CUPS.

Status implementasi saat ini: **Phase 1 — FastAPI + CUPS (printers read-only, health check)**.

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

- API: `http://STB-IP:8000/api/health`, `http://STB-IP:8000/api/printers`
- Docs: `http://STB-IP:8000/docs`

(Frontend & Nginx reverse proxy akan menggantikan akses langsung ke port backend pada Phase 4.)

## Test print

Fitur print (`POST /api/print`) belum diimplementasikan — akan hadir di Phase 2.

## Troubleshooting

Jika `/api/health` mengembalikan `{"status": "degraded", "cups": "disconnected"}`:

1. Pastikan container `cups-test` berjalan: `docker ps`
2. Pastikan `cups-test` sudah di-connect ke network `cups-network`.
3. Pastikan `CUPS_SERVER` di `.env` sesuai nama container CUPS.
4. Cek log backend: `docker compose logs -f backend`

Jika operasi admin (pause/resume/enable/disable/print/cancel — Phase 2/3) gagal dengan
"Unauthorized": CUPS mensyaratkan autentikasi untuk operasi tersebut. Buat user pada
`cups-test` yang tergabung di grup `lpadmin`, lalu isi `CUPS_USER`/`CUPS_PASSWORD` di `.env`.
Endpoint read-only (printer list/detail) tidak memerlukan ini.

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
