# app/services/ahp_service.py
import pandas as pd
from typing import Dict, List, Optional

from app.models.schemas import (
    StudentTranscript, AHPMatrixResult, ProfileRanking, AHPFinalResult, ProfileType
)
from app.services.knowledge_base import knowledge_base
from app.services.ahp_math import ahp_math

class AHPSynthesisService:
    PROFILES = ["AI", "DMS", "PSD", "INFRA"]
    CRITERIA = ["FOUNDATION", "COMPETENCY", "MINAT"]

    def analyze_student(self, transcript: StudentTranscript, selected_criteria: Optional[List[str]] = None) -> AHPFinalResult:
        """
        Menjalankan analisis AHP.

        selected_criteria membuat sistem fleksibel:
        - Jika user memilih 1 kriteria, skor akhir hanya memakai kriteria tersebut.
        - Jika user memilih 2 kriteria, bobot sintesis hanya dihitung dari 2 kriteria aktif.
        - Jika user memilih 3 kriteria, sistem berjalan seperti mode awal/adaptive penuh.
        """
        selected_criteria = self._normalize_selected_criteria(selected_criteria)

        # 1. Hitung Nilai Rata-rata (Quality) & Jumlah Kelas (Density)
        raw_foundation = self._calculate_raw_scores(transcript, "FOUNDATION")
        raw_competency = self._calculate_raw_scores(transcript, "COMPETENCY")
        raw_density = self._calculate_density(transcript) # Hitung jumlah kelas

        matrices_results = []
        matrix_by_criteria = {}

        # 2. Matriks 1: FOUNDATION (Quality)
        f_matrix, _ = self._build_pairwise_from_scores(raw_foundation)
        f_eigen, f_ci, f_cr, f_is_cons = self._process_matrix(f_matrix)
        matrix_by_criteria["FOUNDATION"] = self._package_matrix(
            "Kriteria 1: Nilai Dasar (Foundation)", self.PROFILES, f_matrix, f_eigen, f_ci, f_cr, f_is_cons,
            raw_scores=raw_foundation, conversion_rule="Skala Saaty = 1 + Round(Selisih Rata-rata IPK × 2)"
        )

        # 3. Matriks 2: COMPETENCY (Quality)
        c_matrix, _ = self._build_pairwise_from_scores(raw_competency)
        c_eigen, c_ci, c_cr, c_is_cons = self._process_matrix(c_matrix)
        matrix_by_criteria["COMPETENCY"] = self._package_matrix(
            "Kriteria 2: Nilai Keahlian (Competency)", self.PROFILES, c_matrix, c_eigen, c_ci, c_cr, c_is_cons,
            raw_scores=raw_competency, conversion_rule="Skala Saaty = 1 + Round(Selisih Rata-rata IPK × 2)"
        )

        # 4. Matriks 3: MINAT / DENSITY (Volume Kelas)
        d_matrix, _ = self._build_pairwise_from_counts(raw_density)
        d_eigen, d_ci, d_cr, d_is_cons = self._process_matrix(d_matrix)
        matrix_by_criteria["MINAT"] = self._package_matrix(
            "Kriteria 3: Minat (Jumlah Kelas Profesi Diambil)", self.PROFILES, d_matrix, d_eigen, d_ci, d_cr, d_is_cons,
            raw_scores=raw_density, conversion_rule="Skala Saaty = 1 + Selisih Jumlah Kelas"
        )

        # Masukkan ke hasil hanya matriks kriteria yang dipilih user.
        # Dengan begitu, tab transparansi tidak menampilkan kriteria yang sedang tidak digunakan.
        for criteria_name in selected_criteria:
            matrices_results.append(matrix_by_criteria[criteria_name])

        # 5. MATRIKS KRITERIA UTAMA (FLEKSIBEL + ADAPTIVE)
        total_elective_classes = sum(raw_density.values())
        crit_matrix, aturan_pakar_teks = self._build_flexible_criteria_matrix(selected_criteria, total_elective_classes)
        crit_eigen, crit_ci, crit_cr, crit_is_cons = self._process_matrix(crit_matrix)
        matrices_results.append(self._package_matrix(
            "Matriks Bobot Kriteria Utama (Fleksibel)", selected_criteria, crit_matrix, crit_eigen, crit_ci, crit_cr, crit_is_cons,
            raw_scores={
                "Total Kelas Peminatan Diambil": total_elective_classes,
                "Jumlah Kriteria Dipakai": len(selected_criteria)
            },
            conversion_rule=aturan_pakar_teks
        ))

        # 6. SINTESIS AKHIR (Hanya memakai kriteria yang dipilih user)
        eigen_by_criteria = {
            "FOUNDATION": f_eigen,
            "COMPETENCY": c_eigen,
            "MINAT": d_eigen
        }

        rankings = []
        for profile in self.PROFILES:
            score = 0.0
            for criteria_name in selected_criteria:
                score += eigen_by_criteria[criteria_name][profile] * crit_eigen[criteria_name]

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

        # Check if early stage (No profile classes taken)
        is_early = total_elective_classes == 0

        return AHPFinalResult(
            student=transcript,
            matrices=matrices_results,
            rankings=rankings,
            is_early_stage=is_early,
            selected_criteria=selected_criteria
        )

    def _normalize_selected_criteria(self, selected_criteria: Optional[List[str]]) -> List[str]:
        """Validasi pilihan kriteria agar hanya berisi FOUNDATION, COMPETENCY, dan MINAT."""
        if not selected_criteria:
            return self.CRITERIA.copy()

        selected_clean = []
        for criteria_name in selected_criteria:
            criteria_name = str(criteria_name).upper().strip()
            if criteria_name in self.CRITERIA and criteria_name not in selected_clean:
                selected_clean.append(criteria_name)

        if not selected_clean:
            return self.CRITERIA.copy()
        return selected_clean

    def _build_flexible_criteria_matrix(self, selected_criteria: List[str], total_elective_classes: int):
        """Membuat matriks bobot kriteria sesuai jumlah kriteria yang dipilih user."""
        if len(selected_criteria) == 1:
            criteria_name = selected_criteria[0]
            comparisons = {}
            aturan_pakar_teks = (
                f"Mode Fleksibel 1 Kriteria: hanya memakai {criteria_name}. "
                f"Bobot {criteria_name} = 1.00, sedangkan kriteria lain tidak ikut dihitung."
            )
            return ahp_math.create_pairwise_matrix(selected_criteria, comparisons), aturan_pakar_teks

        if total_elective_classes == 0:
            # Tahap awal: Foundation dibuat dominan karena mahasiswa belum punya data kelas peminatan.
            base_comparisons = {
                ("FOUNDATION", "COMPETENCY"): 9.0,
                ("FOUNDATION", "MINAT"): 9.0,
                ("COMPETENCY", "MINAT"): 1.0
            }
            aturan_pakar_teks = (
                "Mode Fleksibel + Adaptive Tahap Awal: sistem hanya menghitung kriteria yang dipilih user. "
                "Jika Foundation dipilih bersama kriteria lain, Foundation tetap menjadi prioritas karena belum ada kelas peminatan."
            )
        else:
            # Tahap lanjut: mahasiswa sudah punya kelas peminatan, sehingga minat dan keahlian lebih dominan.
            base_comparisons = {
                ("COMPETENCY", "FOUNDATION"): 2.0,
                ("MINAT", "FOUNDATION"): 4.0,
                ("MINAT", "COMPETENCY"): 2.0
            }
            aturan_pakar_teks = (
                "Mode Fleksibel + Adaptive Tahap Lanjut: sistem hanya menghitung kriteria yang dipilih user. "
                "Perbandingan antar kriteria aktif tetap mengikuti aturan adaptive AHP: Minat > Keahlian > Dasar."
            )

        # Filter agar matriks utama hanya berisi kriteria yang dipilih user.
        comparisons = {}
        for (left, right), value in base_comparisons.items():
            if left in selected_criteria and right in selected_criteria:
                comparisons[(left, right)] = value

        return ahp_math.create_pairwise_matrix(selected_criteria, comparisons), aturan_pakar_teks

    def _calculate_raw_scores(self, transcript: StudentTranscript, criteria_type: str) -> Dict[str, float]:
        """Menghitung IPK asli (Weighted by SKS) untuk mata kuliah pada kriteria tertentu."""
        scores = {p: {"total_weighted_points": 0.0, "total_sks": 0} for p in self.PROFILES}
        
        for course in transcript.courses:
            rules = knowledge_base.get_rules_for_course(course.code, criteria_type)
            for profile in rules.keys():
                if profile in scores:
                    # Rumus IPK: (Nilai x SKS)
                    scores[profile]["total_weighted_points"] += (course.grade_value * course.sks)
                    scores[profile]["total_sks"] += course.sks
                    
        averages = {}
        for p in self.PROFILES:
            if scores[p]["total_sks"] > 0:
                # Hasil akhir IPK: Total Poin / Total SKS
                averages[p] = scores[p]["total_weighted_points"] / scores[p]["total_sks"]
            else:
                averages[p] = 0.01 # Cegah zero-division
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
