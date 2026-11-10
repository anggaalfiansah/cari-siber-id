## 1. SITUASI RUANG SIBER & INDEKS POLARISASI

Lanskap ruang siber terkait isu "Penyadapan Presiden" menunjukkan dinamika opini publik yang sangat volatil dan terpolarisasi tajam dalam periode 25 Oktober hingga 8 November 2026. Berdasarkan telemetri dari 98 video lintas 35 kanal media utama, tercatat total 46.183 komentar dengan distribusi sentimen yang didominasi oleh nada negatif sebesar 74,38% (34.353 komentar), diikuti sentimen positif 24,15% (11.155 komentar), dan netral hanya 1,46% (675 komentar). Indeks Polarisasi mencapai angka tinggi yaitu 0,72, mengindikasikan adanya jurang persepsi yang lebar antara kelompok pendukung dan penentang kebijakan atau narasi yang beredar.

Analisis *Silent Majority* versus *Loud Minority* memperlihatkan bahwa meskipun sentimen negatif mendominasi secara kuantitas, mayoritas komentar tersebut teridentifikasi sebagai bagian dari kampanye provokasi terkoordinasi daripada ekspresi organik masyarakat luas. Topik konflik dominan berpusat pada polarisasi antara dukungan terhadap Presiden Prabowo Subianto versus serangan terhadap mantan Presiden Jokowi dan lingkaran elit politik lainnya. Lonjakan volume komentar (*spike detection*) terjadi signifikan pada tanggal 7 dan 8 November 2026, masing-masing mencatat 14.037 dan 15.067 komentar, yang bertepatan dengan munculnya narasi seruan hukum mati bagi pengkhianat negara dan spekulasi identitas dalang penyadapan ilegal. Kondisi ini menciptakan ekosistem informasi yang reaktif, di mana skeptisisme publik menjadi konsensus diam (*silent majority consensus*), sementara suara keras (*loud minority*) dikendalikan oleh agen-agen provokatif yang membingkai isu keamanan nasional sebagai alat politik partisan.

## 2. IDENTIFIKASI OPERASI INFORMASI TERKOORDINASI / CIB

Skor ancaman Coordinated Inauthentic Behavior (CIB) global berada pada level RENDAH (0.08), namun analisis granular mengungkap aktivitas bot dan buzzer yang cukup masif di balik layar. Dari 34.639 penulis unik, rasio duplikasi penulis mencapai 0,25, menandakan sebagian akun digunakan untuk menyebarkan pesan serupa di berbagai video. Terdapat 407 akun berisiko tinggi yang terdeteksi, serta 41 jaringan bot terkoordinasi. Meskipun rasio ledakan cepat (*rapid burst ratio*) tercatat 0,0%, pola repetisi konten melalui klaster *copypasta* menjadi indikator kuat manipulasi opini.

Temuan forensik mengidentifikasi beberapa klaster bot dengan tingkat koordinasi kritis. Klaster terbesar melibatkan 11 akun unik yang menyebarkan template teks "Hukum mati... Penghianat bangsa" dengan status *CRITICAL_MASS*. Klaster lain melibatkan 4 akun yang berulang kali memposting variasi kalimat serupa seperti "PENGHIANAT WAJIB DIHUKUM MATI" dan "Hukum mati penghianat negara". Pola ini menunjukkan upaya sistematis untuk membanjiri kolom komentar dengan narasi dehumanisasi dan ajakan kekerasan verbal guna menekan algoritma rekomendasi platform agar mengangkat topik tersebut ke permukaan.

Daftar akun terindikasi mencakup berbagai peran, mulai dari *Hybrid Cyber Threat*, *Provokator Berdampak*, hingga *Buzzer Terarah*. Akun seperti @musafirilmu9408 (skor bot 75, provokasi 100) aktif menyebarkan disinformasi mengenai kapasitas sadap presiden sebelumnya. Sementara itu, akun @Abeng123-u8q (skor bot 100) berfungsi sebagai amplifier massal untuk narasi hukum mati. Akun @pagisiangmalam6564 dan @LudfiAhmad-r9y terdeteksi sebagai buzzer dengan skor bot sempurna (100) yang bertugas mengarahkan diskusi ke arah konspirasi tertentu tanpa substansi argumentatif yang valid. Total 2.972 akun telah ditandai sebagai ancaman potensial dalam operasi informasi ini.

## 3. PEMETAAN NARASI ANCAMAN KOGNITIF & KORELASI ANCAMAN INFRASTRUKTUR IT/OT

Pemetaan domain ancaman kognitif reveals empat pilar utama narasi berbahaya: Provokasi SARA & Separatisme, Delegitimasi Institusi, Disinformasi Pertahanan, dan Disinformasi Anggaran Negara. Kategori Provokasi SARA mendominasi dengan 33.570 komentar, fokus pada seruan ekstrem dan hashtag menyerang tokoh politik spesifik. Domain Delegitimasi Institusi (390 komentar negatif + 504 netral) bertujuan meruntuhkan kepercayaan publik terhadap lembaga resmi dengan spekulasi liar tentang "dalang" penyadapan. Disinformasi Pertahanan (280 komentar) menyebarkan narasi "musuh dalam selimut" dan spam emoji konspirasi makar, yang memiliki skor keterlibatan tertinggi (17,84) karena sifat viralnya.

Korelasi antara narasi siber sosial ini dengan ancaman infrastruktur IT/OT bersifat tidak langsung namun signifikan. Narasi delegitimasi institusi dan teori konspirasi tentang "penyadapan ilegal" dapat memicu aksi *doxing* terhadap personel keamanan siber atau pejabat teknis yang terlibat dalam investigasi. Hal ini meningkatkan risiko serangan *social engineering* terhadap staf internal organisasi vital. Selain itu, polarisasi ekstrem yang dipicu oleh narasi kebencian dapat menjadi pemicu (*trigger event*) bagi aktor ancaman non-negara untuk melancarkan serangan DDoS atau defacement website pemerintah sebagai bentuk protes digital atau peretasan oportunistik. Gangguan operasional juga mungkin terjadi jika tim komunikasi krisis kewalahan menangani banjir hoaks yang mengaburkan fakta teknis, sehingga memperlambat respons insiden siber aktual.

## 4. DISARM FRAMEWORK MAPPING

Analisis taktik menggunakan kerangka kerja DISARM (*Disrupting Information Operations*) mengidentifikasi empat teknik utama yang digunakan oleh operator informasi:

1.  **DISARM-T0083 (Synchronized Swarming Attack):** Terdeteksi pada 808 instance. Taktik ini melibatkan mobilisasi massa akun palsu atau semi-palsu untuk menyerbu kolom komentar secara bersamaan, menciptakan ilusi dukungan publik yang besar terhadap narasi tertentu (misalnya, seruan hukuman mati).
2.  **DISARM-T0092 (Astroturfing & Content Repetition):** Terdeteksi pada 209 instance. Ini berkaitan dengan penciptaan gerakan akar rumput semu, di mana konten repetitif disebarluaskan untuk membuat narasi tampak organik dan didukung oleh banyak individu berbeda, padahal berasal dari sumber terkoordinasi.
3.  **DISARM-T0088 (Dehumanization & Polarization Campaign):** Terdeteksi pada 141 instance. Fokus pada penggunaan bahasa kasar, label "pengkhianat", dan retorika yang merendahkan lawan politik untuk memperdalam polarisasi dan menghambat dialog rasional.
4.  **DISARM-T0089 (Coordinated Inauthentic Amplification):** Terdeteksi pada 44 instance. Teknik ini melibatkan amplifikasi konten provokatif melalui interaksi buatan (like, reply, share) untuk menaikkan visibilitas algoritmis.

Keempat taktik ini bekerja sinergis untuk mendominasi ruang percakapan, menekan suara moderat, dan membingkai isu keamanan nasional sebagai perang identitas politik.

## 5. REKOMENDASI TINDAKAN PENANGKALAN & KONTRA-NARASI

Untuk memitigasi dampak operasi informasi ini, disarankan langkah-langkah taktis berikut:

**Bagi Tim Komunikasi Strategis:**
Prioritaskan transparansi proaktif dengan merilis pernyataan resmi yang berbasis data faktual mengenai prosedur penyadapan dan investigasi, guna menutup celah spekulasi. Hindari respons emosional terhadap provokasi; sebaliknya, gunakan kontra-narasi yang menekankan supremasi hukum dan profesionalisme institusi. Manfaatkan influencer kredibel non-politis untuk menyebarkan edukasi literasi digital tentang bahaya *astroturfing*.

**Bagi Tim Analis Intelijen Kognitif:**
Perkuat pemantauan real-time terhadap klaster bot baru yang muncul pasca-spike tanggal 7-8 November. Lakukan profilisasi lebih lanjut terhadap akun dengan skor provokasi >90 untuk mengidentifikasi potensi keterkaitan dengan jaringan politik atau kepentingan ekonomi (seperti penipuan trading yang terlihat dalam sampel komentar). Pantau migrasi narasi dari platform terbuka ke grup tertutup (Telegram/WA) yang sering menjadi tempat perencanaan eskalasi luring.

**Bagi Tim Pertahanan Siber / CSIRT-SOC:**
Siapkan protokol darurat untuk mitigasi serangan DDoS atau *website defacement* yang mungkin dipicu oleh frustrasi massa akibat pemblokiran akun bot. Tingkatkan deteksi anomali lalu lintas data yang mencurigakan dari IP range terkait akun flagged. Pastikan cadangan data (*backup*) sistem kritikal diperbarui secara rutin untuk mencegah ransomware opportunistik yang mungkin memanfaatkan kekacauan informasi. Koordinasikan dengan platform media sosial untuk penghapusan konten yang melanggar kebijakan *hate speech* dan *harassment* secara cepat.