# 📘 Dokumentasi Teknis: SPK Pemilihan Profil Lulusan (Metode AHP)

## DAFTAR ISI

1. [BAB 1: Pendahuluan & Gambaran Umum Sistem](#bab-1-pendahuluan--gambaran-umum-sistem)
2. [BAB 2: Landasan Metodologi AHP](#bab-2-landasan-metodologi-ahp) 3.[BAB 3: Arsitektur Sistem & Basis Pengetahuan](#bab-3-arsitektur-sistem--basis-pengetahuan)
3. [BAB 4: Implementasi Teknis & Alur Algoritma](#bab-4-implementasi-teknis--alur-algoritma) 5.[BAB 5: Antarmuka Pengguna & Transparansi](#bab-5-antarmuka-pengguna--transparansi) 6.[BAB 6: Panduan Instalasi & Deployment](#bab-6-panduan-instalasi--deployment)

---

## BAB 1: Pendahuluan & Gambaran Umum Sistem

### 1.1 Latar Belakang

Mahasiswa seringkali mengalami kebingungan dalam menentukan jalur profesi (profil lulusan) di akhir masa studinya. Keputusan yang diambil seringkali hanya berdasarkan insting atau tren sesaat, bukan berdasarkan rekam jejak akademik yang objektif. Sistem Pendukung Keputusan (SPK) ini dibangun sebagai **"Konselor Akademik Digital"** yang mampu memberikan rekomendasi profil secara otomatis, presisi, dan berbasis data (data-driven).

### 1.2 Tujuan Sistem

Sistem ini menerima input berupa dokumen PDF Transkrip Nilai mahasiswa, mengekstraksi data mata kuliah secara otomatis, dan menghitung rekomendasi profil menggunakan algoritma **Analytic Hierarchy Process (AHP) metode Thomas L. Saaty**.

Terdapat 4 Profil Alternatif yang direkomendasikan, mengacu pada **Kurikulum FTI UKDW 2021 (Revisi 2023)**:

1. **AI** (Artificial Intelligence)
2. **DMS** (Database Management System)
3. **PSD** (Programming & Software Development)
4. **INFRA** (Network and Infrastructure)

---

## BAB 2: Landasan Metodologi AHP

Sistem ini tidak menggunakan pembobotan statis (tebakan manual), melainkan menghitung bobot secara dinamis menggunakan **Matriks Perbandingan Berpasangan (Pairwise Comparison Matrix)** sesuai standar AHP Saaty.

### 2.1 Tiga Kriteria Utama (Parameter Evaluasi)

Sistem mengevaluasi mahasiswa berdasarkan 3 matriks kriteria utama untuk mencegah anomali data (seperti mahasiswa mendapat nilai A di 1 kelas AI, lalu dianggap ahli AI).

1. **Kualitas Dasar (Foundation):** Evaluasi rata-rata IPK untuk mata kuliah wajib (Semester 1-4) yang menjadi fondasi dari sebuah profil.
2. **Kualitas Keahlian (Competency):** Evaluasi rata-rata IPK untuk mata kuliah Pilihan Wajib Profesi dan Pilihan Bebas.
3. **Kepadatan/Minat (Density):** Evaluasi berdasarkan _volume_ atau **jumlah kelas** keahlian yang diambil. Ini adalah kriteria krusial untuk membuktikan seberapa besar _effort_ dan minat mahasiswa pada suatu bidang.

### 2.2 Rumus Konversi ke Skala Saaty (1-9)

AHP Saaty mewajibkan perbandingan antara 2 elemen (Misal: AI vs DMS) dalam skala 1 hingga 9. Sistem merubah data mentah mahasiswa menjadi skala Saaty dengan rumus berikut:

- **Untuk Kriteria Kualitas (IPK):**
  Rentang perbedaan IPK maksimal adalah 4.0.
  `Skala Saaty = 1 + Round( |IPK_A - IPK_B| × 2 )`
  _(Contoh: Selisih IPK 2.0 (A vs C) = 1 + (2.0 × 2) = Skala 5 / Lebih Penting)._
- **Untuk Kriteria Minat (Jumlah Kelas):**
  `Skala Saaty = 1 + |JumlahKelas_A - JumlahKelas_B|`
  _(Nilai dibatasi maksimal pada skala 9 / Mutlak Penting)._

### 2.3 Rasio Konsistensi (Consistency Ratio / CR)

Setiap matriks yang dihasilkan oleh nilai mahasiswa diuji konsistensinya menggunakan _Consistency Index_ (CI) dan _Random Index_ (RI). Sistem menjamin bahwa nilai **CR $\le$ 0.1**, yang membuktikan bahwa logika perhitungan rasional dan dapat dipertanggungjawabkan secara matematis.

---

## BAB 3: Arsitektur Sistem & Basis Pengetahuan

Sistem ini dibangun menggunakan arsitektur **Monolitik** berbasis Python, di mana antarmuka pengguna dan logika pemrosesan digabung untuk memaksimalkan kecepatan akses dan kesederhanaan _deployment_.

### 3.1 Struktur Direktori (Folder Structure)

```text
Skripsi_SPK_AHP/
│
├── data/
│   ├── courses.yaml          # Database Katalog Mata Kuliah
│   └── relevance_rules.yaml  # Aturan Pakar (Pemetaan Profil)
│
├── app/
│   ├── core/
│   │   └── config.py         # Pengaturan Environment Variables (.env)
│   ├── models/
│   │   └── schemas.py        # Pydantic Schemas (Validasi Tipe Data)
│   └── services/
│       ├── ahp_math.py       # Engine Matematika AHP murni (Numpy/Pandas)
│       ├── ahp_service.py    # Jembatan antara Nilai Mhs & Matriks AHP
│       ├── knowledge_base.py # Pengelola Database YAML di Memori (Thread-Safe)
│       └── parser_service.py # Ekstraktor PDF Transkrip (Regex & pdfplumber)
│
├── .env                      # File Konfigurasi Lokal
├── requirements.txt          # Daftar Library Python
└── streamlit_app.py          # Antarmuka Pengguna Utama (Frontend)
```

### 3.2 Knowledge Base (Basis Pengetahuan Pakar)

Sistem memisahkan "Aturan Kampus" dari "Kode Program" menggunakan file **YAML** sebagai _Single Source of Truth_ (SSOT). Jika kurikulum berubah di tahun depan, admin hanya perlu mengubah file `relevance_rules.yaml` tanpa menyentuh satupun baris kode Python. Data dibaca menggunakan `threading.Lock()` agar aman dari _race condition_ saat digunakan oleh banyak pengguna secara bersamaan.

---

## BAB 4: Implementasi Teknis & Alur Algoritma

Proses pemrosesan dari awal hingga akhir terjadi dalam hitungan milidetik melalui 4 tahapan (services):

### Fase 1: Data Ingestion (`parser_service.py`)

Sistem menggunakan `pdfplumber` untuk membaca teks mentah PDF dan menggunakan **Regular Expression (Regex)** untuk mencari pola data secara presisi, melewati _header/footer_ yang tidak relevan.
_Pola Regex:_ `((?:TI|MH|EL)\d{4})\s+.*?\s+(\d{1,2})\s+([A-E][+-]?)`

### Fase 2: Data Validation (`schemas.py`)

Data yang diekstrak dilewatkan melalui **Pydantic V2**. Hal ini menjamin tipe data sangat ketat (Misal: SKS harus _integer_ 1-6, Nilai harus di antara 0.0 - 4.0). Validasi ini mencegah terjadinya "sampah masuk, sampah keluar" (GIGO) yang dapat merusak matriks matematika.

### Fase 3: Mathematical Engine (`ahp_math.py`)

Modul ini bertanggung jawab memproses array Pandas menjadi matriks perbandingan berpasangan. Operasi matriks (mencari _Eigenvector_ dengan cara menormalkan kolom dan merata-rata baris) diselesaikan menggunakan operasi vektor `numpy` dan `pandas` yang memiliki kompleksitas waktu (Big-O) sangat rendah.

### Fase 4: Synthesis & Scoring (`ahp_service.py`)

Modul ini menggabungkan bobot alternatif dari 3 kriteria (Foundation, Competency, Minat) dan mengalikannya dengan Matriks Kriteria Utama. Berdasarkan aturan pakar:
`Bobot Kriteria: Minat (Sangat Penting) > Competency (Penting) > Foundation (Dasar)`

---

## BAB 5: Antarmuka Pengguna & Transparansi

Aplikasi dibangun menggunakan **Streamlit**. UI/UX dirancang bukan hanya untuk mahasiswa, tetapi juga untuk **dosen penguji/akademisi** agar dapat memvalidasi algoritma.

### 5.1 Explainable AI (XAI)

SPK sering dianggap sebagai "Black Box" (kotak hitam yang asal menebak angka). Sistem ini menerapkan konsep _Explainable AI_ dengan menyediakan Tab **"Bukti Perhitungan SPK"**.

1. **Transparansi Data Mentah:** Sistem menyediakan _dropdown_ yang memperlihatkan nilai mentah (IPK / Jumlah kelas) dan rumus yang mengubahnya menjadi skala Saaty.
2. **Visibilitas Matriks:** Semua Matriks Perbandingan, Normalisasi, Eigenvector, Lambda Max, CI, dan CR ditampilkan utuh dan interaktif.

### 5.2 Visualisasi Data (Plotly)

Untuk memudahkan interpretasi kognitif, hasil tidak hanya disajikan dalam bentuk teks, melainkan diolah menggunakan `plotly.express` menjadi **Horizontal Bar Chart** interaktif, lengkap dengan narasi kesimpulan (insight) yang di-generate oleh sistem secara otomatis.

---

## BAB 6: Panduan Instalasi & Deployment

### 6.1 Persyaratan Sistem (Prerequisites)

- Sistem Operasi: Windows / macOS / Linux
- Python: Versi 3.10 atau lebih baru

### 6.2 Langkah-langkah Instalasi (Local Environment)

1. **Buka Terminal / Command Prompt** di folder proyek.
2. **Buat Virtual Environment:**
   ```bash
   python -m venv venv
   ```
3. **Aktivasi Virtual Environment:**
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. **Instalasi Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Jalankan Aplikasi:**
   ```bash
   streamlit run streamlit_app.py
   ```
6. Aplikasi akan otomatis terbuka di browser melalui URL: `http://localhost:8501`

---
