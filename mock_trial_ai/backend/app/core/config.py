from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Simplified Mock Trial App"
    VERSION: str = "0.1.0"

settings = Settings()