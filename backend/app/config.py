"""Configuration centralisée."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # GLPI
    GLPI_URL: str = os.getenv("GLPI_URL", "http://localhost:8083/apirest.php")
    GLPI_USER: str = os.getenv("GLPI_USER", "glpi")
    GLPI_PASSWORD: str = os.getenv("GLPI_PASSWORD", "glpi")
    GLPI_APP_TOKEN: str = os.getenv("GLPI_APP_TOKEN", "")
    USE_MOCK: bool = os.getenv("USE_MOCK", "false").lower() == "true"
    
    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    MODEL_NAME: str = "mistral"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    class Config:
        env_file = ".env"

settings = Settings()