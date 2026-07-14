import os
import socket
from typing import Optional

# Caminho absoluto para o .env.local na pasta backend
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(backend_dir, ".env.local")

def _apply_sandbox_mapping(url: Optional[str]) -> Optional[str]:
    if url and ("localhost" in url or "127.0.0.1" in url):
        try:
            # Extrai a porta
            parts = url.split("@")[-1].split("/")[0].split(":")
            port = int(parts[1]) if len(parts) > 1 else 5432
            
            # Testa se a porta está aberta localmente
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            s.close()
        except Exception:
            # Localhost falhou. Testa o gateway da ponte do Docker (172.18.0.1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(("172.18.0.1", port))
                s.close()
                url = url.replace("localhost", "172.18.0.1").replace("127.0.0.1", "172.18.0.1")
            except Exception:
                pass
    return url

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import field_validator
    from typing import Union, List
    
    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=env_path,
            env_file_encoding="utf-8",
            extra="ignore"
        )
        SECRET_KEY: str = "sua_chave_secreta_jwt_de_producao_super_segura"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
        DATABASE_URL: Optional[str] = None
        ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
        
        ADMIN_USERNAME: str = "admin"
        ADMIN_PASSWORD: str = "admin123"
        ADMIN_EMAIL: str = "admin@example.com"

        @field_validator("ALLOWED_ORIGINS", mode="before")
        @classmethod
        def parse_allowed_origins(cls, v):
            if isinstance(v, str):
                if not v.strip():
                    return []
                cleaned = v.strip("[]'\" ")
                return [origin.strip().strip("'\"") for origin in cleaned.split(",") if origin.strip()]
            return v
except ImportError:
    from pydantic import BaseSettings, validator
    from typing import Union, List
    
    class Settings(BaseSettings):
        class Config:
            env_file = env_path
            env_file_encoding = "utf-8"
            extra = "ignore"
        SECRET_KEY: str = "sua_chave_secreta_jwt_de_producao_super_segura"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
        DATABASE_URL: Optional[str] = None
        ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
        
        ADMIN_USERNAME: str = "admin"
        ADMIN_PASSWORD: str = "admin123"
        ADMIN_EMAIL: str = "admin@example.com"

        @validator("ALLOWED_ORIGINS", pre=True)
        def parse_allowed_origins(cls, v):
            if isinstance(v, str):
                if not v.strip():
                    return []
                cleaned = v.strip("[]'\" ")
                return [origin.strip().strip("'\"") for origin in cleaned.split(",") if origin.strip()]
            return v

settings = Settings()

# Se a DATABASE_URL não foi preenchida pelas configurações, tenta carregar manualmente
if not settings.DATABASE_URL:
    url = None
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        if key.strip() == "DATABASE_URL":
                            url = val.strip()
                            break
    if not url:
        url = os.environ.get("DATABASE_URL")
    settings.DATABASE_URL = _apply_sandbox_mapping(url)
else:
    settings.DATABASE_URL = _apply_sandbox_mapping(settings.DATABASE_URL)

# Exportações a nível de módulo para compatibilidade legada
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
DATABASE_URL = settings.DATABASE_URL
ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS

