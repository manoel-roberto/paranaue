from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import config, security
from app.api.deps import get_db
from app.models.usuario import Usuario
from app.schemas.auth import TokenResponse
from app.schemas.errors import HTTP_400_RESPONSE, HTTP_401_RESPONSE, HTTP_422_RESPONSE

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticar usuário",
    description="Autentica o usuário utilizando fluxo OAuth2 Password Flow. Recebe as credenciais form-encoded (username e password) e retorna o token JWT de acesso.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        422: HTTP_422_RESPONSE
    }
)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Endpoint OAuth2 compatível que autentica o usuário e retorna o token de acesso.
    """
    # Busca o usuário pelo username fornecido no formulário
    stmt = select(Usuario).where(Usuario.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Valida usuário e senha
    if not user or not security.verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )

    # Gera o JWT Token
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.username,
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expira_em_segundos": config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
