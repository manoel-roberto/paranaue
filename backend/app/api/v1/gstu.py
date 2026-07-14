from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.schemas.gstu import (
    GstuCreate,
    GstuUpdate,
    GstuResponse,
)
from app.schemas.errors import HTTP_400_RESPONSE, HTTP_401_RESPONSE, HTTP_403_RESPONSE, HTTP_422_RESPONSE
from app.services import gstu as gstu_service
from app.api.v1.parametros import get_current_admin_user

router = APIRouter()


@router.post(
    "",
    response_model=GstuResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova gratificação GSTU",
    description="Insere uma nova linha na tabela de referência de gratificação GSTU. Operação restrita a administradores do sistema.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        422: HTTP_422_RESPONSE
    }
)
async def criar_gstu(
    payload: GstuCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Cadastra uma nova referência de gratificação GSTU.
    Apenas administradores podem acessar esta rota.
    """
    try:
        ip_origem = request.client.host if request.client else "0.0.0.0"
        tabela = await gstu_service.criar_gstu(
            db=db,
            payload=payload,
            usuario_id=admin_user.id,
            ip_origem=ip_origem
        )
        return tabela
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=list[GstuResponse],
    summary="Listar gratificações GSTU",
    description="Retorna todas as referências de gratificação GSTU cadastradas com paginação. Permite acesso a qualquer usuário autenticado.",
    responses={
        401: HTTP_401_RESPONSE
    }
)
async def listar_gstu(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna a tabela de referência de GSTU cadastrada com paginação.
    Acesso permitido a todos os usuários autenticados.
    """
    tabelas = await gstu_service.listar_gstu(db=db, skip=skip, limit=limit)
    return tabelas


@router.get(
    "/{id}",
    response_model=GstuResponse,
    summary="Obter gratificação GSTU específica",
    description="Retorna os dados detalhados de uma gratificação GSTU cadastrada na base de dados pelo seu ID. Requer autenticação.",
    responses={
        401: HTTP_401_RESPONSE,
        404: {
            "description": "Gratificação GSTU não encontrada",
            "content": {
                "application/json": {
                    "example": {"detail": "Gratificação GSTU não encontrada"}
                }
            }
        }
    }
)
async def obter_gstu(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Recupera uma gratificação GSTU específica pelo ID. Endpoint restrito a usuários autenticados.
    """
    gstu = await gstu_service.obter_gstu(db=db, id=id)
    if not gstu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gratificação GSTU não encontrada"
        )
    return gstu


@router.put(
    "/{id}",
    response_model=GstuResponse,
    summary="Atualizar gratificação GSTU",
    description="Atualiza uma referência de gratificação GSTU existente pelo seu ID. Operação restrita a administradores do sistema.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        404: {
            "description": "Gratificação GSTU não encontrada",
            "content": {
                "application/json": {
                    "example": {"detail": "Gratificação GSTU não encontrada"}
                }
            }
        },
        422: HTTP_422_RESPONSE
    }
)
async def atualizar_gstu(
    id: UUID,
    payload: GstuUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Atualiza uma referência de gratificação GSTU existente pelo ID.
    Apenas administradores podem acessar esta rota.
    """
    try:
        ip_origem = request.client.host if request.client else "0.0.0.0"
        gstu = await gstu_service.atualizar_gstu(
            db=db,
            id=id,
            payload=payload,
            usuario_id=admin_user.id,
            ip_origem=ip_origem
        )
        if not gstu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gratificação GSTU não encontrada"
            )
        return gstu
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir gratificação GSTU",
    description="Remove uma referência de gratificação GSTU existente pelo seu ID. Operação restrita a administradores do sistema.",
    responses={
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        404: {
            "description": "Gratificação GSTU não encontrada",
            "content": {
                "application/json": {
                    "example": {"detail": "Gratificação GSTU não encontrada"}
                }
            }
        }
    }
)
async def deletar_gstu(
    id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Exclui uma referência de gratificação GSTU pelo ID.
    Apenas administradores podem acessar esta rota.
    """
    ip_origem = request.client.host if request.client else "0.0.0.0"
    sucesso = await gstu_service.deletar_gstu(
        db=db,
        id=id,
        usuario_id=admin_user.id,
        ip_origem=ip_origem
    )
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gratificação GSTU não encontrada"
        )
