import logging
from dotenv import load_dotenv
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
logging.info(BASE_DIR)

class DbSettings(BaseSettings):
    user: str = Field(..., alias='DB_USER')
    password: str = Field(..., alias='DB_PASS')
    host: str = Field(..., alias='DB_HOST')
    port: int = Field(..., alias='DB_PORT')
    name: str = Field(..., alias='DB_NAME')
    echo: bool = Field(True, alias='DB_ECHO')
    future: bool = Field(True, alias='DB_FUTURE')

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class CelerySettings(BaseSettings):
    broker_url: str = Field(..., alias="CELERY_BROKER_URL")
    backend_url: str = Field(..., alias="CELERY_RESULT_BACKEND")

class RefPrintSettings(BaseSettings):
    save_dir: Path = Field( BASE_DIR / "saved_docs", alias='SAVE_DIR')
    
class AuthJWT(BaseSettings):
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorithm: str = Field(..., alias="JWT_ALGORITHM")
    access_token_expires_minutes: int = Field(..., alias="ACCESS_TOKEN_EXPIRES_MINUTES")
    refresh_token_expires_days: int = Field(..., alias="REFRESH_TOKEN_EXPIRES_DAYS")

    @property
    def private_key(self) -> str:
        if self.private_key_path.exists():
            return self.private_key_path.read_text()
        return ""

    @property
    def public_key(self) -> str:
        if self.public_key_path.exists():
            return self.public_key_path.read_text()
        return ""

class RefAgentSettings(BaseSettings):
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    model_name: str = Field(..., alias="MODEL_NAME")
    temperature: float = Field(..., alias="TEMPERATURE")
    validation_max_retries: int = Field(..., alias="VALIDATION_MAX_RETRIES")
    chars: int | None = Field(None, alias="CHARS")
    full_chars: int | None = Field(None, alias="FULL_CHARS")
    words: int | None = Field(None, alias="WORDS")
    
    
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', env_file_encoding='utf-8', extra='ignore')

    api_v1_prefix: str = "/api/v1"
    is_prod: str = Field(False, alias="IS_PROD")
    db: DbSettings = DbSettings()
    auth_jwt: AuthJWT = AuthJWT()
    refagent: RefAgentSettings = RefAgentSettings()
    refprint: RefPrintSettings = RefPrintSettings() 
    celery: CelerySettings = CelerySettings()

    host: str = Field("127.0.0.1", alias="HOST")
    port: int = Field(8000, alias="PORT")
    debug: bool = Field(True, alias="DEBUG")
    default_balance: int = Field(40, alias="DEFAULT_BALANCE")

settings = Settings()