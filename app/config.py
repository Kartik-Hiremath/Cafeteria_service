from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # IBM SSO Configuration
    ibm_client_id: str
    ibm_client_secret: str
    ibm_redirect_uri: str
    ibm_discovery_url: str
    
    # Application Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore

# Made with Bob
