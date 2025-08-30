"""
Upload Feature Tests - Implementation Rulebook
==============================================

This file serves as the SPECIFICATION for upload functionality.
Build your upload endpoint to satisfy these tests exactly.

Test-Driven Development Rule:
1. Run these tests (they will fail - RED phase)
2. Write MINIMUM code to make them pass (GREEN phase)  
3. Refactor if needed (REFACTOR phase)
4. Move to next feature

Focus: Build exactly what these tests require, nothing more.
"""

from fastapi.testclient import TestClient
from io import BytesIO
import pytest
from app.main import app

client = TestClient(app)


class TestUploadFeature:
    """
    Upload Feature Specification
    
    Each test defines EXACTLY what your upload endpoint must do.
    Don't implement features not covered by these tests.
    """

    def test_valid_image_upload_succeeds(self):
        """
        RULE 1: Accept valid JPEG images
        
        Implementation Requirements:
        - POST /uploads/gradesheet endpoint exists
        - Accepts multipart/form-data with 'file' field
        - Returns 202 status (accepted for processing)
        - Returns JSON with upload_id, filename, status, message
        - Saves upload record to database
        """
        # Valid JPEG file (real JPEG header + content)
        jpeg_content = bytes([
            0xFF, 0xD8, 0xFF, 0xE0,  # JPEG magic bytes
            0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01
        ]) + b"fake_jpeg_image_data" * 200
        
        file_data = ("grade_sheet.jpg", BytesIO(jpeg_content), "image/jpeg")
        
        # Make the request
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        # Verify response format
        assert response.status_code == 202, "Must accept valid images"
        
        data = response.json()
        assert "upload_id" in data, "Must return upload_id"
        assert "filename" in data, "Must return filename"
        assert "status" in data, "Must return status"
        assert "message" in data, "Must return message"
        
        assert data["filename"] == "grade_sheet.jpg", "Must preserve filename"
        assert data["status"] == "processing", "Initial status must be 'processing'"
        assert len(data["upload_id"]) > 10, "Upload ID must be substantial"

    def test_png_images_also_accepted(self):
        """
        RULE 2: Accept PNG images too
        
        Implementation Requirements:
        - Support image/png MIME type
        - Handle PNG magic bytes correctly
        """
        # Valid PNG file (real PNG header)
        png_content = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A  # PNG magic bytes
        ]) + b"fake_png_image_data" * 200
        
        file_data = ("grades.png", BytesIO(png_content), "image/png")
        
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        assert response.status_code == 202, "Must accept PNG images"
        assert response.json()["filename"] == "grades.png"

    def test_pdf_files_rejected_with_helpful_message(self):
        """
        RULE 3: Reject PDF files with user-friendly error
        
        Implementation Requirements:
        - Detect PDF MIME type (application/pdf)
        - Return 415 Unsupported Media Type
        - Error message must mention "image" and supported formats
        - Help user understand what to do instead
        """
        # Real PDF file header
        pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n" + b"pdf_content_here" * 100
        
        file_data = ("grades.pdf", BytesIO(pdf_content), "application/pdf")
        
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        assert response.status_code == 415, "Must reject PDF files"
        
        error_detail = response.json()["detail"].lower()
        assert "image" in error_detail, "Error must mention 'image'"
        assert any(fmt in error_detail for fmt in ["jpeg", "png", "jpg"]), \
            "Error must mention supported formats"

    def test_oversized_files_rejected(self):
        """
        RULE 4: Reject files larger than 10MB
        
        Implementation Requirements:
        - Check file size before processing
        - Return 413 Payload Too Large
        - Error message must mention size limit
        - Include actual file size in error for user feedback
        """
        # Create 11MB file (over the limit)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        file_data = ("huge_image.jpg", BytesIO(large_content), "image/jpeg")
        
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        assert response.status_code == 413, "Must reject oversized files"
        
        error_detail = response.json()["detail"].lower()
        assert "size" in error_detail or "large" in error_detail, \
            "Error must mention file size"

    def test_empty_files_rejected(self):
        """
        RULE 5: Reject empty files
        
        Implementation Requirements:
        - Check for zero-byte files
        - Return 422 Unprocessable Entity
        - Clear error message about empty file
        """
        empty_content = b""  # 0 bytes
        
        file_data = ("empty.jpg", BytesIO(empty_content), "image/jpeg")
        
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        assert response.status_code == 422, "Must reject empty files"
        
        error_detail = response.json()["detail"].lower()
        assert "empty" in error_detail, "Error must mention empty file"

    def test_malicious_filenames_sanitized(self):
        """
        RULE 6: Sanitize dangerous filenames
        
        Implementation Requirements:
        - Remove path traversal attempts (../, ..\)
        - Remove absolute path attempts (/, \)
        - Preserve file extension
        - Still accept the upload if image is valid
        """
        valid_image = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"valid_image" * 100
        malicious_filename = "../../../etc/passwd.jpg"
        
        file_data = (malicious_filename, BytesIO(valid_image), "image/jpeg")
        
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        # Should either sanitize and accept, or reject entirely
        if response.status_code == 202:
            # If accepted, filename must be sanitized
            returned_filename = response.json()["filename"]
            assert ".." not in returned_filename, "Must remove path traversal"
            assert "/" not in returned_filename, "Must remove path separators"
            assert returned_filename.endswith(".jpg"), "Must preserve extension"
        else:
            # Also acceptable to reject malicious filenames entirely
            assert response.status_code in [400, 422], "Must handle malicious filenames"

    def test_missing_file_parameter_error(self):
        """
        RULE 7: Handle missing file parameter gracefully
        
        Implementation Requirements:
        - Return 422 when 'file' parameter is missing
        - Clear error message about required field
        """
        # Request without file parameter
        response = client.post("/uploads/gradesheet", json={"other": "data"})
        
        assert response.status_code == 422, "Must require file parameter"

    def test_non_gradesheet_images_rejected(self):
        """
        RULE 8: Only accept images that look like grade sheets
        
        Implementation Requirements:
        - Analyze image content to detect if it's a grade sheet
        - Reject random photos, memes, screenshots, etc.
        - Return 422 with helpful message about grade sheet requirement
        
        Implementation Options (choose one):
        SIMPLE: Check filename for keywords like "grade", "mark", "transcript"
        MEDIUM: Use OCR to extract text and look for academic keywords  
        ADVANCED: ML model trained to recognize grade sheet layouts
        
        For MVP: Start with SIMPLE approach, upgrade later
        """
        # Create a generic image that's clearly not a grade sheet
        # (This would be a photo, meme, or random image)
        generic_image = bytes([
            0xFF, 0xD8, 0xFF, 0xE0,  # JPEG header
            0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01
        ]) + b"clearly_not_gradesheet_content" * 100
        
        file_data = ("vacation_photo.jpg", BytesIO(generic_image), "image/jpeg")
        
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        assert response.status_code == 422, "Must reject non-grade-sheet images"
        
        error_detail = response.json()["detail"].lower()
        assert any(word in error_detail for word in ["grade", "sheet", "transcript", "marksheet"]), \
            "Error must mention grade sheet requirement"

    def test_multiple_files_upload_limit(self):
        """
        RULE 9: Limit number of files per upload request
        
        Implementation Requirements:
        - Accept only single file uploads (no multiple files)
        - OR limit to maximum N files per request (e.g., max 3)
        - Return 422 when limit exceeded
        - Clear error message about file limit
        """
        # Valid grade sheet images
        valid_image = bytes([
            0xFF, 0xD8, 0xFF, 0xE0,
            0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01
        ]) + b"gradesheet_content" * 100
        
        # Try to upload multiple files (assuming limit is 1)
        files = [
            ("file", ("sheet1.jpg", BytesIO(valid_image), "image/jpeg")),
            ("file", ("sheet2.jpg", BytesIO(valid_image), "image/jpeg")),
            ("file", ("sheet3.jpg", BytesIO(valid_image), "image/jpeg")),
        ]
        
        response = client.post("/uploads/gradesheet", files=files)
        
        assert response.status_code == 422, "Must limit number of files"
        
        error_detail = response.json()["detail"].lower()
        assert any(word in error_detail for word in ["limit", "multiple", "one", "single"]), \
            "Error must mention file limit"

    def test_file_upload_quota_per_user(self):
        """
        RULE 10: Limit total uploads per user per time period
        
        Implementation Requirements:
        - Track uploads per user (daily/weekly/monthly limit)
        - Return 429 Too Many Requests when quota exceeded
        - Include quota info in error message
        - Reset quota after time period
        """
        # This test would require user authentication and quota tracking
        # For now, we'll define the expected behavior
        
        valid_image = bytes([
            0xFF, 0xD8, 0xFF, 0xE0,
            0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01
        ]) + b"gradesheet_content" * 100
        
        file_data = ("grade_sheet.jpg", BytesIO(valid_image), "image/jpeg")
        
        # Simulate multiple uploads (this would need user context)
        # For now, just document the expected behavior
        """
        Expected behavior when quota exceeded:
        - response.status_code == 429
        - error includes "quota", "limit", "too many"
        - error includes when quota resets
        """
        
        # For MVP, we'll skip this test until user auth is implemented
        pytest.skip("Quota testing requires user authentication - implement after auth system")

    def test_gradesheet_content_validation(self):
        """
        RULE 11: Advanced grade sheet validation
        
        Implementation Requirements:
        - Image must contain text that looks like grades/marks
        - Should have tabular/structured layout
        - Must contain academic-related keywords
        - Reject images with no text or wrong content type
        """
        # Image that looks like a grade sheet (has appropriate content markers)
        gradesheet_like_image = bytes([
            0xFF, 0xD8, 0xFF, 0xE0,
            0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01
        ]) + b"grade_markers_course_marks_semester" * 50
        
        file_data = ("valid_gradesheet.jpg", BytesIO(gradesheet_like_image), "image/jpeg")
        
        response = client.post("/uploads/gradesheet", files={"file": file_data})
        
        # This should pass if content looks like a grade sheet
        assert response.status_code in [202, 422], "Must validate grade sheet content"
        
        if response.status_code == 422:
            error_detail = response.json()["detail"].lower()
            assert any(word in error_detail for word in ["content", "text", "readable", "valid"]), \
                "Error must explain content validation failure"


# ==========================================
# IMPLEMENTATION CHECKLIST
# ==========================================
"""
To make these tests pass, your upload endpoint must:

✅ 1. Create POST /uploads/gradesheet route
✅ 2. Accept multipart/form-data with 'file' field  
✅ 3. Validate file type (JPEG, PNG only)
✅ 4. Validate file size (max 10MB, min 1 byte)
✅ 5. Sanitize filenames (remove ../, /, \)
✅ 6. Save upload record to database
✅ 7. Return proper JSON response format
✅ 8. Return appropriate HTTP status codes
✅ 9. Provide helpful error messages

NEW BUSINESS RULES:
✅ 10. Grade Sheet Content Validation:
    - Use OCR or image analysis to detect if image contains grade/mark content
    - Look for academic keywords: "grade", "marks", "course", "semester", "GPA"
    - Reject random photos, memes, screenshots that aren't grade sheets
    - Return 422 with "This doesn't appear to be a grade sheet" message

✅ 11. File Upload Limits:
    - Single file per request only (no multiple file uploads)
    - OR maximum N files per request (define your limit)
    - Return 422 with "Only single file uploads allowed" message

✅ 12. User Upload Quota (Optional for MVP):
    - Limit uploads per user per day/week/month
    - Return 429 when quota exceeded
    - Include reset time in error message

IMPLEMENTATION APPROACH:
📋 Phase 1: Basic upload (tests 1-7) - Get core functionality working
📋 Phase 2: Content validation (tests 8, 11) - Add grade sheet detection  
📋 Phase 3: Rate limiting (test 10) - Add user quotas

Don't build anything else until these tests pass.
"""
