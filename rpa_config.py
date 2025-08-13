"""
Configuration settings for the Multimodal RPA Generator
"""

import os
from typing import Dict, Any

class RpaConfig:
    """Configuration class for RPA generation settings"""
    
    # API Settings
    GEMINI_MODEL = "gemini-1.5-flash"
    MAX_FILE_SIZE_MB = 20
    API_TIMEOUT = 300  # 5 minutes
    
    # Video Processing Settings
    VIDEO_FPS = 1.0  # Frames per second for analysis
    
    # Generation Settings
    TEMPERATURE = 0.2
    TOP_K = 1
    TOP_P = 0.9
    MAX_OUTPUT_TOKENS = 4000
    
    # File Paths
    RECORDS_DIR = "records"
    OUTPUT_DIR = "generated_rpa_commands"
    
    # Processing Limits
    MAX_SESSIONS_PER_BATCH = 5
    INTERACTION_GAP_THRESHOLD = 2.0  # seconds
    
    @classmethod
    def get_generation_config(cls) -> Dict[str, Any]:
        """Get Gemini generation configuration"""
        return {
            "temperature": cls.TEMPERATURE,
            "topK": cls.TOP_K,
            "topP": cls.TOP_P,
            "maxOutputTokens": cls.MAX_OUTPUT_TOKENS,
            "responseMimeType": "text/plain"
        }
    
    @classmethod
    def get_video_metadata(cls) -> Dict[str, Any]:
        """Get video processing metadata"""
        return {
            "fps": cls.VIDEO_FPS
        }
    
    @classmethod
    def ensure_output_dir(cls) -> str:
        """Ensure output directory exists and return path"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        return cls.OUTPUT_DIR