# 🛡️ CaRI-Siber ID – Cognitive Domain Intelligence & Narrative Threat Monitoring

### _Platform Desktop Analisis Domain Kognitif, Deteksi Manipulasi Opini (CIB), & Pemantauan Dinamika Ruang Siber_

**CaRI-Siber ID** adalah platform intelijen kognitif mandiri berbasis aplikasi desktop (**PyWebView + React + TypeScript**) yang mengintegrasikan pemodelan topik deep learning (**IndoBERT + BERTopic**), **Agentic AI Hardened Gates** deterministik bebas halusinasi, dan modul analitik siber sosial untuk memantau opini publik, mendeteksi operasi terkoordinasi bot/buzzer (_Coordinated Inauthentic Behavior / CIB_), serta memetakan polarisasi sosial di ruang digital.

---

## 🏛️ Fokus & Kemampuan Utama Platform

1. **Deteksi Operasi Informasi & Buzzer/Bot (CIB Threat Score)**:
   - Mengkalkulasi rasio repetisi akun (_author duplication_), lonjakan komentar serentak (_rapid-fire burst_), dan intensitas akun anomali berbobot tinggi.
2. **Pemetaan Polarisasi Ruang Digital (Polarization Index)**:
   - Menghitung rasio friksi antara kubu sentimen positif vs negatif secara kuantitatif ($0.00$ - $1.00$) untuk membedakan perdebatan organik vs polarisasi buatan.
3. **Analisis Mayoritas Pasif (_Silent Majority Consensus_)**:
   - Memisahkan narasi bising minoritas (_loud minority_) dengan aspirasi riil penonton pasif melalui normalisasi pembobotan keterlibatan (_likes & replies weight ratio_).
4. **4 Agentic AI Hardened Gates (Bebas Halusinasi)**:
   - **Gate 1 (Quality Gate)**: Validasi kualitas pembersihan kata slang/alay Nasalsabila & eliminasi token sampah.
   - **Gate 2 (Topic Gate)**: Audit kohesi vektor klaster BERTopic dan pencegahan penggelembungan klaster (_anti-mega blob guardrail_).
   - **Gate 3 (Labeling Gate)**: Pelabelan nama kategori isu dan sub-isu berbasis semantik AI kontekstual.
   - **Gate 4 (Verification Gate)**: Audit silang deterministik dengan batasan konfidensi $\ge 0.70$.
5. **Multi-Provider LLM & Keamanan Kredensial**:
   - Mendukung Google Gemini, OpenAI, OpenRouter, EdgeOne, dan Custom OpenAI-compatible endpoints.
   - Penyimpanan API key aman melalui Windows Credential Manager / Keyring terenkripsi.
6. **Ekspor Laporan Intelijen Eksekutif (Excel XLSX)**:
   - Menghasilkan dokumen laporan terstruktur multi-sheet (Overview, Klaster Isu, Deteksi CIB, Engagement, Komentar Teratas).

---

## 💻 Persyaratan Sistem

- **Sistem Operasi**: Windows 10/11 (64-bit) atau macOS 11.0+ (Apple Silicon / Intel).
- **Python**: Python 3.10, 3.11, atau 3.12 (direkomendasikan).
- **Node.js**: Node.js 18+ & npm (untuk kompilasi antarmuka frontend).
- **Koneksi Internet**: Dibutuhkan saat proses scraping dan inferensi API LLM (model IndoBERT dapat berjalan offline setelah terunduh).

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

_(Catatan: Anda juga dapat memasukkan API Key secara langsung melalui menu **Pengaturan API** di dalam antarmuka desktop)._

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
   _File installer siap pakai akan tercipta di `dist/CaRI-Siber-ID-Setup.exe` (~240 MB dengan kompresi solid LZMA)._

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
│   │   ├── api.py                  # API RPC bridge ke frontend React
│   │   ├── window.py               # Konfigurasi native webview desktop
│   │   └── events.py               # Event emitter progres & log real-time
│   ├── engine/                     # Pipeline Analitik & AI Engine
│   │   ├── core/                   # IndoBERT, BERTopic, AI Client, Agentic Gates
│   │   ├── pipelines/              # Orkestrator scraping, topik, sentimen, narasi
│   │   └── reporters/              # Generator laporan XLSX multi-sheet
│   ├── services/                   # History database SQLite, CIB intelligence, results
│   ├── bootstrap.py                # Logging system & penanganan stream tanpa konsol
│   ├── paths.py                    # Resolusi path lintas platform (Win/macOS/Linux)
│   ├── settings.py                 # Manajemen konfigurasi & Keyring terenkripsi
│   └── ui_dist/                    # Distribusi bundle produksi antarmuka React
├── frontend/                       # Source Code Antarmuka Desktop (React 18 + Vite)
│   ├── src/                        # Komponen UI, halaman analitik, chart visualisasi
│   ├── package.json                # Dependensi frontend
│   └── vite.config.ts              # Konfigurasi build Vite
├── resources/                      # Kamus Slang Nasalsabila, Stopwords, & Konfigurasi NLP
├── dist/                           # Direktori output hasil build (.exe, .dmg, installer)
├── CaRI-Siber-ID.spec              # Spesifikasi PyInstaller lintas platform
├── installer.nsi                   # Skrip kompilasi installer NSIS Windows
├── main.py                         # Titik masuk utama aplikasi desktop
├── requirements.txt                # Dependensi Python
├── .env.example                    # Template file variabel lingkungan
└── README.md                       # Dokumentasi resmi proyek
```

---

## 🔒 Privasi Data & Keamanan

- **Penyimpanan Lokal**: Seluruh data audit, cache klaster, basis data SQLite (`history.db`), dan log disimpan secara lokal di direktori data pengguna (`%LOCALAPPDATA%\CaRI-Siber-ID` di Windows atau `~/Library/Application Support/CaRI-Siber-ID` di macOS).
- **Kredensial Aman**: Kunci API tidak disimpan dalam teks polos (plaintext), melainkan diamankan menggunakan Windows Credential Manager atau Keychain native OS via pustaka `keyring`.
