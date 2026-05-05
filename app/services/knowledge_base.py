# app/services/knowledge_base.py
import yaml
import logging
import threading
from typing import Dict, List, Any, Optional

from app.core.config import settings
from app.models.schemas import CourseMetadata

logger = logging.getLogger("ahp_spk")

class KnowledgeBase:
    """
    Loads and serves YAML expert data. Uses Thread Lock to prevent 
    memory corruption in Streamlit's multi-threaded environment.
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        self._raw_courses = self._load_yaml("courses.yaml")
        self._raw_relevance = self._load_yaml("relevance_rules.yaml")
        
        # O(1) Lookup Tables
        self._metadata_map: Dict[str, CourseMetadata] = {}
        self._foundation_rules: Dict[str, Dict[str, float]] = {}
        self._competency_rules: Dict[str, Dict[str, float]] = {}
        
        self._build_indexes()

    def _load_yaml(self, filename: str) -> Any:
        file_path = settings.DATA_DIR / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return {}

    def _build_indexes(self):
        """Indexes data for instant O(1) lookups."""
        with self._lock:
            # 1. Build Metadata Map
            for item in self._raw_courses:
                code = item.get('code', '').upper()
                if code:
                    self._metadata_map[code] = CourseMetadata(
                        code=code, name=item.get('name', ''), sks=item.get('sks', 0)
                    )
            
            # 2. Build Rule Maps
            self._foundation_rules = self._raw_relevance.get('FOUNDATION', {})
            self._competency_rules = self._raw_relevance.get('COMPETENCY', {})

    def get_course_metadata(self, code: str) -> Optional[CourseMetadata]:
        return self._metadata_map.get(code.upper())

    def get_rules_for_course(self, code: str, criteria_type: str) -> Dict[str, float]:
        """
        Returns { 'AI': 1.0, 'PSD': 1.0 } if the course belongs to those profiles.
        criteria_type must be "FOUNDATION" or "COMPETENCY"
        """
        code = code.upper()
        if criteria_type == "FOUNDATION":
            return self._foundation_rules.get(code, {})
        elif criteria_type == "COMPETENCY":
            return self._competency_rules.get(code, {})
        return {}

# Singleton
knowledge_base = KnowledgeBase()