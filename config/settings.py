"""
SAP BW Process Chain Chatbot - Application Configuration

This module contains application settings and configuration management.
"""

import os
from pathlib import Path
from typing import Optional

class AppConfig:
    """Application configuration settings"""
    
    # Application Info
    APP_NAME = "SAP BW Process Chain Assistant"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Local chatbot for SAP BW process chain management"
    
    # Database Configuration (SQLite)
    DATABASE_PATH = os.getenv("DATABASE_PATH", "sap_bw_demo.db")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "sap_bw_demo")  # For compatibility
    # Legacy PostgreSQL settings (kept for compatibility)
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", "0"))
    DATABASE_USER = os.getenv("DATABASE_USER", "sqlite")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "1"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "0"))
    
    # AI Model Configuration
    AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "t5-small")
    AI_MODEL_CACHE_DIR = os.getenv("AI_MODEL_CACHE_DIR", "./models")
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "512"))
    AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.1"))
    
    # Groq API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192")
    GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "8192"))
    GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
    
    # Application Settings
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
    DEBUG = APP_DEBUG  # Alias for backward compatibility
    APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")
    APP_SESSION_TIMEOUT = int(os.getenv("APP_SESSION_TIMEOUT", "1800"))
    APP_MAX_QUERY_RESULTS = int(os.getenv("APP_MAX_QUERY_RESULTS", "1000"))
    
    # UI Configuration
    STREAMLIT_THEME = os.getenv("STREAMLIT_THEME", "dark")
    STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")
    
    # Logging Configuration
    LOG_FILE = os.getenv("LOG_FILE", "./logs/chatbot.log")
    LOG_ROTATION = os.getenv("LOG_ROTATION", "daily")
    LOG_RETENTION = int(os.getenv("LOG_RETENTION", "30"))
    
    # Project Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATABASE_DIR = PROJECT_ROOT / "database"
    MODELS_DIR = PROJECT_ROOT / "models"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.MODELS_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get SQLite connection URL"""
        return f"sqlite:///{cls.DATABASE_PATH}"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.APP_DEBUG
    
    @classmethod
    def get_log_config(cls) -> dict:
        """Get logging configuration"""
        return {
            "level": cls.APP_LOG_LEVEL,
            "file": cls.LOG_FILE,
            "rotation": cls.LOG_ROTATION,
            "retention": cls.LOG_RETENTION
        }

# Initialize directories on import
AppConfig.ensure_directories() 