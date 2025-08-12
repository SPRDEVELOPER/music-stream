import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Required Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    SESSION_STRING = os.getenv("SESSION_STRING")
    
    # Optional Configuration
    LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", 0)) if os.getenv("LOG_CHAT_ID") else None
    OWNER_ID = int(os.getenv("OWNER_ID", 0)) if os.getenv("OWNER_ID") else None
    SUDO_USERS = [int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.strip().isdigit()]
    
    # Database Configuration
    MONGO_URI = os.getenv("MONGO_URI")
    
    # Bot Settings
    MAX_DURATION = 3600  # 1 hour max duration
    QUEUE_LIMIT = 50     # Max 50 songs in queue
    
    # Audio/Video Quality
    AUDIO_BITRATE = 512
    VIDEO_BITRATE = 1000
    
    # Supported Platforms
    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.wav', '.flac', '.m4a', '.webm', '.mkv']
    SUPPORTED_SOURCES = ['youtube', 'soundcloud', 'spotify']
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_fields = ["BOT_TOKEN", "API_ID", "API_HASH", "SESSION_STRING"]
        missing_fields = []
        
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True