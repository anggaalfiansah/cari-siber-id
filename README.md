# 🛡️ CaRI-Siber ID – Sistem Intelijen Domain Kognitif & Forensik Ancaman Siber-Sosial

### _Platform Desktop Deteksi Operasi Informasi (CIB), Pemetaan Polarisasi, & Forensik Bukti Digital_

[![Status: Prototype](https://img.shields.io/badge/Status-Prototype%20%2F%20PoC-yellow.svg)](docs/ARSITEKTUR_DAN_ROADMAP_24_7.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-blue.svg)](README.md)
[![Security: SHA-256](https://img.shields.io/badge/Evidence%20Sealing-SHA--256%20ISO%2F27037-success.svg)](docs/PANDUAN_AWAM_DAN_EDUKASI.md)
[![NLP: IndoBERT + BERTopic](https://img.shields.io/badge/AI%20Core-IndoBERT%20%2B%20BERTopic-purple.svg)](README.md)
[![Air-Gap Ready](https://img.shields.io/badge/Air--Gapped-100%25%20Offline%20Ready-emerald.svg)](README.md)

---

> ### ⚠️ PEMBERITAHUAN PENTING: STATUS PROTOTIPE CEPAT (PROOF-OF-CONCEPT)
> 
> **Aplikasi CaRI-Siber ID saat ini merupakan PROTOTIPE FUNGSIONAL (Proof-of-Concept / PoC)** yang dikembangkan dalam kurun waktu singkat untuk mengejar tenggat waktu (*deadline*).
> 
> **Fokus Saat Ini:**  
> Versi desktop mandiri (*standalone desktop app*) ini menyajikan contoh simpel dan teruji untuk membuktikan keandalan algoritma:
> 1. Mengambil cuplikan percakapan berbasis insiden/isu pada **YouTube** (atau impor berkas log **X, TikTok, Instagram, Telegram** secara *offline*).
> 2. Menjalankan ekstraksi semantik **IndoBERT**, klastering **BERTopic**, deteksi pola buzzer (**CIB Dual-Track**), penyegelan bukti **SHA-256**, dan laporan eksekutif **KIRKA Excel**.
> 
> **Visi & Rencana Masa Depan (Sistem Pemantauan 24/7):**  
> Konsep dan kode dalam proyek ini dirancang secara modular agar dapat di-scale menjadi **Sistem Pemantauan Siber 24/7 Non-Stop** berbasis server/cloud yang terus mendengarkan percakapan seluruh media sosial di Indonesia secara otomatis tanpa henti, dilengkapi peringatan instan (*real-time push alert*) ke Pusat Komando Operasi (Puskodal).  
> 📖 _Baca cetak biru transisi teknis selengkapnya di [docs/ARSITEKTUR_DAN_ROADMAP_24_7.md](file:///d:/UNSIA/review-analysis/cari-siber-id/docs/ARSITEKTUR_DAN_ROADMAP_24_7.md)._

---

## 💡 Penjelasan untuk Orang Awam (Konsep 2 Menit)

Jika Anda bukan orang IT atau analis siber, jangan khawatir! Berikut rangkuman sederhana tentang apa dan mengapa aplikasi ini dibuat:

### 1. Masalah Nyata: "Perang Opini & Pasukan Buzzer"
Pernahkah Anda membaca kolom komentar di media sosial dan merasa suasananya sangat panas, penuh makian, adu domba suku/agama, atau memuji/menyerang figur tertentu secara berlebihan?  
Di dunia maya, **suara yang paling berisik sering kali bukan suara rakyat asli**, melainkan **pasukan robot (bot) dan buzzer bayaran** yang dibayar untuk merekayasa opini publik (*astroturfing*).

### 2. Solusi: "Radar Cuaca Siber"
Ibarat radar cuaca di bandara yang bisa membedakan mana awan hujan alami dan mana asap buatan dari pabrik, **CaRI-Siber ID** memindai ribuan komentar untuk memisahkan:
- **Mana suara tulus masyarakat biasa** (keluhan asli, apresiasi wajar).
- **Mana serangan terorganisir dari buzzer** (komentar *copypasta* yang teksnya persis sama disalin ke ratusan akun dan disebar dalam hitungan detik).

### 3. Mengapa Ada "Segel Bukti Digital SHA-256"?
Sama seperti polisi yang memasukkan barang bukti ke dalam amplop bersegel lak merah di TKP (*Chain of Custody*), setiap data komentar yang diunduh aplikasi ini langsung diberi **sidik jari digital (kriptografi SHA-256)**. Tujuannya agar data tersebut dijamin asli, sah secara hukum, dan tidak bisa diubah-ubah atau direkayasa oleh siapa pun.

### 4. Apa itu "Silent Majority" (Mayoritas yang Diam)?
Sering kali jutaan orang setuju atau tidak setuju dengan suatu hal, tetapi mereka malas berdebat di kolom komentar. Mereka hanya menekan tombol *Like*. Aplikasi ini menghitung rasio jempol (*likes*) untuk mengetahui apa yang sebenarnya dipikirkan oleh **mayoritas masyarakat yang tidak bersuara lantang**.

📖 _Ingin penjelasan lebih santai dan mendalam? Baca [docs/PANDUAN_AWAM_DAN_EDUKASI.md](file:///d:/UNSIA/review-analysis/cari-siber-id/docs/PANDUAN_AWAM_DAN_EDUKASI.md)._

---

## 🔍 Alur Kerja Pipeline 5 Langkah (Sederhana & Terukur)

```
[Sumber Data: YouTube / Berkas CSV Medsos]
                   │
                   ▼
[1. Akuisisi & Segel Bukti] ───► Segel SHA-256 langsung dicatat (forensic_manifest.json)
                   │
                   ▼
[2. Pembersihan Bahasa Slang] ─► Mengubah kata gaul/singkatan Indonesia ke kata baku
                   │
                   ▼
[3. Pemodelan Topik IndoBERT] ─► Mengelompokkan ribuan komentar ke dalam klaster tema utama
                   │
                   ▼
[4. Deteksi Buzzer & 4 Gates] ─► Menyaring copypasta, akun berisiko, & audit angka bebas halusinasi
                   │
                   ▼
[5. Peta Situasi & Laporan] ───► Dashboard SITREP taktis + Ekspor Dokumen Intelijen KIRKA (.xlsx)
```

1. **Langkah 1 (Akuisisi Target)**: Memasukkan kata kunci isu atau link video YouTube, atau mengimpor berkas CSV komentar dari medsos lain.
2. **Langkah 2 (Pembersihan Bahasa)**: Kamus slang Indonesia (Nasalsabila) menormalkan bahasa gaul (misal: `"yg"` jadi `"yang"`, `"bgt"` jadi `"banget"`).
3. **Langkah 3 (Ekstraksi Semantik)**: Model transformer **IndoBERT** membaca makna kalimat dan **BERTopic** mengelompokkannya ke topik-topik spesifik secara otomatis.
4. **Langkah 4 (Penyaringan Buzzer & Verifikasi AI)**:
   - **Track A (CIB Engine)**: Melacak copypasta dan pengiriman pesan serentak (*burst*).
   - **Track B (Threat Domain)**: Mengelompokkan bahaya ke 6 domain (Disinformasi, Separatisme, Kekerasan, SARA, Siber/OT, Organik).
   - **4 Hardened Gates**: Verifikasi silang deterministik agar angka dan analisis 100% faktual tanpa halusinasi AI.
5. **Langkah 5 (Laporan Intelijen KIRKA)**: Hasil ditampilkan dalam dashboard grafis dan dapat diunduh sebagai berkas Excel resmi multi-sheet (*Perkiraan Intelijen Siber*).

---

## 🏛️ Kapabilitas Utama & Keunggulan Taktis

### 1. 🔐 Integritas Bukti Kriptografis SHA-256 (*Chain of Custody*)
- Sesuai standar bukti elektronik **ISO/IEC 27037**, setiap korpus data mentah maupun artefak analitik otomatis disegel dengan hash **SHA-256** (`forensic_manifest.json`).
- Menjamin data tidak terkontaminasi atau dimanipulasi dari tahap pengumpulan hingga pelaporan eksekutif.

### 2. 🎯 Deteksi Buzzer (CIB) & Provokator (*Dual-Track Engine*)
- **Track A – CIB / Buzzer / Bot**: Mendeteksi pola *copypasta*, lonjakan pesan serentak (*rapid-fire burst*), dan anomali rasio akun duplikat.
- **Track B – Akun Berisiko Tinggi**: Memetakan akun provokator penyebar disinformasi, separatisme, ujaran SARA, dan ancaman siber/OT.

### 3. 🧠 Kalibrasi Konteks Human-in-the-Loop (< 2 Detik)
- Analis dapat menandai slogan positif warga (seperti *"NKRI Harga Mati"*) agar tidak salah terdeteksi sebagai spam buzzer (*anti-false positive*).
- Kalkulasi ulang skor ancaman berjalan instan (< 2 detik) tanpa perlu mengulang pengambilan data atau proses AI dari awal.

### 4. 🛡️ 4 Agentic AI Hardened Verification Gates (Bebas Halusinasi)
- **Gate 1 (*Quality Gate*)**: Normalisasi slang & sanitasi token.
- **Gate 2 (*Topic Gate*)**: Audit kohesi vektor IndoBERT & pencegahan *mega-blob*.
- **Gate 3 (*Verification Gate*)**: Verifikasi silang deterministik konfidensi $\ge 0,70$.
- **Gate 4 (*Report Gate*)**: Audit kecocokan angka persentase KIRKA terhadap tabel fakta mentah.

### 5. 🔌 Mode Intranet (*100% Air-Gapped Local LLM*)
- Dapat berjalan di lingkungan militer/pemerintahan yang **terisolasi tanpa internet sama sekali** menggunakan model **IndoBERT lokal** dan server **Ollama / vLLM lokal** (`http://127.0.0.1:11434/v1`).
- Penyimpanan kunci API terenkripsi pada **Windows Credential Manager / OS Keychain**.

---

## 🗺️ Roadmap: Menuju Sistem Monitoring 24/7 Non-Stop

| Fitur | Versi Prototipe Saat Ini (PoC) | Target Sistem Produksi 24/7 |
| :--- | :--- | :--- |
| **Arsitektur** | Desktop Standalone (PyWebView + React) | Distributed Cloud/On-Premise Microservices |
| **Siklus Analisis** | *On-Demand Snapshot* (per kasus/video) | *Continuous 24/7 Streaming Ingestion* |
| **Sumber Data** | YouTube otomatis + Impor file medsos offline | Direct Stream API: X, TikTok, IG, YouTube, Telegram |
| **Notifikasi** | Layar desktop setelah proses selesai | Peringatan instan (< 5 detik) ke Telegram/Signal/SIEM |
| **Penyimpanan** | SQLite lokal (`history.db`) | Distributed PostgreSQL (pgvector) + Neo4j Graph DB |
| **Tujuan** | Uji Coba Cepat & Pembuktian Algoritma | Pusat Komando Pertahanan Kognitif Skala Penuh |

---

## 💻 Persyaratan Sistem

- **Sistem Operasi**: Windows 10/11 (64-bit) atau macOS 11.0+ (Apple Silicon / Intel).
- **Python**: Python 3.10, 3.11, atau 3.12.
- **Node.js**: Node.js 18+ & npm (untuk kompilasi antarmuka frontend).
- **Mode Operasi**:
  - **Mode Online**: Koneksi internet untuk akuisisi YouTube & LLM Cloud (Gemini/OpenRouter).
  - **Mode Air-Gapped**: 100% offline dengan model IndoBERT lokal dan server Ollama lokal.

---

## 🚀 Panduan Menjalankan (Mode Pengembangan)

### 1. Kloning Repositori & Persiapan Python

```bash
git clone https://github.com/username/cari-siber-id.git
cd cari-siber-id

# Buat virtual environment
python -m venv .venv

# Aktivasi lingkungan:
# Windows (PowerShell):
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Pasang dependensi
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Kompilasi Antarmuka Desktop (React/Vite)

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Menjalankan Aplikasi Desktop

```bash
python main.py
```
*(Tambahkan argumen `--dev` jika ingin menghubungkan antarmuka ke Vite Dev Server di `localhost:5173`).*

---

## 📦 Panduan Membangun Installer (Distribusi Produksi)

### A. Windows Installer (NSIS Setup `.exe`)
```powershell
# 1. Kompilasi Executable Windowed (tanpa terminal hitam)
pyinstaller CaRI-Siber-ID.spec --clean --noconfirm

# 2. Kemas Menjadi Installer Resmi NSIS
& "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
```
_Hasil installer berada di `dist/CaRI-Siber-ID-Setup.exe`._

### B. macOS Application (`.app` & `.dmg`)
```bash
# 1. Kompilasi Bundle macOS
pyinstaller CaRI-Siber-ID.spec --clean --noconfirm

# 2. Kemas Menjadi Installer Drag-and-Drop .dmg
create-dmg --volname "CaRI-Siber ID Installer" "dist/CaRI-Siber-ID-Installer.dmg" "dist/CaRI-Siber-ID.app"
```

---

## 📂 Struktur Proyek

```text
cari-siber-id/
├── docs/                           # Dokumentasi Komprehensif
│   ├── PANDUAN_AWAM_DAN_EDUKASI.md # Penjelasan konsep, analogi, & panduan non-teknis
│   └── ARSITEKTUR_DAN_ROADMAP_24_7.md # Cetak biru transisi prototipe menuju sistem 24/7
├── cari_siber/                     # Paket Inti Backend & Mesin AI
│   ├── desktop/                    # Window pywebview, bridge RPC API, & event emitter
│   ├── engine/                     # IndoBERT, BERTopic, 4 Agentic Gates, & Excel Reporter
│   ├── services/                   # History DB SQLite, CIB Dual-Track, & SHA-256 Forensik
│   ├── paths.py                    # Resolusi path lintas platform (Appdata/Local)
│   ├── settings.py                 # Keyring terenkripsi OS & manajemen konfigurasi
│   └── ui_dist/                    # Bundle hasil kompilasi frontend produksi
├── frontend/                       # Source Code Antarmuka Desktop (React 19 + TypeScript + Vite 8)
│   ├── src/
│   │   ├── components/             # AboutModal (Info PoC), Sidebar, KpiCard, TopicTable
│   │   ├── pages/                  # NewAnalysis, Progress, Result (SITREP), History, Settings
│   │   └── api/                    # Bridge PyWebView & tipe data
├── resources/                      # Kamus Slang, Stopwords, & Korpus Simulasi Bawaan (.csv)
├── CaRI-Siber-ID.spec              # Konfigurasi PyInstaller lintas platform
├── installer.nsi                   # Skrip kompilator NSIS Windows
├── main.py                         # Entry point utama aplikasi
└── README.md                       # Dokumentasi resmi repositori
```

---

## 🔒 Keamanan Siber & Kedaulatan Data

- **Zero External Data Leak**: Seluruh data komentar, basis data SQLite (`history.db`), berkas hash forensik (`forensic_manifest.json`), dan aturan kalibrasi disimpan 100% di direktori pengguna lokal (`%LOCALAPPDATA%\CaRI-Siber-ID`).
- **Penyimpanan Kunci API Terenkripsi**: Kunci API tidak disimpan dalam teks polos (*plaintext*), melainkan dilindungi menggunakan **Windows Credential Manager** atau **macOS Keychain** melalui pustaka `keyring`.

---

## 👥 Pengembang & Hak Cipta
Dikembangkan sebagai instrumen riset dan demonstrasi intelijen domain kognitif, pembongkaran manipulasi informasi terkoordinasi (CIB), serta forensik bukti digital berstandar nasional.
