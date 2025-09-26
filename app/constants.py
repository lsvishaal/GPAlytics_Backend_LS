"""
Application constants for GPAlytics
Centralized configuration values
"""

# Grade point mapping for Indian university system
GRADE_POINTS_MAP = {
    "O": 10.0,   # Outstanding
    "A+": 9.0,   # Excellent
    "A": 8.0,    # Very Good
    "B+": 7.0,   # Good
    "B": 6.0,    # Above Average
    "C": 5.0,    # Average
    "D": 4.0,    # Below Average
    "F": 0.0,    # Fail
    "U": 0.0,    # University exam failed
    "AB": 0.0    # Absent
}

# File upload constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ["image/png", "image/jpeg", "image/jpg"]

# Academic constraints
MIN_SEMESTER = 1
MAX_SEMESTER = 12
MIN_CREDITS = 1
MAX_CREDITS = 6
MIN_GRADE_POINTS = 0.0
MAX_GRADE_POINTS = 10.0

# Batch year constraints
MIN_BATCH_YEAR = 2015
MAX_BATCH_YEAR = 2045

# Registration number constraints
REGNO_LENGTH = 15
REGNO_ALPHA_CHARS = 2
REGNO_DIGIT_CHARS = 13
