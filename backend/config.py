"""
Configuration settings for PyMorph AI application.
Created By: Prabu Arvind M
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Load environment variables from backend/.env or root .env
dotenv_path = BACKEND_DIR / ".env"
if not dotenv_path.exists():
    dotenv_path = BASE_DIR / ".env"

load_dotenv(dotenv_path=dotenv_path)

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
        GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "auto")
        HOST: str = os.getenv("HOST", "0.0.0.0")
        PORT: int = int(os.getenv("PORT", "8000"))
        MAX_EXECUTION_TIMEOUT: int = int(os.getenv("MAX_EXECUTION_TIMEOUT", "5"))
        UPLOADS_DIR: Path = BASE_DIR / "uploads"
        OUTPUTS_DIR: Path = BASE_DIR / "outputs"

        class Config:
            env_file = str(dotenv_path)
            extra = "ignore"

    settings = Settings()

except ImportError:
    # Lightweight fallback if pydantic-settings is not installed
    class Settings:
        GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
        GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "auto")
        HOST: str = os.getenv("HOST", "0.0.0.0")
        PORT: int = int(os.getenv("PORT", "8000"))
        MAX_EXECUTION_TIMEOUT: int = int(os.getenv("MAX_EXECUTION_TIMEOUT", "5"))
        UPLOADS_DIR: Path = BASE_DIR / "uploads"
        OUTPUTS_DIR: Path = BASE_DIR / "outputs"

    settings = Settings()

# Ensure required directories exist
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
