from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.schemas.vencimento_basico import (
    VencimentoBasicoCreate,
    VencimentoBasicoUpdate,
    VencimentoBasicoResponse,
)
from app.schemas.errors import HTTP_400_RESPONSE, HTTP_401_RESPONSE, HTTP_403_RESPONSE, HTTP_422_RESPONSE
from app.services import vencimento_basico as vencimento_service
from app.api.v1.parametros import get_current_admin_user

router = APIRouter()


@router.post(
    "",
    response_model=VencimentoBasicoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo vencimento básico",
    description="Insere uma nova linha na tabela de referência de vencimentos básicos. Operação restrita a administradores do sistema.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        422: HTTP_422_RESPONSE
    }
)
async def criar_vencimento(
    payload: VencimentoBasicoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Cadastra uma nova referência de vencimento básico.
    Apenas administradores podem acessar esta rota.
    """
    try:
        ip_origem = request.client.host if request.client else "0.0.0.0"
        tabela = await vencimento_service.criar_vencimento(
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
    response_model=list[VencimentoBasicoResponse],
    summary="Listar vencimentos básicos",
    description="Retorna todas as referências de vencimento básico cadastradas com paginação. Permite acesso a qualquer usuário autenticado.",
    responses={
        401: HTTP_401_RESPONSE
    }
)
async def listar_vencimentos(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna a tabela de referência de vencimentos básicos cadastrada com paginação.
    Acesso permitido a todos os usuários autenticados.
    """
    tabelas = await vencimento_service.listar_vencimentos(db=db, skip=skip, limit=limit)
    return tabelas


@router.get(
    "/{id}",
    response_model=VencimentoBasicoResponse,
    summary="Obter vencimento básico específico",
    description="Retorna os dados detalhados de um vencimento básico cadastrado na base de dados pelo seu ID. Requer autenticação.",
    responses={
        401: HTTP_401_RESPONSE,
        404: {
            "description": "Vencimento básico não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Vencimento básico não encontrado"}
                }
            }
        }
    }
)
async def obter_vencimento(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Recupera um vencimento básico específico pelo ID. Endpoint restrito a usuários autenticados.
    """
    vencimento = await vencimento_service.obter_vencimento(db=db, id=id)
    if not vencimento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vencimento básico não encontrado"
        )
    return vencimento


@router.put(
    "/{id}",
    response_model=VencimentoBasicoResponse,
    summary="Atualizar vencimento básico",
    description="Atualiza uma referência de vencimento básico existente pelo seu ID. Operação restrita a administradores do sistema.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        404: {
            "description": "Vencimento básico não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Vencimento básico não encontrado"}
                }
            }
        },
        422: HTTP_422_RESPONSE
    }
)
async def atualizar_vencimento(
    id: UUID,
    payload: VencimentoBasicoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Atualiza uma referência de vencimento básico existente pelo ID.
    Apenas administradores podem acessar esta rota.
    """
    try:
        ip_origem = request.client.host if request.client else "0.0.0.0"
        vencimento = await vencimento_service.atualizar_vencimento(
            db=db,
            id=id,
            payload=payload,
            usuario_id=admin_user.id,
            ip_origem=ip_origem
        )
        if not vencimento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vencimento básico não encontrado"
            )
        return vencimento
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir vencimento básico",
    description="Remove uma referência de vencimento básico existente pelo seu ID. Operação restrita a administradores do sistema.",
    responses={
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        404: {
            "description": "Vencimento básico não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Vencimento básico não encontrado"}
                }
            }
        }
    }
)
async def deletar_vencimento(
    id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Exclui uma referência de vencimento básico pelo ID.
    Apenas administradores podem acessar esta rota.
    """
    ip_origem = request.client.host if request.client else "0.0.0.0"
    sucesso = await vencimento_service.deletar_vencimento(
        db=db,
        id=id,
        usuario_id=admin_user.id,
        ip_origem=ip_origem
    )
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vencimento básico não encontrado"
        )
