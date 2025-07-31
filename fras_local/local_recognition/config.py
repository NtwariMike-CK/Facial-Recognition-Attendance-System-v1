# local_recognition/config.py
import os
from typing import Optional

class Config:
    """Configuration settings for local recognition system"""
    
    def __init__(self):
        # API Configuration - Update these with your deployed backend URL
        self.API_BASE_URL = os.getenv("FRAS_API_URL", "https://facial-recognition-attendance-system-mj5y.onrender.com/api")
        
        # Ensure API_BASE_URL doesn't end with /api/api
        if self.API_BASE_URL.endswith('/api'):
            self.API_BASE_URL = self.API_BASE_URL.rstrip('/api')
        if not self.API_BASE_URL.endswith('/api'):
            self.API_BASE_URL = f"{self.API_BASE_URL.rstrip('/')}/api"
        
        # Local Camera Configuration
        self.DEFAULT_CAMERA_SOURCE = 0  # Default webcam
        self.CAMERA_WIDTH = 1280
        self.CAMERA_HEIGHT = 720
        self.CAMERA_FPS = 30
        
        # Recognition Configuration
        self.FACE_RECOGNITION_TOLERANCE = 0.6
        self.FACE_DETECTION_MODEL = "hog"  # or "cnn" for better accuracy but slower
        self.SCALE_FACTOR = 0.25  # Scale down for faster processing
        
        # Blink Detection Configuration
        self.EYE_AR_THRESHOLD = 0.25
        self.BLINK_FRAME_THRESHOLD = 3
        self.DEFAULT_BLINK_THRESHOLD = 5
        
        # Attendance Configuration
        self.CHECKOUT_DELAY_MINUTES = 2
        
        # Display Configuration
        self.DISPLAY_CONFIDENCE_THRESHOLD = 0.4
        self.PREVIEW_WIDTH = 800
        self.PREVIEW_HEIGHT = 600
        
        # File Paths
        self.FACE_LANDMARKS_MODEL = "shape_predictor_68_face_landmarks.dat"
        
        # Logging
        self.LOG_LEVEL = "INFO"
    
    def get_api_url(self, endpoint: str) -> str:
        """Get full API URL for an endpoint"""
        return f"{self.API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def validate_config(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        if not self.API_BASE_URL:
            issues.append("API_BASE_URL is not set")
        
        if not os.path.exists(self.FACE_LANDMARKS_MODEL):
            issues.append(f"Face landmarks model not found at {self.FACE_LANDMARKS_MODEL}")
            issues.append("Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        
        return issues

# Environment-specific configurations
class DevelopmentConfig(Config):
    def __init__(self):
        super().__init__()
        self.API_BASE_URL = "http://localhost:8000/api"
        self.LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    def __init__(self):
        super().__init__()
        # Update with your actual deployed URL
        api_url = os.getenv("FRAS_API_URL", "https://your-deployed-backend.com")
        if not api_url.endswith('/api'):
            api_url = f"{api_url.rstrip('/')}/api"
        self.API_BASE_URL = api_url

# Factory function to get appropriate config
def get_config(env: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    env = env or os.getenv("FRAS_ENV", "development")
    
    if env.lower() == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()