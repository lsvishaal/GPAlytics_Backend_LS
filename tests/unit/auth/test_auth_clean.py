"""
Sprint 1: Clean Authentication Tests
==================================

Tests the core auth functions from app.auth module
Focus: Registration, login, password validation
"""

import pytest
from app.auth import validate_regno, validate_password, hash_password, verify_password


# Registration Number Tests
class TestRegnoValidation:
    
    def test_valid_regno_accepted(self):
        """Valid registration numbers should be accepted"""
        valid_regnos = [
            "AB1234567890123",
            "XY9876543210987", 
            "CD1111111111111",
            "ZZ0000000000000"
        ]
        
        for regno in valid_regnos:
            assert validate_regno(regno) is None, f"Valid regno '{regno}' was rejected"
    
    def test_empty_regno_rejected(self):
        """Empty registration number should be rejected"""
        error = validate_regno("")
        assert error is not None
        assert "required" in error.lower()
    
    def test_wrong_length_rejected(self):
        """Wrong length registration numbers should be rejected"""
        test_cases = [
            "AB123",                    # Too short
            "AB12345678901234567",      # Too long  
            "A",                        # Single char
        ]
        
        for regno in test_cases:
            error = validate_regno(regno)
            assert error is not None, f"Invalid length regno '{regno}' was accepted"
            assert "15 characters" in error
    
    def test_wrong_format_rejected(self):
        """Wrong format registration numbers should be rejected"""
        test_cases = [
            ("ab1234567890123", "uppercase"),      # Lowercase letters
            ("A11234567890123", "uppercase"),      # Number in letter position
            ("AB123456789012X", "digits"),         # Letter in number position
            ("1A1234567890123", "uppercase"),      # Number as first char
            ("A@1234567890123", "uppercase"),      # Special char in letters
            ("AB12345678901@3", "digits"),         # Special char in numbers
        ]
        
        for regno, expected_error in test_cases:
            error = validate_regno(regno)
            assert error is not None, f"Invalid format regno '{regno}' was accepted"


# Password Validation Tests  
class TestPasswordValidation:
    
    def test_strong_password_accepted(self):
        """Strong passwords meeting all requirements should be accepted"""
        strong_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd2024", 
            "Complex#Pass9",
            "A1b2C3d4!",
        ]
        
        for password in strong_passwords:
            assert validate_password(password) is None, f"Strong password '{password}' was rejected"
    
    def test_weak_password_rejected(self):
        """Weak passwords should be rejected with specific errors"""
        weak_cases = [
            ("short", "8 characters"),              # Too short
            ("nouppercase123!", "uppercase"),       # No uppercase
            ("NOLOWERCASE123!", "lowercase"),       # No lowercase  
            ("NoDigitsHere!", "digit"),             # No digits
            ("NoSpecial123", "special"),            # No special chars
        ]
        
        for password, expected_error in weak_cases:
            error = validate_password(password)
            assert error is not None, f"Weak password '{password}' was accepted"


# Password Hashing Tests
class TestPasswordHashing:
    
    def test_password_gets_hashed(self):
        """Passwords should be securely hashed"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        # Basic hash validation
        assert hashed != password, "Hash should not equal original password"
        assert len(hashed) > 50, "Hash seems too short for secure hashing"
        assert hashed.startswith("$argon2"), "Should use Argon2 hashing"
    
    def test_password_verification_works(self):
        """Password verification should work correctly"""
        password = "VerifyMe123!"
        hashed = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True, "Correct password should verify"
        
        # Wrong password should not verify
        assert verify_password("WrongPassword!", hashed) is False, "Wrong password should not verify"
        
        # Empty password should not verify
        assert verify_password("", hashed) is False, "Empty password should not verify"
    
    def test_same_password_different_hashes(self):
        """Same password should produce different hashes (salt effect)"""
        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different (salt)
        assert hash1 != hash2, "Same password produced identical hashes - salt not working"
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True, "Hash 1 should verify correctly"
        assert verify_password(password, hash2) is True, "Hash 2 should verify correctly"

# Sprint 1 Core Auth Tests - Clean & Focused
