from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application-wide settings and environment variables.
    """
    PROJECT_NAME: str = "Horizon API"
    API_V1_STR: str = "/api/v1"

    model_config = {"env_file": ".env"}

settings = Settings()
