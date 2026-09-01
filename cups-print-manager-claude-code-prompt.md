# CUPS Print Manager — Prompt untuk Claude Code

## Peran

Anda adalah Senior Software Engineer yang ahli dalam:

- CUPS / Common UNIX Printing System
- IPP / Internet Printing Protocol
- Linux Print Server
- Docker dan Docker Compose
- ARM64 / aarch64
- Python FastAPI
- React + Vite + TypeScript
- Tailwind CSS
- shadcn/ui
- REST API
- Secure File Upload
- Printer Job Management

Saya ingin membangun aplikasi web bernama **CUPS Print Manager**.

Aplikasi ini menjadi Web UI dan REST API untuk mengelola printer yang terhubung ke server Linux melalui CUPS.

---

## 0. INSTRUKSI KHUSUS UNTUK CLAUDE CODE

Anda bekerja sebagai coding agent menggunakan **Claude Code**.

Ikuti workflow berikut:

1. Sebelum coding, inspeksi repository saat ini.
2. Baca file yang relevan, termasuk `README`, konfigurasi Docker, dan source code yang sudah ada.
3. Jangan menghapus atau mengganti konfigurasi yang sudah bekerja tanpa alasan yang jelas.
4. Gunakan tools Claude Code untuk:
   - membaca file
   - mencari kode
   - membuat/edit file
   - menjalankan command
   - menjalankan test
5. Setelah setiap fase, jalankan test/build yang relevan.
6. Jika menemukan error, diagnosis dan perbaiki sebelum melanjutkan.
7. Jangan mengarang hasil command.
8. Jangan menganggap CUPS tersedia jika belum diuji.
9. Jangan menggunakan mock printer atau fake job untuk production.
10. Jangan berhenti hanya setelah source code dibuat. Pastikan aplikasi benar-benar dapat dibuild dan dijalankan dengan Docker.
11. Prioritaskan implementasi sederhana dan stabil karena target server adalah STB ARM64 dengan resource terbatas.

### Aturan kerja

Jangan langsung membuat seluruh aplikasi.

Kerjakan secara bertahap:

- Phase 0 — inspeksi environment
- Phase 1 — Docker + FastAPI + CUPS
- Phase 2 — Print API
- Phase 3 — Job Management
- Phase 4 — React Frontend
- Phase 5 — Authentication + Security
- Phase 6 — Production Docker
- Phase 7 — Cloudflare Tunnel documentation

Setelah satu phase selesai, test terlebih dahulu sebelum lanjut.

---

# 1. TUJUAN APLIKASI

Aplikasi harus memungkinkan user:

1. Melihat daftar printer dari CUPS.
2. Melihat status printer.
3. Melihat print queue.
4. Upload file untuk dicetak.
5. Memilih printer.
6. Mengatur opsi print.
7. Mengirim print job ke CUPS.
8. Melihat status print job.
9. Melihat history print job.
10. Membatalkan print job.
11. Melihat detail printer.
12. Melihat error CUPS.
13. Menyediakan REST API agar aplikasi lain dapat mengirim dokumen untuk dicetak.

Aplikasi harus benar-benar menggunakan CUPS.

**Jangan membuat data printer/job palsu sebagai implementasi production.**

---

# 2. ENVIRONMENT AKTUAL

Target deployment:

- Linux STB
- Armbian
- ARM64 / aarch64
- Docker
- Docker Compose

Host STB hanya diharapkan membutuhkan:

- Docker
- Docker Compose

Jangan membutuhkan instalasi berikut di host:

- Node.js
- npm
- Python
- pip
- package system untuk aplikasi

Semua dependency aplikasi harus berada di Docker container.

---

# 3. CUPS YANG SUDAH ADA

Saat ini CUPS sudah berjalan di Docker.

Container:

```text
cups-test
```

Printer:

```text
Canon-G2030
```

Printer model:

```text
Canon G2030 series
```

Device URI:

```text
usb://Canon/G2030%20series?serial=008FFE&interface=1
```

Driver:

```text
canong2030.ppd
```

Printer sudah berhasil melakukan test print menggunakan CUPS.

USB printer sudah terlihat dari dalam container CUPS.

**PENTING:**

Jangan membuat container CUPS baru jika tidak diperlukan.

Pertahankan existing CUPS container.

Aplikasi baru harus dapat berkomunikasi dengan CUPS existing.

---

# 4. ARSITEKTUR

Gunakan:

```text
                    INTERNET
                       |
                       | HTTPS
                       v
              Cloudflare Tunnel
                       |
                       v
             +-------------------+
             | CUPS Print Manager|
             |                   |
             | React + Nginx     |
             +---------+---------+
                       |
                       | /api
                       v
             +-------------------+
             | FastAPI Backend   |
             +---------+---------+
                       |
                       | IPP / CUPS
                       v
             +-------------------+
             | Existing CUPS     |
             | cups-test         |
             +---------+---------+
                       |
                       | USB
                       v
             +-------------------+
             | Canon G2030       |
             +-------------------+
```

CUPS tidak boleh diekspos langsung ke Internet.

Public endpoint hanya Web UI/API.

---

# 5. DOCKER-ONLY DEPLOYMENT

Aplikasi harus dapat dijalankan dengan:

```bash
docker compose up -d --build
```

Tidak boleh membutuhkan:

```bash
npm install
pip install
python app.py
node server.js
```

di host STB.

---

# 6. DOCKER COMPOSE

Buat:

```text
docker-compose.yml
```

Minimal:

```yaml
services:

  backend:
    build:
      context: ./backend
    container_name: cups-print-backend
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
    container_name: cups-print-frontend
    restart: unless-stopped
```

Jika CUPS existing berada di Docker container terpisah, dokumentasikan cara menghubungkannya ke network aplikasi.

Contoh:

```bash
docker network create cups-network
docker network connect cups-network cups-test
```

Backend kemudian dapat menggunakan:

```env
CUPS_SERVER=http://cups-test:631
```

Jangan hardcode nama container di source code.

Gunakan environment variable.

---

# 7. DOCKER NETWORK

Gunakan network:

```text
cups-network
```

Backend harus dapat mengakses CUPS melalui network Docker.

Frontend hanya perlu mengakses backend.

Browser tidak boleh membutuhkan akses langsung ke CUPS.

---

# 8. ARM64

Semua image harus mendukung:

```text
linux/arm64
```

Target:

```text
aarch64
```

Periksa compatibility image sebelum digunakan.

Prioritaskan image:

```text
python:3.x-slim
node:22-alpine
nginx:alpine
```

atau image resmi/terpercaya lain yang mendukung ARM64.

Jangan menggunakan image yang hanya mendukung AMD64.

---

# 9. BACKEND

Gunakan:

```text
Python
FastAPI
```

Backend berjalan dalam Docker.

Gunakan production-oriented Uvicorn.

Contoh:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

# 10. CUPS SERVICE

Buat:

```text
backend/app/services/cups.py
```

Implementasikan abstraction:

```python
class CupsService:

    list_printers()
    get_printer(name)
    get_printer_attributes(name)
    list_jobs()
    get_job(job_id)
    submit_print_job()
    cancel_job(job_id)
    pause_printer(name)
    resume_printer(name)
    enable_printer(name)
    disable_printer(name)
```

Jangan mencampurkan logic CUPS dengan FastAPI route.

---

# 11. CUPS LIBRARY

Prioritaskan:

```text
pycups
```

atau library IPP yang kompatibel.

Jika pycups membutuhkan system package:

install di Dockerfile backend.

Jangan meminta user melakukan `apt install` di host.

Jika pycups sulit digunakan pada environment ARM64:

buat fallback menggunakan:

```text
lp
lpstat
lpadmin
cancel
```

melalui `subprocess`.

Gunakan argument list.

Jangan pernah:

```python
os.system(user_input)
```

atau shell command yang memungkinkan injection.

---

# 12. ENVIRONMENT VARIABLES

Buat:

```text
.env.example
```

Minimal:

```env
CUPS_SERVER=http://cups-test:631
PRINT_API_KEY=change-this-key
MAX_UPLOAD_SIZE_MB=50
POLL_INTERVAL_SECONDS=5
CORS_ORIGINS=http://localhost:8080
TZ=Asia/Jakarta
FRONTEND_PORT=8080
BACKEND_PORT=8000
```

Jangan commit `.env`.

---

# 13. HEALTH CHECK

Endpoint:

```http
GET /api/health
```

Jika CUPS aktif:

```json
{
  "status": "ok",
  "cups": "connected",
  "printers": 1
}
```

Jika CUPS tidak tersedia:

```json
{
  "status": "degraded",
  "cups": "disconnected"
}
```

Backend harus dapat reconnect ketika CUPS kembali aktif.

---

# 14. API ENDPOINTS

Implementasikan:

```http
GET /api/health

GET /api/printers

GET /api/printers/{printer_name}

GET /api/printers/{printer_name}/jobs

GET /api/jobs

GET /api/jobs/{job_id}

POST /api/print

DELETE /api/jobs/{job_id}

POST /api/printers/{printer_name}/pause

POST /api/printers/{printer_name}/resume

POST /api/printers/{printer_name}/enable

POST /api/printers/{printer_name}/disable
```

FastAPI harus menyediakan:

```text
/docs
/openapi.json
```

---

# 15. PRINTER LIST

`GET /api/printers`

Ambil data langsung dari CUPS.

Jangan hardcode:

```text
Canon-G2030
```

Jika CUPS memiliki beberapa printer, semuanya harus muncul.

Informasi minimal:

```text
name
description
state
state_message
accepting_jobs
shared
device_uri
current_job
queue_count
```

---

# 16. PRINTER STATUS

Gunakan status aktual dari CUPS.

Contoh status:

```text
IDLE
PRINTING
STOPPED
ERROR
UNKNOWN
```

Jangan membuat status berdasarkan asumsi.

Jika informasi tidak tersedia:

```text
UNKNOWN
```

---

# 17. PRINTER CAPABILITIES

Ambil capability dari CUPS jika tersedia.

Contoh:

```text
media
color
duplex
resolution
copies
page ranges
orientation
```

Jika printer tidak mendukung fitur tertentu:

**Jangan tampilkan option tersebut sebagai option yang aktif.**

Jangan membuat capability palsu.

---

# 18. PRINT DOCUMENT

Endpoint:

```http
POST /api/print
```

multipart/form-data:

```text
file
printer
copies
page_ranges
media
orientation
color
duplex
```

Minimal dukung:

```text
PDF
PNG
JPG
JPEG
TXT
```

Architecture harus mudah diperluas untuk:

```text
DOCX
XLSX
PPTX
```

---

# 19. FILE SECURITY

Upload harus divalidasi:

- extension
- MIME type
- file size
- filename
- path traversal
- executable file

Gunakan UUID untuk temporary path.

Contoh:

```text
/tmp/cups-print-jobs/<uuid>/
```

Jangan menggunakan filename user sebagai filesystem path.

Maximum file size:

```env
MAX_UPLOAD_SIZE_MB=50
```

Setelah job selesai, hapus temporary file jika aman dilakukan.

---

# 20. PRINT RESPONSE

Jika job berhasil diterima CUPS:

```json
{
  "success": true,
  "job_id": "Canon-G2030-15",
  "printer": "Canon-G2030",
  "filename": "document.pdf",
  "status": "queued"
}
```

Penting:

**Request berhasil ≠ print job selesai.**

Status `completed` hanya boleh digunakan jika CUPS benar-benar melaporkan job selesai.

---

# 21. JOB MANAGEMENT

Endpoint:

```http
GET /api/jobs
```

Tampilkan:

```text
Job ID
Printer
Document
User
Submitted
Status
```

Status:

```text
PENDING
PROCESSING
COMPLETED
CANCELED
FAILED
```

Mapping status harus berasal dari CUPS.

Jangan membuat progress percentage palsu.

Jika CUPS tidak menyediakan progress:

```text
Printing...
```

---

# 22. CANCEL JOB

Endpoint:

```http
DELETE /api/jobs/{job_id}
```

Gunakan operasi cancel CUPS.

Hanya job yang masih dapat dibatalkan yang boleh dicancel.

History tidak boleh dihapus.

---

# 23. REALTIME / POLLING

Untuk versi pertama gunakan polling agar sederhana dan ringan untuk STB.

TanStack Query:

```text
refetchInterval = 5000
```

Job:

```text
3-5 seconds
```

Printer:

```text
5 seconds
```

Jangan polling terlalu agresif.

WebSocket boleh dibuat sebagai enhancement, bukan requirement awal.

---

# 24. AUTHENTICATION

Gunakan API Key.

Environment:

```env
PRINT_API_KEY=change-me
```

Request:

```http
Authorization: Bearer <API_KEY>
```

Buat FastAPI dependency:

```text
get_current_api_key()
```

Jangan hardcode API key.

Jangan menampilkan API key dalam log.

---

# 25. FRONTEND

Gunakan:

```text
React
Vite
TypeScript
Tailwind CSS
shadcn/ui
TanStack Query
lucide-react
```

Gunakan TypeScript strict mode.

Hindari penggunaan `any` secara sembarangan.

---

# 26. FRONTEND PAGES

Buat:

```text
/dashboard
/printers
/printers/:printerName
/print
/jobs
/jobs/:jobId
/settings
```

Sidebar:

```text
Dashboard
Printers
Print
Jobs
Settings
```

---

# 27. DASHBOARD

Tampilkan:

```text
Total Printers
Online
Printing
Queued Jobs
Completed Today
Failed Today
```

Printer Status table:

```text
Printer
Status
Current Job
Queue
Last Updated
Action
```

Recent Jobs:

```text
Job
Printer
Document
Status
Time
```

---

# 28. PRINTER PAGE

`/printers`

Tampilkan semua printer CUPS.

Kolom:

```text
Printer
Status
Queue
Current Job
Accepting Jobs
Actions
```

Gunakan badge status.

---

# 29. PRINTER DETAIL

`/printers/:printerName`

Tampilkan:

```text
Name
Description
Location
State
State Message
Device URI
Manufacturer
Model
Accepting Jobs
Shared
```

Capabilities:

```text
Paper
Color
Duplex
Resolution
Copies
```

Actions:

```text
Pause
Resume
Enable
Disable
Print
```

Hanya tampilkan action yang relevan.

---

# 30. PRINT PAGE

`/print`

Buat UI:

```text
Upload File

Drag & Drop

[ Choose File ]
```

Setelah file dipilih:

```text
Filename
File Size
File Type
Preview jika memungkinkan
```

Options:

```text
Printer
Copies
Pages
Paper
Orientation
Color
Duplex
```

Button:

```text
PRINT DOCUMENT
```

---

# 31. PRINT SUCCESS

Setelah job diterima CUPS:

```text
Print job submitted

Printer:
Canon G2030

Job:
#15

Status:
Queued
```

Buttons:

```text
View Job
Print Another
```

---

# 32. JOBS PAGE

`/jobs`

Tampilkan history:

```text
Job ID
Printer
Document
User
Submitted
Status
Action
```

Klik job untuk detail.

---

# 33. JOB DETAIL

`/jobs/:jobId`

Tampilkan:

```text
Job ID
Printer
Document
Owner
Submitted At
Started At
Completed At
Status
Options
Error
```

Timeline:

```text
Submitted
   ↓
Queued
   ↓
Printing
   ↓
Completed
```

Jika gagal:

```text
Submitted
   ↓
Queued
   ↓
Failed
```

---

# 34. API CLIENT

Buat:

```text
frontend/src/lib/api.ts
```

Jangan melakukan HTTP request tersebar di component.

Buat abstraction:

```text
printerApi
jobApi
printApi
```

Contoh:

```typescript
printerApi.getPrinters()
jobApi.getJobs()
printApi.printDocument()
```

---

# 35. NGINX

Frontend production menggunakan:

```text
Nginx
```

Nginx harus:

1. Serve React static files.
2. Proxy `/api/*` ke backend.

Browser cukup mengakses:

```text
http://STB-IP:8080
```

Tidak perlu membuka backend port dari browser.

---

# 36. FRONTEND DOCKERFILE

Gunakan multi-stage build.

Stage 1:

```text
node:22-alpine
```

Build:

```bash
npm ci
npm run build
```

Stage 2:

```text
nginx:alpine
```

Copy:

```text
dist/
```

ke Nginx.

Host STB tidak membutuhkan Node.js.

---

# 37. BACKEND DOCKERFILE

Gunakan:

```text
python:3.12-slim
```

Install dependency di container.

Expose:

```text
8000
```

Run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

# 38. HEALTHCHECK DOCKER

Backend healthcheck:

```http
GET /api/health
```

CUPS healthcheck jika memungkinkan.

Frontend healthcheck menggunakan Nginx.

Backend tidak dianggap healthy jika CUPS tidak dapat diakses.

---

# 39. PERSISTENCE

Versi pertama tidak membutuhkan database.

CUPS sudah menangani print jobs.

Jika membutuhkan persistence aplikasi:

siapkan abstraction agar PostgreSQL dapat ditambahkan kemudian.

Jangan menambahkan PostgreSQL hanya untuk kebutuhan yang belum diperlukan.

---

# 40. LOGGING

Gunakan structured logging.

Log:

```text
print request
printer
job id
user
status
error
```

Jangan log:

```text
API key
password
document contents
```

Gunakan:

```bash
docker compose logs -f backend
```

untuk debugging.

---

# 41. ERROR HANDLING

Tangani:

```text
CUPS unavailable
Printer unavailable
Printer stopped
Printer paused
USB disconnected
Invalid printer
Invalid file
File too large
Print failed
Permission denied
Timeout
Authentication failure
```

Response:

```json
{
  "success": false,
  "error": {
    "code": "PRINTER_UNAVAILABLE",
    "message": "Printer Canon-G2030 is currently unavailable"
  }
}
```

Jangan mengirim stack trace kepada user.

Stack trace hanya masuk log.

---

# 42. SECURITY

Implementasikan:

- API authentication
- CORS
- upload validation
- maximum upload size
- path traversal protection
- filename sanitization
- safe subprocess
- rate limiting sederhana
- timeout
- secure HTTP headers
- printer name validation

CUPS tidak boleh diekspos ke Internet.

---

# 43. DOCKER PORT

Development:

```text
Frontend: 8080
Backend: 8000
CUPS: 631
```

CUPS:

```text
631
```

tidak boleh dipublish ke Internet.

Production sebaiknya hanya mempublikasikan frontend:

```text
8080:80
```

Backend dapat tetap internal Docker network.

---

# 44. CLOUDflare TUNNEL

Sediakan dokumentasi OPTIONAL untuk Cloudflare Tunnel.

Architecture:

```text
https://print.example.com
        ↓
Cloudflare Tunnel
        ↓
STB:8080
        ↓
Frontend Nginx
        ↓
FastAPI
        ↓
CUPS
        ↓
Canon G2030
```

Jangan expose:

```text
CUPS :631
```

ke Internet.

Cloudflare Tunnel bukan dependency aplikasi development.

---

# 45. PROJECT STRUCTURE

Gunakan:

```text
cups-print-manager/

├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .dockerignore
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   │
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   ├── printers.py
│   │   │   ├── jobs.py
│   │   │   └── print.py
│   │   │
│   │   ├── services/
│   │   │   ├── cups.py
│   │   │   ├── printer_service.py
│   │   │   └── print_service.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── printer.py
│   │   │   ├── job.py
│   │   │   └── print.py
│   │   │
│   │   └── utils/
│   │       ├── files.py
│   │       └── security.py
│   │
│   └── tests/
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.ts
│   ├── .dockerignore
│   │
│   └── src/
│       ├── components/
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── Printers.tsx
│       │   ├── PrinterDetail.tsx
│       │   ├── Print.tsx
│       │   ├── Jobs.tsx
│       │   ├── JobDetail.tsx
│       │   └── Settings.tsx
│       │
│       ├── lib/
│       │   ├── api.ts
│       │   └── utils.ts
│       │
│       └── types/
│
└── scripts/
    ├── healthcheck.sh
    └── deploy.sh
```

Sesuaikan struktur jika repository sudah memiliki struktur yang lebih baik. Jangan memaksakan struktur ini jika bertentangan dengan codebase existing.

---

# 46. README

README harus menjelaskan:

## Requirements

```text
Docker
Docker Compose
```

## Environment

```bash
cp .env.example .env
```

## Existing CUPS

Jelaskan cara menghubungkan:

```text
cups-test
```

ke network aplikasi:

```bash
docker network create cups-network
docker network connect cups-network cups-test
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

```text
http://STB-IP:8080
```

## API

```text
http://STB-IP:8080/docs
```

## Test print

Berikan contoh curl:

```bash
curl -X POST \
  http://STB-IP:8080/api/print \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@test.pdf" \
  -F "printer=Canon-G2030" \
  -F "copies=1"
```

---

# 47. BACKUP

README harus menjelaskan backup:

- CUPS configuration
- Docker volumes
- `.env`
- application configuration

Jangan menyimpan secret di Git.

---

# 48. TESTING

Backend:

- health
- CUPS connection
- printer list
- printer detail
- print validation
- invalid printer
- upload validation
- cancel job
- authentication

Frontend:

- dashboard
- printer list
- printer detail
- upload form
- print submission
- job status
- job cancellation
- error state

Mock CUPS hanya boleh digunakan untuk unit test.

Production harus menggunakan CUPS nyata.

---

# 49. ACCEPTANCE TEST

Aplikasi dianggap selesai jika:

```text
[ ] Docker build berhasil di ARM64
[ ] docker compose up -d berhasil
[ ] semua container berjalan
[ ] frontend dapat dibuka
[ ] backend dapat diakses
[ ] backend dapat connect ke CUPS
[ ] Canon-G2030 muncul
[ ] status Canon-G2030 muncul
[ ] file dapat diupload
[ ] print job dapat dibuat
[ ] printer benar-benar mencetak
[ ] job status mengikuti CUPS
[ ] completed job dapat dilihat
[ ] queued job dapat dibatalkan
[ ] API authentication bekerja
[ ] file validation bekerja
[ ] CUPS tidak diekspos ke Internet
[ ] aplikasi dapat diakses melalui LAN
[ ] Cloudflare Tunnel documentation tersedia
```

---

# 50. PHASE 0 — INSPEKSI

Sebelum coding:

1. Periksa repository.
2. Periksa apakah ada source code existing.
3. Periksa Dockerfile existing.
4. Periksa docker-compose existing.
5. Periksa `.env`.
6. Periksa konfigurasi network.
7. Periksa apakah project sudah menggunakan React/FastAPI.
8. Jangan menghapus konfigurasi existing.
9. Periksa apakah CUPS dapat diakses dari environment development.

Gunakan command yang sesuai.

Setelah inspeksi, tampilkan ringkasan:

```text
Environment
Architecture
Existing Docker services
Existing CUPS
Existing project structure
Potential conflicts
Recommended implementation plan
```

Kemudian mulai Phase 1.

---

# 51. PHASE 1 — FASTAPI + CUPS

Implementasikan:

```http
GET /api/health
GET /api/printers
GET /api/printers/{printer_name}
```

Target:

Backend dapat membaca:

```text
Canon-G2030
```

dari existing CUPS.

Test menggunakan:

```bash
curl
```

Jangan lanjut jika koneksi CUPS belum berhasil.

---

# 52. PHASE 2 — PRINT API

Implementasikan:

```http
POST /api/print
```

Test menggunakan PDF nyata.

Pastikan:

```text
Browser/API
    ↓
FastAPI
    ↓
CUPS
    ↓
Canon G2030
```

benar-benar menghasilkan print.

---

# 53. PHASE 3 — JOB MANAGEMENT

Implementasikan:

```http
GET /api/jobs
GET /api/jobs/{id}
DELETE /api/jobs/{id}
```

Pastikan status berasal dari CUPS.

---

# 54. PHASE 4 — FRONTEND

Implementasikan:

```text
Dashboard
Printers
Printer Detail
Print
Jobs
Job Detail
Settings
```

Gunakan data API nyata.

Jangan menggunakan mock data untuk production.

---

# 55. PHASE 5 — SECURITY

Implementasikan:

```text
API Key
CORS
upload validation
rate limiting
secure headers
safe subprocess
```

Test authentication.

---

# 56. PHASE 6 — PRODUCTION DOCKER

Pastikan:

```bash
docker compose build
docker compose up -d
```

berhasil pada ARM64.

Optimalkan ukuran image.

Jangan menambahkan dependency yang tidak diperlukan.

---

# 57. PHASE 7 — CLOUDFLARE TUNNEL

Buat dokumentasi untuk:

```text
Internet
  ↓
Cloudflare Tunnel
  ↓
STB:8080
  ↓
CUPS Print Manager
  ↓
CUPS
  ↓
Printer
```

Jangan expose port 631.

---

# 58. DEVELOPMENT RULES

Selama implementasi:

1. Jangan membuat fake functionality.
2. Jangan hardcode printer.
3. Jangan hardcode API key.
4. Jangan hardcode CUPS hostname.
5. Jangan expose CUPS ke Internet.
6. Jangan menjalankan dependency installation di host.
7. Jangan menggunakan shell injection.
8. Jangan membuat progress print palsu.
9. Jangan menambahkan database jika belum diperlukan.
10. Jangan menambahkan Redis/RabbitMQ/Kubernetes untuk versi pertama.
11. Prioritaskan kestabilan pada STB ARM64.
12. Setiap fitur harus memiliki loading/error/empty state.
13. Setiap perubahan harus dites.

---

# 59. FINAL USER EXPERIENCE

Hasil akhir harus memungkinkan:

```text
User
  ↓
https://print.example.com
  ↓
Login
  ↓
Dashboard
  ↓
Printers
  ↓
Canon G2030
  ↓
Print
  ↓
Upload PDF
  ↓
Select Canon G2030
  ↓
Set copies/options
  ↓
Print
  ↓
Job ID
  ↓
Queued
  ↓
Printing
  ↓
Completed
```

User tidak perlu mengetahui detail CUPS.

---

# 60. MULAI SEKARANG

Mulai dari:

## PHASE 0

Jangan langsung membuat seluruh aplikasi.

Pertama:

1. Inspect repository.
2. Inspect existing Docker setup.
3. Inspect existing CUPS setup.
4. Verify ARM64 compatibility.
5. Verify connectivity to `cups-test`.
6. Buat implementation plan.
7. Setelah itu implementasikan Phase 1.

Pada akhir Phase 1 tampilkan:

- struktur file
- file yang dibuat/diubah
- Dockerfile
- docker-compose configuration
- `.env.example`
- cara menjalankan
- hasil `docker compose ps`
- hasil `/api/health`
- hasil `/api/printers`
- hasil test CUPS
- masalah yang ditemukan dan solusinya

**Jangan lanjut ke Phase 2 sebelum Phase 1 benar-benar berhasil.**
