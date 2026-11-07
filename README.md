# 🛡️ CaRI-Siber ID – Sistem Intelijen Domain Kognitif & Forensik Ancaman Siber-Sosial

### _Platform Desktop Mandiri Deteksi Operasi Informasi (CIB), Pemetaan Polarisasi, & Forensik Bukti Digital_

**CaRI-Siber ID** adalah platform intelijen domain kognitif dan siber-sosial berbasis aplikasi desktop mandiri (**PyWebView + React 18 + TypeScript**) untuk pemantauan ruang siber, deteksi operasi informasi terkoordinasi, dan analisis opini publik. Sistem ini mengintegrasikan pemodelan topik deep learning lokal (**IndoBERT + BERTopic**), arsitektur **4 Agentic AI Hardened Verification Gates** bebas halusinasi, **Penyegelan Bukti Digital Kriptografis SHA-256 (*Chain of Custody*)**, serta **Kalibrasi Konteks *Human-in-the-Loop*** dengan kemampuan **Operasi Intranet *Air-Gapped* (100% Offline)**.

---

## 🏛️ Kapabilitas Utama & Keunggulan Taktis

### 1. 🔐 Integritas Bukti Digital Kriptografis SHA-256 (*Chain of Custody*)
- Sesuai standar akuisisi bukti elektronik **ISO/IEC 27037**, setiap korpus data mentah maupun artefak analitik otomatis disegel secara kriptografis menggunakan algoritma **SHA-256** (`forensic_manifest.json`).
- Mencatat waktu akuisisi UTC, ukuran byte eksak, jumlah baris, dan tanda tangan digital untuk menjamin keutuhan barang bukti (*Chain of Custody*) dari tahap pengumpulan hingga pelaporan eksekutif.
- Dilengkapi badge **Segel Forensik Digital SHA-256** pada antarmuka SITREP untuk memastikan integritas berkas secara *real-time*.

### 2. 🎯 Deteksi Operasi Informasi Terkoordinasi (CIB) & Provokator (*Dual-Track Detection*)
- **Track A – *Coordinated Inauthentic Behavior* (CIB / Bot / Buzzer)**: Mendeteksi jaringan akun terkoordinasi lintas video berdasarkan kemiripan teks (*copypasta clustering*), lonjakan pengiriman pesan serentak (*rapid-fire burst*), dan anomali rasio duplikasi akun.
- **Track B – Provokator, Agitator & *High-Risk Accounts***: Mengidentifikasi akun penyebar disinformasi, propaganda separatisme, provokasi SARA, hasutan kekerasan, dan ancaman siber/OT (DDoS, peretasan, doxing).
- **Taksonomi 6 Domain Ancaman Siber-Sosial**: Mengklasifikasikan setiap klaster isu ke dalam *Disinformasi/Fitnah Institusi*, *Propaganda/Separatisme*, *Hasutan/Kekerasan*, *Polarisasi SARA*, *Ancaman Siber/OT*, atau *Organik/Aspirasi Publik*.

### 3. 🧠 Agentic AI Context Calibrator (*Human-in-the-Loop*) & Kalkulasi Ulang Instan (< 2 Detik)
- Mengeliminasi positif palsu (*false positive*) di mana slogan apresiasi organik warga (misalnya *"NKRI Harga Mati"*) terdeteksi sebagai pola berulang.
- Analis dapat mengkalibrasi akun atau frasa sebagai **Slogan / Apresiasi Warga (Whitelist)** atau **Kata Kunci Ancaman** secara interaktif dan menjalankan **Kalkulasi Ulang Instan (< 2 detik)** tanpa perlu mengulang proses *scraping* maupun *clustering* BERTopic dari awal.

### 4. 🛡️ 4 Agentic AI Hardened Verification Gates (Bebas Halusinasi)
- **Gate 1 (*Quality Gate*)**: Normalisasi kata slang/singkatan bahasa Indonesia berbasis kamus Nasalsabila & audit kualitas token pra-pemodelan.
- **Gate 2 (*Topic Gate*)**: Audit kohesi klaster vektor IndoBERT + BERTopic, penyatuan klaster duplikat otomatis, dan *anti-mega-blob guardrail*.
- **Gate 3 (*Verification Gate*)**: Verifikasi silang deterministik label topik, sentimen, dan domain ancaman dengan ambang konfidensi $\ge 0,70$ serta *auto-reroute* batch berisiko.
- **Gate 4 (*Report Gate*)**: Audit keterlacakan angka, persentase, dan kutipan pada draf laporan **Perkiraan Intelijen Siber (KIRKA)** terhadap tabel fakta CSV sebelum laporan disajikan.

### 5. 📡 Pemetaan Polarisasi & Konsensus Mayoritas Pasif (*Silent Majority*)
- **Polarization Index ($0,00 - 1,00$)**: Mengukur tingkat friksi antara kubu sentimen positif dan negatif secara kuantitatif untuk membedakan diskusi organik dari polarisasi buatan.
- **Silent Majority Consensus**: Memisahkan kebisingan kelompok vokal minoritas (*loud minority*) dari dukungan riil audiens pasif melalui normalisasi rasio bobot *likes* terhadap volume komentar.

### 6. 📂 Ingesti OSINT Lintas-Platform Offline & Korpus Simulasi Bawaan
- **Universal Multi-Platform Importer**: Mendukung impor dataset komentar/unggahan dari **X (Twitter), TikTok, Instagram, Telegram, Facebook, dan YouTube** dalam format **`.CSV`**, **`.JSON`**, atau **`.XLSX`** dengan pemetaan kolom otomatis (*auto-column mapping*).
- **Korpus Simulasi Bawaan**: Menyediakan dataset simulasi siap uji (*Operasi Pengamanan Perbatasan & Bakti Sosial* serta *Pertahanan Siber & Mitigasi Hoaks Infrastruktur Kritis*) untuk demonstrasi dan pengujian di lingkungan tanpa internet.

### 7. 🔌 Mode Intranet (*Air-Gapped Local LLM*) & Kredensial Terenkripsi
- **100% Air-Gapped Ready**: Mendukung koneksi ke server LLM lokal (**Ollama / vLLM / LocalAI** pada `http://127.0.0.1:11434/v1`) bersama model embedding **IndoBERT lokal** (`resources/models/indobert-base-p1`).
- **Multi-Provider Cloud & Lokal**: Mendukung Local LLM (Ollama/vLLM), Google Gemini, OpenRouter, dan Custom OpenAI-compatible Endpoint dengan penyimpanan API Key terenkripsi di **Windows Credential Manager / OS Keyring**.

### 8. 🖥️ Antarmuka Komando 5-Langkah & Ekspor Laporan KIRKA (`.XLSX`)
- Desain antarmuka taktis *Dark Command Center* dengan **5 Langkah Progres Pipeline Terpadu**, pemetaan **DISARM Framework**, dan tombol **Mode Briefing Layar Penuh (`F11`)**.
- Menghasilkan dokumen laporan **Perkiraan Intelijen Siber (KIRKA)** multi-sheet berformat Excel (`.xlsx`) beserta rekomendasi kontra-narasi strategis.

---

## 💻 Persyaratan Sistem

- **Sistem Operasi**: Windows 10/11 (64-bit) atau macOS 11.0+ (Apple Silicon / Intel).
- **Python**: Python 3.10, 3.11, atau 3.12 (direkomendasikan).
- **Node.js**: Node.js 18+ & npm (untuk kompilasi antarmuka frontend).
- **Mode Operasi**:
  - **Mode Online / Hibrida**: Koneksi internet untuk akuisisi langsung YouTube dan API LLM Cloud.
  - **Mode Air-Gapped / Offline Penuh**: Tanpa internet menggunakan fitur **Impor Korpus Eksternal / Simulasi**, model **IndoBERT lokal**, dan server **Ollama / vLLM lokal** (`http://127.0.0.1:11434/v1`).

---

## 🚀 Panduan Menjalankan (Mode Pengembangan)

### 1. Kloning Repositori & Persiapan Lingkungan Python

```bash
git clone https://github.com/username/cari-siber-id.git
cd cari-siber-id

# Buat dan aktifkan virtual environment
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

# Pasang dependensi
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Kompilasi Antarmuka Desktop (Frontend React/Vite)

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Konfigurasi Lingkungan (Opsional)

Salin file template `.env.example` menjadi `.env` jika ingin menyetel konfigurasi awal:

```bash
cp .env.example .env
```

_(Catatan: Anda juga dapat mengonfigurasi endpoint **Intranet / Air-Gap** atau memasukkan API Key secara langsung melalui menu **Konfigurasi Sistem** di dalam antarmuka desktop)._

### 4. Menjalankan Aplikasi Desktop

```bash
python main.py
```

_(Tambahkan argumen `--dev` jika ingin menghubungkan antarmuka ke Vite Dev Server di `localhost:5173`)._

---

## 📦 Panduan Build Distribusi (Executable & Installer)

### A. Membangun Installer Windows (Standalone EXE + NSIS Setup)

1. **Pasang PyInstaller**:
   ```powershell
   pip install pyinstaller
   ```
2. **Kompilasi Executable (Windowed Mode - Tanpa Terminal Hitam)**:

   ```powershell
   pyinstaller CaRI-Siber-ID.spec --clean --noconfirm
   ```

   _Hasil build folder berada di `dist/CaRI-Siber-ID/CaRI-Siber-ID.exe`._

3. **Kemas Menjadi Installer Resmi NSIS (`.exe`)**:
   Pastikan [NSIS](https://nsis.sourceforge.io/) terpasang, lalu jalankan:
   ```powershell
   & "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
   ```
   _File installer siap pakai akan tercipta di `dist/CaRI-Siber-ID-Setup.exe`._

---

### B. Membangun Aplikasi macOS (`.app` & `.dmg`)

1. **Jalankan PyInstaller di macOS**:

   ```bash
   pyinstaller CaRI-Siber-ID.spec --clean --noconfirm
   ```

   _Hasil aplikasi native macOS berada di `dist/CaRI-Siber-ID.app`._

2. **Kemas Menjadi Installer `.dmg` (Drag-and-Drop ke Applications)**:
   ```bash
   brew install create-dmg
   create-dmg \
     --volname "CaRI-Siber ID Installer" \
     --window-pos 200 120 \
     --window-size 600 400 \
     --icon-size 100 \
     --icon "CaRI-Siber-ID.app" 175 120 \
     --hide-extension "CaRI-Siber-ID.app" \
     --app-drop-link 425 120 \
     "dist/CaRI-Siber-ID-Installer.dmg" \
     "dist/CaRI-Siber-ID.app"
   ```

---

## 📂 Struktur Proyek

```text
cari-siber-id/
├── cari_siber/                      # Paket Utama Backend & Desktop Core
│   ├── desktop/                    # Window pywebview & API JavaScript Bridge
│   │   ├── api.py                  # API RPC bridge (YouTube, OSINT Importer, Forensic, Calibrator)
│   │   ├── window.py               # Konfigurasi native webview desktop
│   │   └── events.py               # Event emitter progres 5-langkah & log real-time
│   ├── engine/                     # Pipeline Analitik & AI Engine
│   │   ├── core/                   # IndoBERT, BERTopic, AI Client (SSE Stream), 4 Agentic Gates
│   │   ├── pipelines/              # Orkestrator akuisisi, topik, verifikasi, analisis, & KIRKA
│   │   └── reporters/              # Generator laporan intelijen XLSX multi-sheet
│   ├── services/                   # History DB SQLite, CIB Dual-Track, SHA-256 Forensics, Results
│   ├── bootstrap.py                # Logging system & penanganan stream tanpa konsol
│   ├── paths.py                    # Resolusi path lintas platform (Win/macOS/Linux)
│   ├── settings.py                 # Manajemen konfigurasi & Keyring terenkripsi
│   └── ui_dist/                    # Distribusi bundle produksi antarmuka React
├── frontend/                       # Source Code Antarmuka Desktop (React 18 + TypeScript + Vite)
│   ├── src/                        # Komponen UI, Panel Forensik SHA-256, Context Calibrator
│   ├── package.json                # Dependensi frontend
│   └── vite.config.ts              # Konfigurasi build Vite
├── resources/                      # Kamus Slang, Stopwords, & Korpus Simulasi Bawaan (.csv)
├── dist/                           # Direktori output hasil build (.exe, .dmg, installer)
├── CaRI-Siber-ID.spec              # Spesifikasi PyInstaller lintas platform
├── installer.nsi                   # Skrip kompilasi installer NSIS Windows
├── main.py                         # Titik masuk utama aplikasi desktop
├── requirements.txt                # Dependensi Python
├── .env.example                    # Template file variabel lingkungan
└── README.md                       # Dokumentasi resmi proyek
```

---

## 🔒 Kedaulatan Data, Forensik & Keamanan Siber

- **Penyimpanan Lokal Terisolasi**: Seluruh berkas korpus, manifest forensik SHA-256 (`forensic_manifest.json`), aturan kalibrasi konteks (`context_calibration.json`), basis data SQLite (`history.db`), dan log audit disimpan 100% di direktori lokal pengguna (`%LOCALAPPDATA%\CaRI-Siber-ID` di Windows atau `~/Library/Application Support/CaRI-Siber-ID` di macOS).
- **Kredensial Terenkripsi**: Kunci API tidak disimpan dalam teks polos (*plaintext*), melainkan diamankan menggunakan **Windows Credential Manager** atau **Keychain native OS** melalui pustaka `keyring`.
