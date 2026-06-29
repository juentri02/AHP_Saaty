# streamlit_app.py
import streamlit as st
import pandas as pd

# Import backend services
from app.services.parser_service import parser_service
from app.services.ahp_service import ahp_service

st.set_page_config(page_title="SPK Profiling AHP", page_icon="🎓", layout="wide")

# --- CUSTOM CSS FOR HERO SECTION (Dipertahankan karena bagus) ---
st.markdown("""
    <style>
    .best-profile {
        background-color: #d4edda;
        color: #155724;
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #c3e6cb;
        margin-bottom: 20px;
    }
    .best-profile h1 { margin: 0; font-size: 3em; color: #155724; }
    .best-profile p { font-size: 1.2em; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

def render_matrix_proof(matrix_result):
    """Fungsi helper untuk merender langkah-langkah AHP Saaty secara Edukatif & Transparan."""
    st.markdown(f"### 🧮 {matrix_result.matrix_name}")
    
    # --- TAHAP 1: DATA MENTAH & KONVERSI (Menggunakan st.info bawaan Streamlit) ---
    if matrix_result.raw_scores:
        st.info("**TAHAP 1: Ekstraksi Data Mentah & Konversi Skala Saaty**  \nSistem membaca nilai asli mahasiswa dan mengonversinya menjadi Skala Kepentingan (1-9).")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("**Nilai Mentah Mahasiswa:**")
            df_raw = pd.DataFrame([matrix_result.raw_scores])
            st.dataframe(df_raw.style.format("{:.2f}"))
        with c2:
            st.write("**Rumus Konversi:**")
            st.code(matrix_result.conversion_rule, language="text")
            st.caption("Contoh: Jika nilai AI lebih tinggi dari PSD, selisihnya dimasukkan ke rumus di atas untuk menghasilkan angka 1 hingga 9. Jika AI bernilai 3, maka PSD terhadap AI otomatis bernilai 1/3 (0.33) berdasarkan *Aksioma Timbal Balik*.")

    st.write("---")

    # --- TAHAP 2: MATRIKS BERPASANGAN (Menggunakan st.info bawaan Streamlit) ---
    st.info("**TAHAP 2: Matriks Perbandingan Berpasangan**  \nAngka hasil konversi dimasukkan ke dalam matriks. Langkah selanjutnya adalah **menjumlahkan setiap kolom ke bawah** untuk keperluan normalisasi.")
    
    # Menyiapkan DataFrame Matriks Awal
    df_pairwise = pd.DataFrame(
        matrix_result.pairwise_matrix, 
        index=matrix_result.criteria, 
        columns=matrix_result.criteria
    )
    # Menambahkan baris "JUMLAH KOLOM"
    df_pairwise.loc['JUMLAH KOLOM'] = df_pairwise.sum(axis=0)
    st.dataframe(df_pairwise.style.format("{:.2f}"))

    st.write("---")

    # --- TAHAP 3: NORMALISASI & EIGENVECTOR (Menggunakan st.info bawaan Streamlit) ---
    st.info("**TAHAP 3: Normalisasi & Perhitungan Bobot Prioritas (Eigenvector)**  \nSetiap angka pada matriks di atas dibagi dengan **Jumlah Kolomnya** masing-masing. Setelah itu, angka dijumlahkan menyamping dan dirata-rata untuk mendapatkan **Bobot Prioritas (Eigenvector)**.")

    df_norm = pd.DataFrame(
        matrix_result.normalized_matrix, 
        index=matrix_result.criteria, 
        columns=matrix_result.criteria
    )
    df_norm['BOBOT PRIORITAS (Eigenvector)'] = [matrix_result.eigenvector[c] for c in matrix_result.criteria]
    st.dataframe(df_norm.style.format("{:.3f}"))

    # Mencari nilai tertinggi (Pemenang) dari kamus Eigenvector
    sorted_eigen = sorted(matrix_result.eigenvector.items(), key=lambda x: x[1], reverse=True)
    top_name, top_score = sorted_eigen[0]
    
    # Membuat kalimat yang berbeda untuk Matriks Profil vs Matriks Kriteria Utama
    if "Kriteria Utama" in matrix_result.matrix_name:
        st.success(f"💡 **Interpretasi Hasil:** Berdasarkan perhitungan matematis di atas, kriteria **{top_name}** memegang pengaruh paling krusial dengan bobot **{top_score*100:.1f}%**. Kriteria ini akan memberikan dorongan paling besar dalam penentuan skor akhir mahasiswa.")
    else:
        st.success(f"💡 **Interpretasi Hasil:** Pada matriks ini, profil **{top_name}** mendominasi dengan persentase bobot kemenangan sebesar **{top_score*100:.1f}%**. Angka ini membuktikan bahwa {top_name} paling unggul dibandingkan profil lainnya dalam penilaian kriteria ini.")

    # --- TAHAP 4: KONSISTENSI ---
    if matrix_result.is_consistent:
        st.success(f"✅ **Matriks Rasional dan Konsisten!** (Consistency Ratio = {matrix_result.consistency_ratio:.3f} $\\le$ 0.1)")
    else:
        st.error(f"❌ **Matriks Tidak Konsisten!** (Consistency Ratio = {matrix_result.consistency_ratio:.3f} > 0.1)")
        
    st.caption(f"*Bukti Matematis:* Lambda Max = {matrix_result.lambda_max:.3f}, Consistency Index (CI) = {matrix_result.consistency_index:.3f}")
    st.write("<br><br>", unsafe_allow_html=True)


# ==========================================
# MAIN APP
# ==========================================
st.title("Sistem Pendukung Keputusan (SPK) - Metode AHP")
st.markdown("Rekomendasi Profil Kelulusan Mahasiswa FTI UKDW berdasarkan Transkrip Nilai (Kurikulum 2021/2023).")

# 1. PILIHAN KRITERIA FLEKSIBEL
st.subheader("⚙️ Mode Simulasi Kriteria")
criteria_options = {
    "FOUNDATION": "Foundation / Nilai Dasar",
    "COMPETENCY": "Competency / Nilai Keahlian",
    "MINAT": "Minat / Jumlah Mata Kuliah Profesi"
}
selected_criteria = st.multiselect(
    "Pilih kriteria yang ingin digunakan dalam perhitungan rekomendasi:",
    options=list(criteria_options.keys()),
    default=list(criteria_options.keys()),
    format_func=lambda x: criteria_options[x],
    help="User dapat mencoba 1, 2, atau 3 kriteria. Kriteria yang tidak dipilih tidak akan masuk ke skor akhir."
)

if len(selected_criteria) == 0:
    st.warning("Pilih minimal 1 kriteria agar sistem dapat menghitung rekomendasi.")
elif len(selected_criteria) == 1:
    st.info(f"Mode aktif: **1 kriteria**. Skor akhir hanya dihitung dari **{criteria_options[selected_criteria[0]]}**.")
elif len(selected_criteria) == 2:
    selected_text = " dan ".join([criteria_options[c] for c in selected_criteria])
    st.info(f"Mode aktif: **2 kriteria**. Skor akhir hanya dihitung dari **{selected_text}**.")
else:
    st.info("Mode aktif: **3 kriteria lengkap**. Sistem memakai Foundation, Competency, dan Minat seperti perhitungan utama.")

# 2. FILE UPLOAD
uploaded_file = st.file_uploader("Upload Transkrip Nilai (PDF)", type=["pdf"])

if uploaded_file is not None:
    if len(selected_criteria) == 0:
        st.error("Perhitungan tidak dapat dilanjutkan karena belum ada kriteria yang dipilih.")
        st.stop()

    with st.spinner("Mengekstrak data, membangun matriks, dan menjalankan algoritma AHP..."):
        try:
            # --- JALANKAN PIPELINE ---
            file_bytes = uploaded_file.read()
            transcript = parser_service.parse_pdf(file_bytes)
            
            if not transcript.courses:
                st.error("Gagal membaca data. Sistem mensyaratkan pengguna minimal berada di Semester 2 (telah memiliki rekam jejak nilai Semester 1 yang sah pada transkrip FTI UKDW).")
                st.stop()
                
            ahp_result = ahp_service.analyze_student(transcript, selected_criteria=selected_criteria)
            selected_criteria = ahp_result.selected_criteria
            criteria_weight_matrix = ahp_result.matrices[-1]
            criteria_weights = criteria_weight_matrix.eigenvector
            
            # --- TAMPILKAN DATA MAHASISWA ---
            st.subheader("👤 Data Mahasiswa")
            st.info(f"""
            **Nama:** {transcript.student_name}  
            **NIM:** {transcript.student_id} &nbsp;|&nbsp; **Total SKS:** {transcript.total_sks} &nbsp;|&nbsp; **IPK Ekstraksi:** {transcript.gpa:.2f}  
            **Kriteria Dipakai:** {", ".join([criteria_options[c] for c in selected_criteria])}
            """)

            # --- SMART DETECTION UNTUK MAHASISWA TAHAP AWAL ---
            if ahp_result.is_early_stage and len(selected_criteria) > 1:
                st.warning("""
                Sistem mendeteksi bahwa mahasiswa ini belum mengambil Mata Kuliah Pilihan Profesi (umumnya berada di Semester 4 ke bawah). 
                Jika lebih dari satu kriteria dipilih, sistem tetap memakai aturan **Adaptive AHP Tahap Awal**. Namun, user tetap dapat mencoba satu kriteria saja melalui fitur simulasi fleksibel.
                """)

            # --- HERO SECTION (PROFIL TERBAIK) ---
            best_profile = ahp_result.rankings[0]
            st.markdown(f"""
                <div class="best-profile">
                    <p>Berdasarkan simulasi kriteria yang dipilih, profil profesi terbaik yang direkomendasikan adalah:</p>
                    <h1>{best_profile.profile.value}</h1>
                    <p>Skor Akhir: <b>{best_profile.score:.4f}</b></p>
                </div>
            """, unsafe_allow_html=True)

            # --- RANKING LAINNYA ---
            with st.expander("Lihat Peringkat Profil Lainnya (Ranking 2 - 4)"):
                for rank in ahp_result.rankings[1:]:
                    st.write(f"**Peringkat {rank.rank}: {rank.profile.value}** (Skor: {rank.score:.4f})")
                    st.progress(rank.score)

            st.divider()

            # --- BUKTI MATEMATIKA AHP SAATY TRANSPARAN ---
            st.subheader("📊 Transparansi Algoritma")
            st.write("Sistem hanya menampilkan matriks dari kriteria yang dipilih user. Kriteria yang tidak dipilih tidak ikut dihitung dalam skor akhir.")
            
            tab_names = []
            for idx, matrix_result in enumerate(ahp_result.matrices):
                if idx == len(ahp_result.matrices) - 1:
                    tab_names.append("Sintesis Kriteria")
                else:
                    tab_names.append(matrix_result.matrix_name.replace("Kriteria ", ""))

            tabs = st.tabs(tab_names)
            for idx, tab in enumerate(tabs):
                with tab:
                    matrix_result = ahp_result.matrices[idx]
                    render_matrix_proof(matrix_result)

                    # Tabel sintesis hanya muncul di tab terakhir
                    if idx == len(ahp_result.matrices) - 1:
                        st.info("**TAHAP FINAL: Sintesis Akhir Fleksibel**  \nSistem mengalikan bobot alternatif hanya pada kriteria yang dipilih user. Kriteria yang tidak dipilih dianggap tidak berkontribusi terhadap skor akhir.")

                        score_attr = {
                            "FOUNDATION": "foundation_score",
                            "COMPETENCY": "competency_score",
                            "MINAT": "density_score"
                        }

                        synth_data = []
                        for r in ahp_result.rankings:
                            row = {"Profil Alternatif": r.profile.value}
                            for criteria_name in selected_criteria:
                                label = criteria_options[criteria_name]
                                alternative_score = getattr(r, score_attr[criteria_name])
                                criteria_weight = criteria_weights[criteria_name]
                                row[f"{label} × Bobot"] = f"({alternative_score:.3f} × {criteria_weight:.3f})"
                            row["Skor Akhir"] = round(r.score, 4)
                            synth_data.append(row)

                        st.dataframe(pd.DataFrame(synth_data).set_index("Profil Alternatif"))

                        st.caption("Contoh: jika user hanya memilih Foundation, maka bobot Foundation = 1.000 dan skor akhir sama dengan bobot alternatif pada matriks Foundation.")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {str(e)}")
