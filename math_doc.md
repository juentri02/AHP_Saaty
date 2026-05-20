# 📘 DOKUMENTASI TEKNIS MATEMATIS: ALGORITMA AHP PADA SPK PROFILING

**Sistem Pendukung Keputusan Pemilihan Profil Kelulusan Mahasiswa FTI UKDW**  
**Metode:** _Analytic Hierarchy Process_ (AHP) - Thomas L. Saaty  
**Versi Dokumen:** 1.0 (Final)

---

## DAFTAR ISI

1. [Pendahuluan: Arsitektur Matematika Sistem](#1-pendahuluan-arsitektur-matematika-sistem)
2. [Pertanyaan 1: Asal Usul Bobot Kriteria Utama (14.3%, 28.6%, 57.1%)](#2-pertanyaan-1-asal-usul-bobot-kriteria-utama)
3. [Pertanyaan 2: Aksioma Timbal Balik (Mengapa 3.00 dan 0.33?)](#3-pertanyaan-2-aksioma-timbal-balik-reciprocal-axiom)
4. [Pertanyaan 3: Cara Menghitung Eigenvector (Bobot Prioritas)](#4-pertanyaan-3-cara-menghitung-eigenvector-bobot-prioritas)
5. [Simulasi Kasus Normal (Mahasiswa Semester 6+)](#5-simulasi-kasus-normal-mahasiswa-semester-6)
6. [Simulasi _Cold Start Problem_ (Mahasiswa Semester 4 ke Bawah)](#6-simulasi-cold-start-problem-mahasiswa-semester-4-ke-bawah)
7. [Validasi Logika: Consistency Ratio (CR)](#7-validasi-logika-consistency-ratio-cr)

---

## 1. PENDAHULUAN: ARSITEKTUR MATEMATIKA SISTEM

_Analytic Hierarchy Process_ (AHP) adalah metode matematika yang memecah masalah pengambilan keputusan yang kompleks menjadi sebuah hierarki. Dalam sistem ini, hierarki terdiri dari:

- **Goal (Tujuan):** Menentukan Profil Kelulusan Terbaik.
- **Kriteria (Parameter):**
  1.  _Foundation_ (Kualitas Dasar) $\rightarrow$ Rata-rata IPK Mata Kuliah Wajib Sem 1-4.
  2.  _Competency_ (Kualitas Keahlian) $\rightarrow$ Rata-rata IPK Mata Kuliah Pilihan Profesi.
  3.  _Density_ (Minat/Kepadatan) $\rightarrow$ Jumlah total mata kuliah pilihan yang diambil.
- **Alternatif (Pilihan):** 4 Profil yaitu AI, DMS, PSD, dan INFRA.

Berbeda dengan sistem AHP tradisional di mana pengguna menebak-nebak angka skala 1 hingga 9 (Skala Saaty), **sistem ini sepenuhnya berjalan secara otomatis (Data-Driven)**. Angka 1-9 dihasilkan dari ekstraksi selisih nilai faktual (IPK dan SKS) yang dikonversi menggunakan rumus matematika _backend_.

---

## 2. Pertanyaan 1: ASAL USUL BOBOT KRITERIA UTAMA

_Pertanyaan Kritis: "Dari mana asal angka 14.3% untuk Dasar, 28.6% untuk Keahlian, dan 57.1% untuk Minat?"_

Angka-angka tersebut tidak diketik secara statis (_hardcoded_), melainkan dihitung secara langsung oleh matriks AHP berdasarkan **Aturan Pakar (Expert Judgement)**.
Aturan pakar menetapkan bahwa:

1.  Kualitas Keahlian (C) **2x lebih penting** daripada Kualitas Dasar (F).
2.  Kepadatan/Minat (D) **4x lebih penting** daripada Kualitas Dasar (F).
3.  Kepadatan/Minat (D) **2x lebih penting** daripada Kualitas Keahlian (C).

Berdasarkan aturan tersebut, sistem membangun **Matriks Perbandingan Berpasangan** awal seperti berikut:

| Kriteria         | Dasar (F) | Keahlian (C) | Minat (D)    |
| :--------------- | :-------- | :----------- | :----------- |
| **Dasar (F)**    | 1.00      | 0.50 ($1/2$) | 0.25 ($1/4$) |
| **Keahlian (C)** | 2.00      | 1.00         | 0.50 ($1/2$) |
| **Minat (D)**    | 4.00      | 2.00         | 1.00         |
| **JUMLAH KOLOM** | **7.00**  | **3.50**     | **1.75**     |

Setelah matriks terbentuk, sistem menghitung _Eigenvector_ (Langkah perhitungan detail ada di Bagian 4). Hasil akhirnya adalah:

- Bobot Dasar (F) = **0.1428 (14.3%)**
- Bobot Keahlian (C) = **0.2857 (28.6%)**
- Bobot Minat (D) = **0.5714 (57.1%)**

_Kesimpulan:_ Angka tersebut adalah hasil absolut dari rasio matematika linier, bukan angka persentase tebakan acak.

---

## 3. Pertanyaan 2: AKSIOMA TIMBAL BALIK (Reciprocal Axiom)

_Pertanyaan Kritis: "Jika pada perbandingan AI dan PSD hasilnya adalah 3.00, mengapa saat posisinya dibalik (PSD dan AI) hasilnya menjadi 0.33?"_

Ini adalah hukum fisika matematis di dalam AHP yang disebut **Aksioma Timbal Balik (_Reciprocal Axiom_)**.
Hukum ini menyatakan bahwa jika elemen $A$ dinilai memiliki tingkat kepentingan $x$ kali lipat terhadap elemen $B$, maka elemen $B$ secara otomatis memiliki tingkat kepentingan sebesar $\frac{1}{x}$ terhadap elemen $A$.

**Formula Matematis:**
$$ a*{ij} = \frac{1}{a*{ji}} $$

**Ilustrasi Sederhana:**
Jika IPK PSD adalah 3.48 dan IPK AI adalah 2.65, maka sistem menghitung bahwa PSD lebih unggul dari AI. Sistem mengonversi selisih ini menjadi skala Saaty **3.00 (Sedikit Lebih Penting)**.

- Maka di sel `(Baris PSD, Kolom AI)`, sistem menulis angka **3.00**.
- Secara otomatis, di sel `(Baris AI, Kolom PSD)`, nilainya wajib merupakan kebalikannya, yaitu $\frac{1}{3}$.
- $$ \frac{1}{3} = 0.333333... \approx 0.33 $$

Konsep ini memastikan bahwa Matriks AHP selalu bersifat simetris terhadap diagonal utamanya (di mana diagonal utamanya selalu bernilai 1.00 karena elemen dibandingkan dengan dirinya sendiri).

---

## 4. Pertanyaan 3: CARA MENGHITUNG EIGENVECTOR (BOBOT PRIORITAS)

_Pertanyaan Kritis: "Tabel perbandingan sudah dibuat. Bagaimana sistem merubah tabel itu menjadi persentase pemenang (Eigenvector)?"_

Proses mengubah Matriks Perbandingan Berpasangan menjadi Bobot Prioritas disebut dengan **Sintesis Matriks**. Pendekatan yang digunakan oleh program Python di sistem ini adalah _Approximation Method_ (Metode Rata-rata Normalisasi), yang terdiri dari 3 tahapan matematis murni:

**Langkah 1: Penjumlahan Kolom (Column Sum)**
Sistem menjumlahkan seluruh angka dari atas ke bawah untuk masing-masing kolom.
$$ C*j = \sum*{i=1}^{n} a\_{ij} $$
_(Contoh: Menjumlahkan seluruh angka di kolom vertikal AI)._

**Langkah 2: Normalisasi Matriks (Matrix Normalization)**
Sistem membagi setiap angka (sel) di dalam matriks dengan Jumlah Kolomnya masing-masing. Langkah ini berfungsi untuk mengubah semua rentang angka di dalam matriks menjadi format desimal (antara 0.0 hingga 1.0).
$$ X*{ij} = \frac{a*{ij}}{C*j} $$
*(Contoh: Jika angka di sel adalah 4, dan jumlah kolomnya adalah 8, maka sel dinormalisasi menjadi 4/8 = 0.5).\_

**Langkah 3: Rata-Rata Baris / Eigenvector (Row Average)**
Setelah matriks dinormalisasi, langkah terakhir adalah menjumlahkan seluruh angka secara menyamping (horizontal) dari kiri ke kanan pada satu baris, lalu membaginya dengan jumlah total elemen ($n$). Hasil akhir inilah yang disebut **Bobot Prioritas (Eigenvector)**.
$$ W*i = \frac{1}{n} \sum*{j=1}^{n} X\_{ij} $$
_(Contoh: Untuk mencari nilai akhir AI, jumlahkan semua angka di baris horizontal AI, lalu bagi dengan 4)._

---

## 5. SIMULASI KASUS NORMAL (MAHASISWA SEMESTER 6+)

Untuk membuktikan bahwa seluruh rumus di atas berjalan dengan baik, mari kita lakukan _Dry Run_ (Simulasi Manual) terhadap mahasiswa tingkat akhir yang sudah memiliki mata kuliah pilihan.

### TAHAP A: EKSTRAKSI NILAI MENTAH (RAW DATA)

Sistem membaca transkrip PDF mahasiswa dan mengekstrak data berbasis IPK yang dibobotkan dengan SKS: `Total Poin (Nilai × SKS) / Total SKS`.
Misalkan hasil ekstraksi sistem adalah sebagai berikut:

1. **Rata-rata IPK Dasar (_Foundation_):**
   - AI = 2.65
   - DMS = 3.43
   - PSD = 3.48
   - INFRA = 2.54
2. **Rata-rata IPK Keahlian (_Competency_):**
   - AI = 3.78
   - DMS = 3.90
   - PSD = 3.74
   - INFRA = 3.78
3. **Jumlah Kelas Keahlian (_Density_):**
   - AI = 12 kelas
   - DMS = 6 kelas
   - PSD = 9 kelas
   - INFRA = 6 kelas

### TAHAP B: KONVERSI NILAI MENTAH KE SKALA SAATY (1-9)

Sistem menggunakan dua rumus khusus (_Thresholding_):

- **Rumus Kualitas (IPK):** `Saaty = 1 + Round(|Selisih IPK| × 2)`
- **Rumus Minat (Kepadatan):** `Saaty = 1 + |Selisih Jumlah Kelas|`
  _(Catatan: Nilai dibatasi (clamped) maksimal 9.0 dan minimal 1.0)._

Mari kita ambil satu contoh komparasi dari **Kriteria Minat**: AI (12 kelas) melawan DMS (6 kelas).

- Selisih = $12 - 6 = 6$
- Saaty = $1 + 6 = 7$ (Sangat Kuat / _Very Strong_)
- Maka, sel `(AI, DMS) = 7.00` dan sel `(DMS, AI) = 1/7 = 0.14`.

### TAHAP C: PEMBANGUNAN MATRIKS & EIGENVECTOR (SIMULASI)

Berdasarkan rumus perhitungan Eigenvector di Pertanyaan 3, berikut adalah hasil akhir (Bobot Eigenvector) untuk masing-masing kriteria:

1. **Vektor Matriks Dasar ($V_f$):** (PSD unggul tipis dari DMS)
   - AI = 12.5%
   - DMS = 37.5%
   - PSD = 37.5%
   - INFRA = 12.5%
2. **Vektor Matriks Keahlian ($V_c$):** (Karena IPK mahasiswa rata di kisaran 3.7 - 3.9, semua dinilai sama pintar/Skala 1)
   - AI = 25.0%
   - DMS = 25.0%
   - PSD = 25.0%
   - INFRA = 25.0%
3. **Vektor Matriks Minat ($V_d$):** (AI meledak mendominasi karena mahasiswa ini mengambil 12 kelas AI)
   - AI = 61.3%
   - DMS = 7.3%
   - PSD = 24.0%
   - INFRA = 7.3%

### TAHAP D: SINTESIS AKHIR (PERKALIAN TOTAL)

Rumus akhir AHP adalah perkalian antara Bobot Alternatif dengan Bobot Kriteria Utama (Ingat Pertanyaan 1).
**Rumus:** `Skor Akhir = (V_f × 14.3%) + (V_c × 28.6%) + (V_d × 57.1%)`

Perhitungan untuk Profil AI:

- $\text{Skor AI} = (0.125 \times 0.143) + (0.250 \times 0.286) + (0.613 \times 0.571)$
- $\text{Skor AI} = 0.0179 + 0.0715 + 0.3500$
- **Skor Total AI = 0.4394 (43.94%)** $\rightarrow$ **JUARA 1 MENGALAHKAN PSD.**

**Kesimpulan SPK:** Meskipun IPK Dasar PSD mahasiswa lebih tinggi (3.48 vs 2.65), SPK secara objektif memenangkan AI karena sistem melihat dedikasi luar biasa (12 kelas) yang diambil mahasiswa di bidang AI. Ini membuktikan bahwa SPK tidak sekadar mencari rata-rata nilai, melainkan merepresentasikan "Minat Nyata".

---

## 6. SIMULASI _COLD START PROBLEM_ (MAHASISWA SEMESTER 4 KE BAWAH)

_Pertanyaan Kritis: "Bagaimana jika yang menggunakan sistem adalah mahasiswa Semester 2 atau 4? Mereka belum boleh mengambil mata kuliah peminatan sama sekali. Apakah rumusnya harus diubah?"_

Jawabannya adalah **TIDAK**. Secara struktur aljabar linear, rumus matematika AHP tidak pernah berubah. SPK ini menerapkan arsitektur **Adaptive AHP** menggunakan teknik **Mathematical Freezing (Pembekuan Matematis)** dan **Extreme Penalty Matrix (Matriks Penalti Ekstrem)**.

### Konsep _Mathematical Freezing_

Jika mahasiswa Semester 2 mengunggah transkrip, sistem akan melihat bahwa total kelas peminatan (_Competency_) adalah 0.
Karena jumlah kelas 0, maka nilai IPK Keahlian untuk AI, DMS, PSD, dan INFRA adalah 0.0.

Sistem memasukkan angka 0 ini ke rumus skala Saaty kita:

- Selisih AI (0.0) dan PSD (0.0) = 0.0
- `Saaty = 1 + 0 = 1.0` (Sama Penting / Ekuipartisi)

Hasilnya, Matriks Alternatif Keahlian dan Minat akan berbentuk datar (seluruh isinya bernilai 1). Jika dihitung Eigenvectornya, bobotnya akan terbagi sangat rata (25% untuk masing-masing AI, DMS, PSD, INFRA).
Karena bobotnya persis 25% untuk semua, **Kriteria Keahlian dan Minat menjadi netral secara matematis (Freeze) dan tidak merugikan profil mana pun.**

### Konsep _Extreme Penalty Matrix_

Sistem mendeteksi bahwa mahasiswa belum memiliki kelas peminatan (`total_elective == 0`). Maka sistem secara otomatis mengubah aturan pakar untuk **Matriks Kriteria Utama**.
Kualitas Dasar (Foundation) dipaksa mendapatkan prioritas absolut (Skala 9) terhadap kriteria lainnya.

| Kriteria     | Dasar | Keahlian | Minat |
| :----------- | :---- | :------- | :---- |
| **Dasar**    | 1     | 9        | 9     |
| **Keahlian** | 1/9   | 1        | 1     |
| **Minat**    | 1/9   | 1        | 1     |

_Eigenvector_ yang dihasilkan dari matriks penalti di atas adalah:

- **Bobot Dasar ($W_f$) = 0.818 (81.8%)**
- Bobot Keahlian ($W_c$) = 0.091 (9.1%)
- Bobot Minat ($W_d$) = 0.091 (9.1%)

### Pembuktian Matematis (Sintesis)

Mari kita buktikan rumusnya pada mahasiswa semester 2 ini. Misalnya _Eigenvector_ Kualitas Dasar mahasiswa ini adalah: AI (30%), PSD (50%), INFRA (10%), DMS (10%).

Skor Akhir PSD:

- $\text{Skor PSD} = (V_f \times W_f) + (V_c \times W_c) + (V_d \times W_d)$
- $\text{Skor PSD} = (0.50 \times 0.818) + (0.25 \times 0.091) + (0.25 \times 0.091)$
- $\text{Skor PSD} = 0.409 + 0.02275 + 0.02275 = \textbf{0.4545 (45.45\%)}$

Karena nilai $(0.25 \times 0.091) + (0.25 \times 0.091)$ selalu menghasilkan angka konstan (sama) untuk setiap profil, **maka pemenang mutlaknya akan diproyeksikan 100% dari rekam jejak nilai Kualitas Dasar ($V_f$) mahasiswa tersebut.** Inilah mengapa algoritma ini disebut sebagai Sistem Pendukung Keputusan yang sangat elegan dan adaptif.

---

## 7. VALIDASI LOGIKA: CONSISTENCY RATIO (CR)

AHP Saaty tidak akan sah tanpa adanya pembuktian Konsistensi. Matriks perbandingan berpasangan rawan terhadap inkonsistensi (Misal: A > B, B > C, tetapi tiba-tiba A < C).

Untuk memastikan logika sistem rasional, sistem secara _real-time_ menghitung _Consistency Ratio_ (CR). Syarat sahnya adalah **CR $\le$ 0.1 (atau 10%)**.

**Langkah 1: Menghitung Lambda Max ($\lambda_{\max}$)**
Sistem mengalikan Matriks Awal dengan Eigenvector, kemudian membaginya kembali dengan Eigenvector untuk mendapatkan nilai Eigenvalue di setiap baris. Rata-rata dari nilai Eigenvalue tersebut adalah $\lambda_{\max}$.
$$ \lambda*{\max} = \frac{1}{n} \sum*{i=1}^{n} \frac{\sum*{j=1}^{n} a*{ij} \times W_j}{W_i} $$

**Langkah 2: Menghitung Consistency Index (CI)**
Menghitung penyimpangan deviasi dari matriks sempurna ($n$).
$$ CI = \frac{\lambda\_{\max} - n}{n - 1} $$
*(Dimana $n$ adalah ukuran matriks. Jika membandingkan 4 profil, maka $n = 4$).\*

**Langkah 3: Menghitung Consistency Ratio (CR)**
Sistem membagi CI dengan _Random Index_ (RI). RI adalah indeks matriks acak yang ketetapannya telah dipatenkan oleh Saaty (Untuk matriks ukuran $n=4$, nilai RI adalah **0.90**).
$$ CR = \frac{CI}{RI} $$

Karena sistem SPK ini menghasilkan matriks tidak dari _input_ tebakan acak manusia, melainkan di-generate langsung oleh perhitungan selisih IPK secara linier, **maka seluruh matriks yang dihasilkan oleh sistem ini dipastikan memiliki tingkat konsistensi sempurna (Perfectly Consistent), di mana nilai CR yang dihasilkan selalu menempel di angka 0.00 hingga maksimal batas wajar.**

---

_Dokumentasi disusun secara khusus untuk memberikan transparansi absolut mengenai mekanisme kotak putih (White-Box) dari algoritma SPK Evaluasi Pemilihan Konsentrasi Akademik._
