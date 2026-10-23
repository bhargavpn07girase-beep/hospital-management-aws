import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-hospital-insecure-key-change-me")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    PORT = int(os.getenv("PORT", 5000))
    
    # Database configuration
    DATABASE_PATH = BASE_DIR / "hospital.db"
    BACKUP_DIR = BASE_DIR / "backups"
    
    # AWS S3 Configuration
    AWS_REGION = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "ap-south-1"))
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "hospital-backups-123")
    S3_BACKUP_PREFIX = os.getenv("S3_BACKUP_PREFIX", "backups/")
    
    # Optional direct credentials (empty string defaults to IAM Role / default credential chain)
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

# Ensure essential directories exist
Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
