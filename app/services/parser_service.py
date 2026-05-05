# app/services/parser_service.py
import re
import pdfplumber
from io import BytesIO
from typing import List, Set, Tuple

from app.models.schemas import StudentTranscript, ParsedCourse

class TranscriptParser:
    """
    Robust PDF Parser specifically designed for Indonesian University Transcripts.
    Extracts NIM, Name, and Course Rows using strict Regex mapping.
    """

    # --- REGEX PATTERNS ---
    # Matches: "TI6043 Machine Learning 3 A"
    # Group 1: Code (Must be TI, MH, EL followed by 4 digits)
    # Group 2: SKS (1 or 2 digits)
    # Group 3: Grade (A-E, optional +/-)
    COURSE_REGEX = re.compile(r"((?:TI|MH|EL)\d{4})\s+.*?\s+(\d{1,2})\s+([A-E][+-]?)")
    
    # Metadata Patterns
    NIM_PATTERN = re.compile(r"No\.?\s*Mahasiswa\s*[:]\s*(\d+)", re.IGNORECASE)
    NAME_PATTERN = re.compile(r"Nama\s*[:]\s*([^\n\r]+?)(?=\s+(?:Fakultas|Program|$))", re.IGNORECASE)

    # --- ACADEMIC GRADE MAPPING ---
    GRADE_MAP = {
        'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0,
        'D': 1.0, 'E': 0.0
    }

    def parse_pdf(self, file_bytes: bytes) -> StudentTranscript:
        """
        Main entry point. Reads raw PDF bytes, extracts all text, 
        and constructs a validated StudentTranscript object.
        """
        full_text = self._extract_text_from_pdf(file_bytes)
        
        if not full_text.strip():
            raise ValueError("Parser Error: The PDF is empty or consists only of unreadable images (scanned).")

        # Extract Metadata
        student_id = self._extract_metadata(full_text, self.NIM_PATTERN, "UNKNOWN_NIM")
        student_name = self._extract_metadata(full_text, self.NAME_PATTERN, "UNKNOWN_NAME")
        
        # Extract Courses
        parsed_courses = self._extract_courses(full_text)

        # Calculate Transcript Stats
        total_sks = sum(c.sks for c in parsed_courses)
        gpa = 0.0
        if total_sks > 0:
            total_points = sum(c.sks * c.grade_value for c in parsed_courses)
            gpa = round(total_points / total_sks, 2)

        return StudentTranscript(
            student_id=student_id,
            student_name=student_name,
            courses=parsed_courses,
            total_sks=total_sks,
            gpa=gpa
        )

    def _extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Safely opens the PDF stream and extracts all text page by page."""
        text_content = ""
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    # Using layout=True often helps with column-based transcripts
                    page_text = page.extract_text(layout=False)
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            raise ValueError(f"Failed to read PDF file format: {str(e)}")
            
        return text_content

    def _extract_metadata(self, text: str, pattern: re.Pattern, default: str) -> str:
        """Helper to find Regex patterns for NIM and Name."""
        match = pattern.search(text)
        if match:
            # Strip trailing whitespaces or unwanted characters
            return match.group(1).strip()
        return default

    def _extract_courses(self, text: str) -> List[ParsedCourse]:
        """
        Loops through all Regex matches to find valid courses.
        Uses a Set to prevent duplicates if the PDF headers repeat on page 2.
        """
        results: List[ParsedCourse] = []
        seen_codes: Set[str] = set()

        matches: List[Tuple[str, str, str]] = self.COURSE_REGEX.findall(text)

        for code, sks_str, grade_letter in matches:
            raw_code = code.strip().upper()
            
            # Prevent duplicate counting
            if raw_code in seen_codes:
                continue

            try:
                sks_val = int(sks_str)
                # If a weird grade appears, default to 0.0 to be safe
                grade_val = self.GRADE_MAP.get(grade_letter, 0.0)
                
                # We use a placeholder name here.
                # In Phase 4, the KnowledgeBase will inject the correct official name from courses.yaml.
                course_obj = ParsedCourse(
                    code=raw_code,
                    name=f"Course {raw_code}", # Placeholder
                    sks=sks_val,
                    grade_letter=grade_letter,
                    grade_value=grade_val
                )
                
                results.append(course_obj)
                seen_codes.add(raw_code)

            except Exception as e:
                # In a strict academic parser, we log this but don't crash the whole process
                print(f"Warning: Failed to parse course {raw_code}. Reason: {e}")
                continue

        return results

# Singleton instantiation
parser_service = TranscriptParser()