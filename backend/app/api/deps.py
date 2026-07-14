from collections.abc import AsyncGenerator
from typing import Optional
from jose import jwt, JWTError
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import config
from app.core.database import async_session_maker
from app.models.usuario import Usuario

# Rota onde o token é obtido
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenPayload(BaseModel):
    sub: Optional[str] = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência FastAPI que cria uma sessão assíncrona com o banco e garante
    seu fechamento ao término da requisição.
    """
    async with async_session_maker() as session:
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Usuario:
    """
    Dependência FastAPI que extrai, decodifica o JWT e valida o usuário correspondente no banco.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica as claims do token JWT
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenPayload(sub=username)
    except JWTError:
        raise credentials_exception

    # Busca o usuário na base pelo username registrado na claim 'sub'
    stmt = select(Usuario).where(Usuario.username == token_data.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )

    return user
