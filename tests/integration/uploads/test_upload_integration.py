"""
Sprint 2: File Upload & OCR Processing Tests
==========================================

Focus: Grade sheet upload, OCR extraction, AI cleanup
Goal: Core business value - automated grade processing
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGradeSheetUpload:
    """Core feature: Upload and process grade sheets"""
    
    def test_upload_grade_sheet_image(self):
        """Test uploading a grade sheet image for OCR processing"""
        # Create test user and login
        register_response = client.post("/auth/register", json={
            "name": "Upload User",
            "regno": "UP1234567890123", 
            "password": "UploadPass123!",
            "batch": 2020
        })
        token = register_response.json()["token"]
        
        # Upload grade sheet (mock image file)
        test_image = b"fake_image_content_here"
        
        response = client.post(
            "/upload/grade-sheet",
            files={"file": ("grades.jpg", test_image, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "processing_id" in data
        assert "status" in data
        assert data["status"] == "processing"
    
    def test_upload_requires_authentication(self):
        """Test upload requires valid token"""
        test_image = b"fake_image_content_here"
        
        response = client.post(
            "/upload/grade-sheet",
            files={"file": ("grades.jpg", test_image, "image/jpeg")}
        )
        
        assert response.status_code == 401
    
    def test_invalid_file_type_rejected(self):
        """Test invalid file types are rejected"""
        # Login first
        token = self._get_test_token()
        
        # Try uploading text file
        response = client.post(
            "/upload/grade-sheet", 
            files={"file": ("grades.txt", b"text content", "text/plain")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "unsupported file type" in response.json()["detail"].lower()
    
    def test_get_processing_status(self):
        """Test checking processing status of uploaded file"""
        token = self._get_test_token()
        
        response = client.get(
            "/upload/status/some-processing-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should return processing status
        assert response.status_code in [200, 404]  # 404 if not found is ok
    
    def _get_test_token(self):
        """Helper: Get auth token for tests"""
        response = client.post("/auth/register", json={
            "name": "Test User",
            "regno": f"TU{hash('test') % 10000000000000:013d}",  # Random regno
            "password": "TestPass123!",
            "batch": 2020
        })
        return response.json()["token"]


class TestOCRProcessing:
    """Tests for OCR and AI processing pipeline"""
    
    def test_ocr_extraction_endpoint(self):
        """Test OCR text extraction from image"""
        token = self._get_test_token()
        
        # Mock image with grade sheet content
        test_image = b"mock_grade_sheet_image"
        
        response = client.post(
            "/ocr/extract",
            files={"file": ("grades.jpg", test_image, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "raw_text" in data
        assert "confidence" in data
    
    def test_gemini_cleanup_endpoint(self):
        """Test Gemini API grade data cleanup"""
        token = self._get_test_token()
        
        # Raw OCR text (messy)
        raw_text = """
        SEMESTER II RESULT
        Mathematics    A+
        Physics       O
        Chemistry     B+
        Total Credits: 22
        GPA: 8.5
        """
        
        response = client.post(
            "/ai/cleanup-grades",
            json={"raw_text": raw_text},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cleaned_data" in data
        assert "subjects" in data["cleaned_data"]
        assert "gpa" in data["cleaned_data"]
    
    def _get_test_token(self):
        """Helper: Get auth token"""
        response = client.post("/auth/register", json={
            "name": "OCR User",
            "regno": f"OC{hash('ocr') % 10000000000000:013d}",
            "password": "OCRPass123!",
            "batch": 2020
        })
        return response.json()["token"]


class TestGradeStorage:
    """Tests for storing processed grades in database"""
    
    def test_store_processed_grades(self):
        """Test storing cleaned grade data to database"""
        token = self._get_test_token()
        
        grade_data = {
            "semester": 2,
            "year": 2020,
            "subjects": {
                "Mathematics": "A+",
                "Physics": "O", 
                "Chemistry": "B+"
            },
            "gpa": 8.5,
            "credits": 22
        }
        
        response = client.post(
            "/grades/store",
            json=grade_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "grade_id" in data
        assert data["semester"] == 2
    
    def test_get_user_grades(self):
        """Test retrieving user's stored grades"""
        token = self._get_test_token()
        
        response = client.get(
            "/grades/my-grades",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "grades" in data
        assert isinstance(data["grades"], list)
    
    def _get_test_token(self):
        """Helper: Get auth token"""
        response = client.post("/auth/register", json={
            "name": "Storage User",
            "regno": f"ST{hash('storage') % 10000000000000:013d}",
            "password": "StoragePass123!",
            "batch": 2020
        })
        return response.json()["token"]


# Sprint 2 Focus: Get these tests passing!
# Build: /upload/grade-sheet, /ocr/extract, /ai/cleanup-grades, /grades/store
