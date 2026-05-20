# app/models/schemas.py
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
import pandas as pd

# ==========================================
# 1. ENUMS (Strict Vocabulary)
# ==========================================
class ProfileType(str, Enum):
    AI = "AI"
    DMS = "DMS"
    PSD = "PSD"
    INFRA = "INFRA"

class GradeLetter(str, Enum):
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    E = "E"

# ==========================================
# 2. COURSE & TRANSCRIPT MODELS
# ==========================================
class ParsedCourse(BaseModel):
    """Represents a single row extracted from the student's PDF transcript."""
    code: str = Field(..., description="Course code, e.g., TI6043")
    name: str = Field(..., description="Full course name")
    sks: int = Field(..., ge=1, le=12, description="SKS/Credit weight") # Sudah diganti sks max 12 dengan asumsi sks matkul tertinggi yang ada sekarang adalah 12
    grade_letter: str = Field(..., description="Raw letter grade from PDF")
    grade_value: float = Field(..., ge=0.0, le=4.0, description="Numeric academic weight (0.0 - 4.0)")

    model_config = ConfigDict(extra='ignore')

class StudentTranscript(BaseModel):
    """Represents the complete extracted academic history."""
    student_id: str = Field("UNKNOWN", description="NIM Mahasiswa")
    student_name: str = Field("UNKNOWN", description="Nama Mahasiswa")
    courses: List[ParsedCourse] = Field(default_factory=list)
    total_sks: int = Field(0, description="Total SKS taken")
    gpa: float = Field(0.0, description="Grade Point Average (IPK)")

# ==========================================
# 3. KNOWLEDGE BASE MODELS (YAML Mappings)
# ==========================================
class CourseMetadata(BaseModel):
    """Metadata from courses.yaml"""
    code: str
    name: str
    sks: int

# ==========================================
# 4. AHP RESULT MODELS (For UI Rendering)
# ==========================================
class AHPMatrixResult(BaseModel):
    """
    Stores the exact mathematical steps for transparency in the UI.
    This is CRITICAL for the Skripsi defense (SPK calculations).
    """
    matrix_name: str
    criteria: List[str]
    pairwise_matrix: List[List[float]] # Nested list representing pd.DataFrame
    normalized_matrix: List[List[float]]
    eigenvector: Dict[str, float] # Priority weights
    lambda_max: float
    consistency_index: float
    consistency_ratio: float
    is_consistent: bool
    raw_scores: Dict[str, float] = {} 
    conversion_rule: str = ""

class ProfileRanking(BaseModel):
    """Final output ranking for the 4 profiles."""
    profile: ProfileType
    rank: int
    score: float
    foundation_score: float
    competency_score: float
    density_score: float

class AHPFinalResult(BaseModel):
    """The master wrapper for the entire calculation process."""
    student: StudentTranscript
    matrices: List[AHPMatrixResult] # All matrices used in calculation
    rankings: List[ProfileRanking]  # The final sorted recommendation
    is_early_stage: bool = False