"""
Core Configuration Management
Centralized settings for GPAlytics application
"""
from pydantic import BaseModel, Field, SecretStr
import secrets
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings with environment variable support"""
    
    # Database Configuration
    database_url: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("DATABASE_URL", "")))
    
    # JWT Configuration  
    jwt_secret_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))))
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    use_secure_cookies: bool = os.getenv("USE_SECURE_COOKIES", "true").lower() == "true"
    
    # Gemini AI Configuration
    gemini_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("GEMINI_KEY", "")))
    
    # Application Configuration
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "production")
    
    # Computed Properties
    @property
    def database_url_str(self) -> str:
        """Get database URL as string"""
        return self.database_url.get_secret_value()
    
    @property 
    def jwt_secret_str(self) -> str:
        """Get JWT secret as string"""
        return self.jwt_secret_key.get_secret_value()
    
    @property
    def gemini_key_str(self) -> str:
        """Get Gemini API key as string"""
        return self.gemini_key.get_secret_value()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
