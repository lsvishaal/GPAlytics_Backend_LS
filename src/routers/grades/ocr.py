"""OCR Service for Grade Extraction (feature-based)
Moved from app/features/grades/ocr.py with adjusted imports
"""
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from PIL import Image, ImageEnhance
import io
import logging
import json
from typing import Dict, Any

from ...shared.constants import ALLOWED_FILE_TYPES, MAX_FILE_SIZE
from ...shared.config import settings
from ...shared.exceptions import OCRProcessingError

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        if not GEMINI_AVAILABLE:
            logger.error("Google Generative AI package not available")
            return
        if settings.gemini_key_str:
            # Use getattr to avoid static attribute errors when type checking
            configure = getattr(genai, "configure", None)
            if callable(configure):
                configure(api_key=settings.gemini_key_str)
            logger.info("Gemini AI configured successfully")
        else:
            logger.warning("Gemini API key not configured")

    @staticmethod
    def validate_file_type(content_type: str) -> bool:
        return content_type in ALLOWED_FILE_TYPES

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        return file_size <= MAX_FILE_SIZE

    @staticmethod
    def get_allowed_file_types() -> list[str]:
        return ALLOWED_FILE_TYPES

    def sharpen_image(self, image_bytes: bytes) -> bytes:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            enhancer = ImageEnhance.Sharpness(image)
            sharpened = enhancer.enhance(2.0)
            contrast_enhancer = ImageEnhance.Contrast(sharpened)
            enhanced = contrast_enhancer.enhance(1.5)
            output_buffer = io.BytesIO()
            enhanced.save(output_buffer, format="JPEG", quality=95)
            output_buffer.seek(0)
            logger.info("Image sharpened successfully")
            return output_buffer.getvalue()
        except Exception as e:
            logger.error(f"Image sharpening failed: {str(e)}")
            return image_bytes

    def clean_ai_response(self, response_text: str) -> str:
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        prefixes_to_remove = [
            "Here's the extracted data:",
            "Here is the extracted information:",
            "The extracted data is:",
            "Based on the image, here's the data:",
        ]
        for prefix in prefixes_to_remove:
            if response_text.startswith(prefix):
                response_text = response_text[len(prefix) :].strip()
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx : end_idx + 1]
        return response_text.strip()

    async def process_result_card(self, image_bytes: bytes) -> Dict[str, Any]:
        if not GEMINI_AVAILABLE or not genai:
            raise OCRProcessingError("Gemini AI service unavailable - AI processing not configured")
        if not settings.gemini_key_str:
            raise OCRProcessingError("Gemini API key not configured - contact administrator")
        response_text = ""
        try:
            GenerativeModel = getattr(genai, "GenerativeModel", None)
            if GenerativeModel is None:
                raise OCRProcessingError("Gemini SDK incompatible: GenerativeModel not found")
            model = GenerativeModel("gemini-1.5-flash")
            image = Image.open(io.BytesIO(image_bytes))
            prompt = (
                "You are a data extraction expert. Analyze this grade/result card image and extract ONLY a "
                "valid JSON object with the exact required structure. Return only JSON."
            )
            response = model.generate_content([prompt, image])
            response_text = response.text.strip()
            logger.info(f"Raw Gemini response: {response_text[:200]}...")
            response_text = self.clean_ai_response(response_text)
            extracted_data = json.loads(response_text)
            logger.info(
                f"Successfully extracted data for {len(extracted_data.get('subjects', []))} subjects"
            )
            return extracted_data
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini response as JSON")
            logger.error(f"Raw response was: {response_text}")
            raise OCRProcessingError(
                "AI response parsing failed - the image may not contain clear grade information"
            )
        except Exception as e:
            error_message = str(e).lower()
            if "quota" in error_message or "rate limit" in error_message:
                logger.error(f"Gemini rate limit exceeded: {str(e)}")
                raise OCRProcessingError(
                    "AI service temporarily unavailable due to rate limits - please try again in a few minutes"
                )
            elif "invalid api key" in error_message or "authentication" in error_message:
                logger.error(f"Gemini authentication failed: {str(e)}")
                raise OCRProcessingError("AI service authentication failed - contact administrator")
            elif "network" in error_message or "connection" in error_message:
                logger.error(f"Network error calling Gemini: {str(e)}")
                raise OCRProcessingError("Network error accessing AI service - please check your connection and try again")
            else:
                logger.error(f"Unexpected Gemini error: {str(e)}")
                raise OCRProcessingError(f"AI processing failed: {str(e)}")

    def validate_extracted_grades(self, data: Dict[str, Any]) -> bool:
        try:
            required_keys = ["student_info", "subjects", "semester_summary"]
            if not all(key in data for key in required_keys):
                return False
            subjects = data.get("subjects", [])
            if not isinstance(subjects, list) or len(subjects) == 0:
                return False
            for subject in subjects:
                required_subject_keys = ["subject_code", "subject_name", "credits", "grade"]
                if not all(key in subject for key in required_subject_keys):
                    return False
                if not isinstance(subject.get("credits"), (int, float)):
                    return False
            logger.info("Grade data validation passed")
            return True
        except Exception as e:
            logger.error(f"Grade data validation failed: {str(e)}")
            return False


ocr_service = OCRService()
