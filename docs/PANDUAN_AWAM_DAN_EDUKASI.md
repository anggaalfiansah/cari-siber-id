# 📖 Panduan Edukasi & Pengenalan CaRI-Siber ID (Untuk Orang Awam)

> _"Di era perang kognitif modern, senjata paling mematikan bukanlah peluru, melainkan narasi palsu yang disebarkan berulang kali hingga dianggap sebagai kebenaran."_

---

## 1. 🎯 Kenapa Aplikasi Ini Dibuat? (Latar Belakang Nyata)

Pernahkah Anda membuka kolom komentar di YouTube, X (Twitter), TikTok, atau Instagram pada sebuah video berita, lalu merasa ada yang aneh?
- Ratusan akun menuliskan **kalimat yang persis sama kata demi kata** (*copypasta*).
- Komentar-komentar provokatif membanjiri video dalam waktu hitungan detik setelah video diunggah.
- Isu yang awalnya tenang mendadak dipenuhi adu domba suku, agama, ras, dan fitnah terhadap institusi publik.

Apakah itu suara murni masyarakat Indonesia? **Sering kali bukan.**  
Fenomena ini dikenal sebagai **Operasi Informasi Terkoordinasi (*Coordinated Inauthentic Behavior / CIB*)** yang digerakkan oleh sindikat buzzer bayaran dan ribuan akun bot untuk merekayasa persepsi publik (*astroturfing*).

**CaRI-Siber ID** diciptakan untuk menjadi alat bantu bagi analis, akademisi, instansi pemerintah, dan masyarakat dalam **melihat fakta objektif di balik hiruk-pikuk kolom komentar**, memisahkan mana aspirasi tulus masyarakat dan mana manipulasi mesin/buzzer.

---

## 2. 📡 Analogi Sederhana: "Radar Cuaca Siber"

Bayangkan Anda seorang petugas lalu lintas udara yang sedang memantau langit:
1. **Mata Telanjang (Manual)**: Anda melihat langit mendung gelap dan mengira ada badai dahsyat.
2. **Radar Cuaca Canggih (CaRI-Siber ID)**: Radar memindai partikel udara dan memberi tahu Anda: *"Itu bukan awan badai alami, itu adalah asap buatan dari cerobong pabrik yang sengaja ditiupkan ke arah bandara."*

Begitulah cara kerja **CaRI-Siber ID**:
- Ribuan komentar yang tampak seperti "kemarahan seluruh rakyat" dipindai oleh algoritma.
- Sistem akan membongkar apakah kemarahan tersebut asli dari ribuan individu berbeda, atau hanya 10 orang operator yang mengendalikan 500 akun palsu dengan teks serentak.

---

## 3. 🤖 Apa Itu CIB (*Coordinated Inauthentic Behavior*)?

**CIB** adalah istilah internasional (yang dipopulerkan oleh peneliti keamanan siber global dan Meta Threat Intelligence) untuk menyebut:
> **Tindakan sekelompok akun yang bekerja sama secara terorganisir untuk menyesatkan pengguna lain mengenai siapa mereka dan apa yang sedang mereka lakukan.**

Ciri-ciri khas CIB yang dideteksi oleh CaRI-Siber ID:
1. **Copypasta Clustering**: Teks komentar yang 90%–100% sama disalin-tempel ke berbagai video atau waktu yang berbeda.
2. **Rapid-Fire Burst**: Lonjakan puluhan hingga ratusan komentar yang masuk dalam rentang waktu sangat sempit (misalnya selisih 1–3 detik antar komentar) yang mustahil dilakukan manusia normal tanpa otomatisasi.
3. **Akun Anonim Berulang**: Akun tanpa identitas jelas yang terus-menerus muncul hanya untuk memperkuat narasi provokatif.

---

## 4. 🤫 Fenomena "Loud Minority" vs "Silent Majority"

Di media sosial berlaku hukum: **Yang paling berisik belum tentu yang paling banyak.**
- **Loud Minority (Minoritas Berisik)**: Sekelompok kecil buzzer/provokator yang menulis ribuan komentar kebencian. Jika hanya melihat jumlah komentar, kita akan merasa seolah-olah "seluruh dunia setuju dengan mereka".
- **Silent Majority (Mayoritas Pasif)**: Ratusan ribu masyarakat umum yang menonton video, menyukai (*like*), namun malas atau enggan menulis komentar karena tidak ingin berdebat dengan buzzer.

**CaRI-Siber ID** memiliki metrik khusus: **Silent Majority Consensus**.  
Algoritma kami menimbang rasio dukungan jempol (*likes*) pada komentar-komentar yang konstruktif dan membandingkannya dengan komentar negatif yang minim *likes*, sehingga pimpinan atau pengambil keputusan tidak tertipu oleh kebisingan semu kelompok buzzer.

---

## 5. 🔐 Mengapa Ada Segel Digital Kriptografis SHA-256?

Dalam dunia hukum dan forensik digital, ada konsep bernama **Chain of Custody** (Rantai Keabsahan Bukti).

> **Analogi Amplop Bukti Polisi:**  
> Saat polisi menemukan barang bukti di tempat kejadian perkara (TKP), barang itu dimasukkan ke dalam kantong khusus, lalu disegel dengan lak dan ditandatangani. Jika segelnya robek, barang bukti tersebut tidak sah di pengadilan karena dicurigai sudah diubah-ubah.

Hal yang sama dilakukan oleh **CaRI-Siber ID**:
- Saat aplikasi mengunduh 5.000 komentar dari YouTube, berkas data mentah tersebut langsung dihitung sidik jari digitalnya menggunakan algoritma matematika **SHA-256**.
- Kode unik SHA-256 (contoh: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`) dicatat di berkas bukti `forensic_manifest.json`.
- Jika ada oknum yang mencoba menambah, menghapus, atau merekayasa satu huruf pun di dalam file data tersebut, kode SHA-256 akan langsung berubah total dan sistem akan membunyikan alarm integritas rusak.

---

## 6. 🏷️ Taksonomi 6 Domain Ancaman Siber-Sosial

Aplikasi ini tidak sekadar memberi label "positif" atau "negatif", melainkan mengelompokkan bahaya komentar ke dalam 6 domain taktis:

| Domain Ancaman | Contoh Isi Komentar | Tingkat Bahaya |
| :--- | :--- | :--- |
| **1. Disinformasi / Fitnah Institusi** | Hoaks pemilu curang buatan, tuduhan palsu korupsi tanpa dasar pada lembaga negara. | 🔴 Tinggi |
| **2. Propaganda / Separatisme** | Ajakan memisahkan diri dari NKRI, simbol-simbol kelompok terlarang, delegitimasi kedaulatan. | 🔴 Sangat Tinggi |
| **3. Hasutan / Kekerasan** | Seruan pembakaran fasilitas umum, ancaman fisik terhadap aparat atau tokoh publik. | 🔴 Kritis |
| **4. Polarisasi SARA** | Ujaran kebencian berbasis suku, agama, ras, dan antargolongan untuk mengadu domba. | 🟠 Tinggi |
| **5. Ancaman Siber / OT** | Tautan jebakan *phishing*, klaim peretasan (*doxing* data KTP/pejabat), seruan serangan DDoS. | 🔴 Kritis |
| **6. Organik / Aspirasi Publik** | Kritik membangun terhadap kebijakan jalan tol, apresiasi kinerja TNI/Polri, keluhan harga pupuk. | 🟢 Aman (Aspirasi Asli) |

---

## 7. 🚦 Status Saat Ini: Mengapa Ini Berupa "Prototipe Cepat"?

Aplikasi yang Anda jalankan saat ini adalah **Prototipe Fungsional (Proof-of-Concept / PoC)** yang dirancang untuk membuktikan bahwa integrasi teknologi ini berhasil bekerja dalam tenggat waktu riset singkat:
- **Yang Bisa Dilakukan Saat Ini**:
  - Mengambil cuplikan (*snapshot*) percakapan dari video YouTube tertentu.
  - Mengimpor berkas komentar offline dari medsos lain (X/Twitter, TikTok, Instagram, Telegram).
  - Menjalankan analisis deep learning lokal IndoBERT, deteksi buzzer CIB, 4 gerbang verifikasi AI, dan mengekspor laporan Excel KIRKA.
- **Batasan Saat Ini**:
  - Masih bersifat *on-demand / batch* (analis harus memasukkan URL atau mengklik tombol).
  - Belum bekerja otomatis 24 jam nonstop di server awan.

**Rencana Masa Depan (Sistem 24/7)**:  
Konsep ini siap dikembangkan menjadi sistem server terpusat yang berjalan otomatis siang dan malam, terus-menerus memantau medsos di seluruh Indonesia tanpa henti, dan mengirim notifikasi darurat jika terdeteksi serangan hoaks berskala besar. (Baca selengkapnya di [ARSITEKTUR_DAN_ROADMAP_24_7.md](file:///d:/UNSIA/review-analysis/cari-siber-id/docs/ARSITEKTUR_DAN_ROADMAP_24_7.md)).
