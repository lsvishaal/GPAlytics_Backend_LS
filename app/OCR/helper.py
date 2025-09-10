"""
AI helper functions for grade extraction using Gemini Vision
Pure business logic - no FastAPI dependencies
"""
import google.generativeai as genai
from PIL import Image, ImageEnhance
import io
import logging
import json
from typing import Dict, Any

from ..constants import ALLOWED_FILE_TYPES, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

# ==========================================
# FILE VALIDATION
# ==========================================

def validate_file_type(content_type: str) -> bool:
    """Check if file type is allowed"""
    return content_type in ALLOWED_FILE_TYPES

def validate_file_size(file_size: int) -> bool:
    """Check if file size is within limits"""
    return file_size <= MAX_FILE_SIZE

def get_allowed_file_types() -> list[str]:
    """Get list of allowed file types"""
    return ALLOWED_FILE_TYPES

# ==========================================
# GEMINI CONFIGURATION
# ==========================================

def configure_gemini(api_key: str) -> None:
    """Configure Gemini AI with API key"""
    genai.configure(api_key=api_key)
    logger.info("Gemini AI configured successfully")

# ==========================================
# IMAGE PROCESSING
# ==========================================

def sharpen_image(image_bytes: bytes) -> bytes:
    """
    Sharpen image for better AI processing
    Enhances contrast and sharpness for better text recognition
    """
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        sharpened = enhancer.enhance(2.0)  # Increase sharpness
        
        # Enhance contrast
        contrast_enhancer = ImageEnhance.Contrast(sharpened)
        enhanced = contrast_enhancer.enhance(1.5)  # Increase contrast
        
        # Convert back to bytes
        output_buffer = io.BytesIO()
        enhanced.save(output_buffer, format='JPEG', quality=95)
        output_buffer.seek(0)
        
        logger.info("Image sharpened successfully")
        return output_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Image sharpening failed: {str(e)}")
        # Return original if sharpening fails
        return image_bytes

# ==========================================
# RESPONSE CLEANING
# ==========================================

def clean_ai_response(response_text: str) -> str:
    """
    Clean AI response text to extract valid JSON
    Handles common issues like markdown formatting, extra text, etc.
    """
    # Remove markdown code blocks
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
    
    # Remove common prefixes
    prefixes_to_remove = [
        "Here's the extracted data:",
        "Here is the extracted information:",
        "The extracted data is:",
        "Based on the image, here's the data:",
    ]
    
    for prefix in prefixes_to_remove:
        if response_text.startswith(prefix):
            response_text = response_text[len(prefix):].strip()
    
    # Find JSON object boundaries
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        response_text = response_text[start_idx:end_idx+1]
    
    return response_text.strip()

# ==========================================
# GEMINI VISION PROCESSING
# ==========================================

async def process_result_card(image_bytes: bytes) -> Dict[str, Any]:
    """
    Process result card image using Gemini Vision API
    Returns structured grade data
    """
    response_text = ""  # Initialize for error handling
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Convert bytes to PIL Image for Gemini
        image = Image.open(io.BytesIO(image_bytes))
        
        # Create a more explicit prompt for JSON output
        prompt = """
        You are a data extraction expert. Analyze this grade/result card image and extract ONLY a valid JSON object with this exact structure:

        {
            "student_info": {
                "name": "student name or null",
                "registration_number": "reg number or null", 
                "semester": "semester number or null"
            },
            "subjects": [
                {
                    "subject_code": "course code",
                    "subject_name": "full course name",
                    "credits": 3,
                    "grade": "A+",
                    "grade_points": 9.0
                }
            ],
            "semester_summary": {
                "total_credits": 20,
                "sgpa": 8.5,
                "cgpa": 8.2
            }
        }

        CRITICAL INSTRUCTIONS:
        1. Return ONLY the JSON object, no explanations or markdown
        2. Use null for missing information
        3. Calculate grade_points: O=10, A+=9, A=8, B+=7, B=6, C=5, D=4, F=0
        4. Ensure all numbers are numeric (not strings)
        5. Start your response with { and end with }
        """
        
        # Generate content with image
        response = model.generate_content([prompt, image])
        
        # Get response text and clean it
        response_text = response.text.strip()
        logger.info(f"Raw Gemini response: {response_text[:200]}...")  # Log first 200 chars
        
        # Clean up common AI response issues
        response_text = clean_ai_response(response_text)
        
        # Parse JSON response
        extracted_data = json.loads(response_text)
        
        logger.info(f"Successfully extracted data for {len(extracted_data.get('subjects', []))} subjects")
        return extracted_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
        logger.error(f"Raw response was: {response_text}")
        
        # Try to create a fallback response for debugging
        fallback_response = {
            "student_info": {"name": None, "registration_number": None, "semester": None},
            "subjects": [],
            "semester_summary": {"total_credits": 0, "sgpa": None, "cgpa": None},
            "error": "JSON parsing failed",
            "raw_response": response_text[:500]
        }
        return fallback_response
        
    except Exception as e:
        logger.error(f"Gemini Vision processing failed: {str(e)}")
        raise ValueError(f"Failed to process result card: {str(e)}")

# ==========================================
# DATA VALIDATION
# ==========================================

def validate_extracted_grades(data: Dict[str, Any]) -> bool:
    """
    Validate extracted grade data structure
    Returns True if data is valid, False otherwise
    """
    try:
        # Check required top-level keys
        required_keys = ["student_info", "subjects", "semester_summary"]
        if not all(key in data for key in required_keys):
            return False
        
        # Validate subjects array
        subjects = data.get("subjects", [])
        if not isinstance(subjects, list) or len(subjects) == 0:
            return False
        
        # Validate each subject
        for subject in subjects:
            required_subject_keys = ["subject_code", "subject_name", "credits", "grade"]
            if not all(key in subject for key in required_subject_keys):
                return False
            
            # Validate data types
            if not isinstance(subject.get("credits"), (int, float)):
                return False
        
        logger.info("Grade data validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Grade data validation failed: {str(e)}")
        return False