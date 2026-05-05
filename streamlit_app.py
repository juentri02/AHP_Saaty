# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# Import backend services
from app.services.parser_service import parser_service
from app.services.ahp_service import ahp_service

st.set_page_config(page_title="SPK Profiling AHP", page_icon="🎓", layout="wide")

# --- CUSTOM CSS FOR HERO SECTION ---
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
    """Fungsi helper untuk merender langkah-langkah AHP Saaty."""
    st.markdown(f"#### 🧮 {matrix_result.matrix_name}")
    
    # --- MENAMPILKAN ASAL ANGKA (TRANSPARANSI) ---
    if matrix_result.raw_scores:
        with st.expander("🔍 Lihat Asal Angka (Data Mentah Mahasiswa)"):
            st.write(f"**Rumus Konversi:** `{matrix_result.conversion_rule}`")
            st.write("Nilai Mentah Mahasiswa untuk masing-masing profil:")
            df_raw = pd.DataFrame([matrix_result.raw_scores])
            st.dataframe(df_raw.style.format("{:.2f}"))
            st.caption("💡 *Cara baca: Sistem menghitung selisih angka mentah antara dua profil, lalu memasukkannya ke rumus di atas untuk menghasilkan skala Saaty 1-9 pada matriks di bawah.*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**1. Matriks Perbandingan Berpasangan**")
        df_pairwise = pd.DataFrame(
            matrix_result.pairwise_matrix, 
            index=matrix_result.criteria, 
            columns=matrix_result.criteria
        )
        st.dataframe(df_pairwise.style.format("{:.2f}"))

    with col2:
        st.write("**2. Matriks Normalisasi & Eigenvector (Bobot Prioritas)**")
        df_norm = pd.DataFrame(
            matrix_result.normalized_matrix, 
            index=matrix_result.criteria, 
            columns=matrix_result.criteria
        )
        df_norm['EIGENVECTOR'] = [matrix_result.eigenvector[c] for c in matrix_result.criteria]
        st.dataframe(df_norm.style.format("{:.3f}"))

    # Cek Konsistensi
    if matrix_result.is_consistent:
        st.success(f"✅ **Konsisten!** (CR = {matrix_result.consistency_ratio:.3f} $\le$ 0.1)")
    else:
        st.error(f"❌ **Tidak Konsisten!** (CR = {matrix_result.consistency_ratio:.3f} > 0.1)")
        
    st.caption(f"*Lambda Max: {matrix_result.lambda_max:.3f} | Consistency Index (CI): {matrix_result.consistency_index:.3f}*")
    st.divider()

# ==========================================
# MAIN APP
# ==========================================
st.title("🎓 Sistem Pendukung Keputusan (SPK) - Metode AHP")
st.markdown("Rekomendasi Profil Kelulusan Mahasiswa FTI UKDW berdasarkan Transkrip Nilai (Kurikulum 2021/2023).")

# 1. FILE UPLOAD
uploaded_file = st.file_uploader("Upload Transkrip Nilai (PDF)", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Memproses dokumen dan menjalankan algoritma AHP..."):
        try:
            # --- JALANKAN PIPELINE ---
            file_bytes = uploaded_file.read()
            transcript = parser_service.parse_pdf(file_bytes)
            
            if not transcript.courses:
                st.error("Gagal membaca mata kuliah. Pastikan PDF yang diupload adalah transkrip FTI UKDW yang valid.")
                st.stop()
                
            ahp_result = ahp_service.analyze_student(transcript)
            
            # --- TAMPILKAN DATA MAHASISWA ---
            st.subheader("👤 Data Mahasiswa")
            st.info(f"""
            **Nama:** {transcript.student_name}  
            **NIM:** {transcript.student_id} &nbsp;|&nbsp; **Total SKS:** {transcript.total_sks} &nbsp;|&nbsp; **IPK Ekstraksi:** {transcript.gpa:.2f}
            """)

            # --- HERO SECTION (PROFIL TERBAIK) ---
            best_profile = ahp_result.rankings[0]
            st.markdown(f"""
                <div class="best-profile">
                    <p>Berdasarkan analisis AHP, profil profesi terbaik untuk mahasiswa ini adalah:</p>
                    <h1>{best_profile.profile.value}</h1>
                    <p>Skor Akhir: <b>{best_profile.score:.4f}</b></p>
                </div>
            """, unsafe_allow_html=True)

            # --- 1. KESIMPULAN NARATIF OTOMATIS ---
            st.info(f"💡 **Analisis Sistem:** Mahasiswa ini sangat direkomendasikan untuk mengambil jalur **{best_profile.profile.value}**. "
                    f"Hal ini didukung oleh dominasi bobot pada kriteria minat (jumlah kelas) dan performa nilai keahlian. "
                    f"Profil alternatif kedua adalah **{ahp_result.rankings[1].profile.value}** dengan selisih skor {(best_profile.score - ahp_result.rankings[1].score):.4f}.")

            # --- 2. VISUALISASI GRAFIK BAR ---
            st.subheader("📈 Perbandingan Skor Akhir Profil")
            
            # Siapkan data untuk grafik
            chart_data = {
                "Profil":[r.profile.value for r in ahp_result.rankings],
                "Skor AHP":[round(r.score, 4) for r in ahp_result.rankings]
            }
            df_chart = pd.DataFrame(chart_data)
            
            # Buat Bar Chart menggunakan Plotly
            fig = px.bar(
                df_chart, 
                x="Skor AHP", 
                y="Profil", 
                orientation='h',
                text="Skor AHP",
                color="Profil",
                color_discrete_sequence=["#28a745", "#17a2b8", "#ffc107", "#dc3545"]
            )
            fig.update_layout(
                xaxis_title="Total Skor AHP (Bobot Prioritas Akhir)",
                yaxis_title="",
                showlegend=False,
                height=350,
                yaxis={'categoryorder':'total ascending'} # Urutkan dari skor terkecil ke terbesar
            )
            fig.update_traces(textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            st.divider()

            # --- BUKTI MATEMATIKA AHP SAATY (UNTUK PENGUJI) ---
            st.subheader("📊 Bukti Perhitungan SPK (Metode Saaty AHP)")
            st.write("Langkah-langkah perhitungan Matriks Perbandingan Berpasangan berdasarkan selisih rata-rata nilai dan kepadatan/jumlah kelas.")
            
            # Menggunakan 4 Tab karena sekarang kita punya 4 Matriks
            tab1, tab2, tab3, tab4 = st.tabs([
                "1. Kualitas Dasar", 
                "2. Kualitas Keahlian", 
                "3. Kepadatan / Minat", 
                "4. Sintesis Kriteria Utama"
            ])
            
            with tab1:
                render_matrix_proof(ahp_result.matrices[0])
            
            with tab2:
                render_matrix_proof(ahp_result.matrices[1])

            with tab3:
                render_matrix_proof(ahp_result.matrices[2])
                
            with tab4:
                render_matrix_proof(ahp_result.matrices[3])
                
                # Menampilkan Tabel Sintesis Akhir
                st.write("#### 🎯 Sintesis Akhir (Perkalian Bobot Gabungan)")
                synth_data =[]
                for r in ahp_result.rankings:
                    synth_data.append({
                        "Profil Alternatif": r.profile.value,
                        "Bobot Dasar (F)": round(r.foundation_score, 4),
                        "Bobot Keahlian (C)": round(r.competency_score, 4),
                        "Bobot Minat (D)": round(r.density_score, 4),
                        "Skor Akhir (AHP)": round(r.score, 4)
                    })
                st.dataframe(pd.DataFrame(synth_data).set_index("Profil Alternatif"))

            # --- RANKING LAINNYA YANG DISEMBUNYIKAN ---
            st.write("") # Spacer
            with st.expander("Lihat Peringkat Profil Lainnya (Ranking 2 - 4)"):
                for rank in ahp_result.rankings[1:]: # Skip rank 1
                    st.write(f"**Peringkat {rank.rank}: {rank.profile.value}** (Skor: {rank.score:.4f})")
                    # Visualisasi progress bar sederhana
                    st.progress(rank.score)

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {str(e)}")