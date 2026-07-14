from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core import config

# Configuração do contexto de criptografia de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera o hash criptográfico seguro a partir da senha em texto plano.
    """
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """
    Gera um token JWT com expiração configurada.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {
        "exp": expire,
        "sub": str(subject)
    }
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt
