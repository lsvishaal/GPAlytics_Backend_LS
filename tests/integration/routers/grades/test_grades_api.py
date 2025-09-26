"""Integration tests for grade management API endpoints"""
from httpx import AsyncClient
import io
from PIL import Image


class TestGradeUpload:
    """Test grade sheet upload functionality"""
    
    async def test_upload_grade_sheet_success(self, client: AsyncClient, auth_headers):
        """Test successful grade sheet upload"""
        # Create a test image
        img = Image.new('RGB', (800, 600), color='white')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        files = {"file": ("test_grade_sheet.jpg", img_buffer, "image/jpeg")}
        
        response = await client.post(
            "/grades/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert data["status"] in ["processing", "completed"]
    
    async def test_upload_invalid_file_fails(self, client: AsyncClient, auth_headers):
        """Test upload fails with invalid file type"""
        files = {"file": ("test.txt", io.StringIO("not an image"), "text/plain")}
        
        response = await client.post(
            "/grades/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    async def test_upload_without_auth_fails(self, client: AsyncClient):
        """Test upload fails without authentication"""
        img = Image.new('RGB', (100, 100), color='white')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        files = {"file": ("test.jpg", img_buffer, "image/jpeg")}
        
        response = await client.post("/grades/upload", files=files)
        
        assert response.status_code == 401


class TestGradeHistory:
    """Test grade history endpoints"""
    
    async def test_get_grade_history_success(self, client: AsyncClient, auth_headers):
        """Test getting user's grade history"""
        response = await client.get("/grades/history", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return empty list for new user or list of grade records
    
    async def test_get_grade_by_id_success(self, client: AsyncClient, auth_headers, test_grade):
        """Test getting specific grade by ID"""
        response = await client.get(f"/grades/{test_grade.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_grade.id
        assert data["subject"] == test_grade.subject
    
    async def test_get_nonexistent_grade_fails(self, client: AsyncClient, auth_headers):
        """Test getting non-existent grade returns 404"""
        response = await client.get("/grades/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Grade not found" in response.json()["detail"]
