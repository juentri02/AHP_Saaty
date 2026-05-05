# app/services/ahp_service.py
import pandas as pd
from typing import Dict, List

from app.models.schemas import (
    StudentTranscript, AHPMatrixResult, ProfileRanking, AHPFinalResult, ProfileType
)
from app.services.knowledge_base import knowledge_base
from app.services.ahp_math import ahp_math

class AHPSynthesisService:
    PROFILES = ["AI", "DMS", "PSD", "INFRA"]

    def analyze_student(self, transcript: StudentTranscript) -> AHPFinalResult:
        
        # 1. Hitung Nilai Rata-rata (Quality) & Jumlah Kelas (Density)
        raw_foundation = self._calculate_raw_scores(transcript, "FOUNDATION")
        raw_competency = self._calculate_raw_scores(transcript, "COMPETENCY")
        raw_density = self._calculate_density(transcript) # Hitung jumlah kelas

        matrices_results =[]
        
        # 2. Matriks 1: FOUNDATION (Quality)
        f_matrix, _ = self._build_pairwise_from_scores(raw_foundation)
        f_eigen, f_ci, f_cr, f_is_cons = self._process_matrix(f_matrix)
        matrices_results.append(self._package_matrix(
            "Kriteria 1: Nilai Dasar (Foundation)", self.PROFILES, f_matrix, f_eigen, f_ci, f_cr, f_is_cons,
            raw_scores=raw_foundation, conversion_rule="Skala Saaty = 1 + Round(Selisih Rata-rata IPK × 2)"
        ))

        # 3. Matriks 2: COMPETENCY (Quality)
        c_matrix, _ = self._build_pairwise_from_scores(raw_competency)
        c_eigen, c_ci, c_cr, c_is_cons = self._process_matrix(c_matrix)
        matrices_results.append(self._package_matrix(
            "Kriteria 2: Nilai Keahlian (Competency)", self.PROFILES, c_matrix, c_eigen, c_ci, c_cr, c_is_cons,
            raw_scores=raw_competency, conversion_rule="Skala Saaty = 1 + Round(Selisih Rata-rata IPK × 2)"
        ))

        # 4. Matriks 3: MINAT / DENSITY (Volume Kelas)
        d_matrix, _ = self._build_pairwise_from_counts(raw_density)
        d_eigen, d_ci, d_cr, d_is_cons = self._process_matrix(d_matrix)
        matrices_results.append(self._package_matrix(
            "Kriteria 3: Minat (Jumlah Kelas Profesi Diambil)", self.PROFILES, d_matrix, d_eigen, d_ci, d_cr, d_is_cons,
            raw_scores=raw_density, conversion_rule="Skala Saaty = 1 + Selisih Jumlah Kelas"
        ))

        # 5. MATRIKS KRITERIA UTAMA (ADAPTIVE AHP)
        criteria =["FOUNDATION", "COMPETENCY", "MINAT"]
        
        # Deteksi Fase Mahasiswa (Berapa total kelas peminatan yang sudah diambil?)
        total_elective_classes = sum(raw_density.values())
        
        if total_elective_classes == 0:
            # SKENARIO A: MAHASISWA TAHAP AWAL (Semester 4)
            # Karena belum ada kelas peminatan, Kualitas Dasar (Foundation) menjadi prioritas MUTLAK (Skala 9)
            crit_comparisons = {
                ("FOUNDATION", "COMPETENCY"): 9.0, 
                ("FOUNDATION", "MINAT"): 9.0,      
                ("COMPETENCY", "MINAT"): 1.0       # Keduanya sama-sama tidak ada (Sama Penting/Nol)
            }
            aturan_pakar_teks = "Adaptive AHP (Tahap Awal): Deteksi 0 kelas peminatan. Rekomendasi 100% didasarkan pada fondasi nilai dasar (Semester 1-4)."
        else:
            # SKENARIO B: MAHASISWA TAHAP LANJUT (Semester 5+)
            # Sudah mengambil kelas peminatan, maka Minat dan Keahlian menjadi prioritas utama.
            crit_comparisons = {
                ("COMPETENCY", "FOUNDATION"): 2.0, 
                ("MINAT", "FOUNDATION"): 4.0,      
                ("MINAT", "COMPETENCY"): 2.0       
            } 
            aturan_pakar_teks = "Adaptive AHP (Tahap Lanjut): Minat (Paling Penting) > Keahlian (Penting) > Dasar"

        # Buat Matriks berdasarkan skenario yang terpilih
        crit_matrix = ahp_math.create_pairwise_matrix(criteria, crit_comparisons)
        crit_eigen, crit_ci, crit_cr, crit_is_cons = self._process_matrix(crit_matrix)
        matrices_results.append(self._package_matrix(
            "Matriks Bobot Kriteria Utama (Adaptive)", criteria, crit_matrix, crit_eigen, crit_ci, crit_cr, crit_is_cons,
            raw_scores={"Total Kelas Peminatan Diambil": total_elective_classes}, 
            conversion_rule=aturan_pakar_teks
        ))

        # 6. SINTESIS AKHIR (Perkalian Bobot Eigenvector)
        w_f = crit_eigen["FOUNDATION"]
        w_c = crit_eigen["COMPETENCY"]
        w_d = crit_eigen["MINAT"]

        rankings =[]
        for profile in self.PROFILES:
            # (Skor F * Bobot F) + (Skor C * Bobot C) + (Skor D * Bobot D)
            score = (f_eigen[profile] * w_f) + (c_eigen[profile] * w_c) + (d_eigen[profile] * w_d)
            rankings.append(
                ProfileRanking(
                    profile=ProfileType(profile),
                    rank=0,
                    score=score,
                    foundation_score=f_eigen[profile],
                    competency_score=c_eigen[profile],
                    density_score=d_eigen[profile]
                )
            )

        # Urutkan Ranking
        rankings.sort(key=lambda x: x.score, reverse=True)
        for idx, r in enumerate(rankings):
            r.rank = idx + 1

        # Fix nama mata kuliah dari KB
        for course in transcript.courses:
            meta = knowledge_base.get_course_metadata(course.code)
            if meta:
                course.name = meta.name

        return AHPFinalResult(student=transcript, matrices=matrices_results, rankings=rankings)

    def _calculate_raw_scores(self, transcript: StudentTranscript, criteria_type: str) -> Dict[str, float]:
        scores = {p: {"total_points": 0.0, "count": 0} for p in self.PROFILES}
        for course in transcript.courses:
            rules = knowledge_base.get_rules_for_course(course.code, criteria_type)
            for profile in rules.keys():
                if profile in scores:
                    scores[profile]["total_points"] += course.grade_value
                    scores[profile]["count"] += 1
                    
        averages = {}
        for p in self.PROFILES:
            averages[p] = scores[p]["total_points"] / scores[p]["count"] if scores[p]["count"] > 0 else 0.01
        return averages

    def _calculate_density(self, transcript: StudentTranscript) -> Dict[str, int]:
        """Hitung jumlah kelas Competency yang diambil untuk setiap profil."""
        counts = {p: 0 for p in self.PROFILES}
        for course in transcript.courses:
            rules = knowledge_base.get_rules_for_course(course.code, "COMPETENCY")
            for profile in rules.keys():
                counts[profile] += 1
        return counts

    def _build_pairwise_from_scores(self, scores: Dict[str, float]) -> tuple:
        """Konversi IPK menjadi skala Saaty (Selisih IPK max 4.0)."""
        comparisons = {}
        for i, p1 in enumerate(self.PROFILES):
            for j, p2 in enumerate(self.PROFILES):
                if i >= j: continue
                diff = abs(scores[p1] - scores[p2])
                saaty_val = min(max(1.0 + round(diff * 2.0), 1.0), 9.0)
                
                if scores[p1] >= scores[p2]:
                    comparisons[(p1, p2)] = saaty_val
                else:
                    comparisons[(p2, p1)] = saaty_val

        matrix = ahp_math.create_pairwise_matrix(self.PROFILES, comparisons)
        return matrix, comparisons

    def _build_pairwise_from_counts(self, counts: Dict[str, int]) -> tuple:
        """Konversi Selisih Jumlah Kelas menjadi Skala Saaty (1-9)."""
        comparisons = {}
        for i, p1 in enumerate(self.PROFILES):
            for j, p2 in enumerate(self.PROFILES):
                if i >= j: continue
                diff = abs(counts[p1] - counts[p2])
                # Selisih 8 kelas berarti skala Saaty = 9 (Mutlak Penting)
                saaty_val = min(max(1.0 + diff, 1.0), 9.0)
                
                if counts[p1] >= counts[p2]:
                    comparisons[(p1, p2)] = saaty_val
                else:
                    comparisons[(p2, p1)] = saaty_val

        matrix = ahp_math.create_pairwise_matrix(self.PROFILES, comparisons)
        return matrix, comparisons

    def _process_matrix(self, matrix: pd.DataFrame):
        eigenvector = ahp_math.calculate_eigenvector(matrix)
        ci, cr, is_consistent = ahp_math.check_consistency(matrix, eigenvector)
        return eigenvector, ci, cr, is_consistent

    def _package_matrix(self, name: str, criteria: List[str], matrix: pd.DataFrame, 
                        eigen: pd.Series, ci: float, cr: float, is_cons: bool,
                        raw_scores: Dict[str, float] = None, conversion_rule: str = "") -> AHPMatrixResult:
        col_sums = matrix.sum(axis=0)
        norm_matrix = matrix.div(col_sums, axis=1)
        return AHPMatrixResult(
            matrix_name=name, criteria=criteria, pairwise_matrix=matrix.values.tolist(),
            normalized_matrix=norm_matrix.values.tolist(), eigenvector=eigen.to_dict(),
            lambda_max=ci * (len(criteria) - 1) + len(criteria), consistency_index=ci,
            consistency_ratio=cr, is_consistent=is_cons,
            raw_scores=raw_scores or {},           
            conversion_rule=conversion_rule        
        )

ahp_service = AHPSynthesisService()