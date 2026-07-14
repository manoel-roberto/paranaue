from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.schemas.parametros import (
    TabelaVencimentoSchema,
    TabelaVencimentoResponse,
    TabelaGstuSchema,
    TabelaGstuResponse,
    TabelaComissaoResponse,
)
from app.schemas.errors import HTTP_400_RESPONSE, HTTP_401_RESPONSE, HTTP_403_RESPONSE, HTTP_422_RESPONSE
from app.services import parametros as parametros_service

router = APIRouter()


async def get_current_admin_user(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Dependência que valida se o usuário autenticado possui o perfil de ADMINISTRADOR.
    """
    stmt = (
        select(Usuario)
        .options(selectinload(Usuario.perfis))
        .where(Usuario.id == current_user.id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one()

    nomes_perfis = [perfil.nome for perfil in user.perfis]
    if "ADMINISTRADOR" not in nomes_perfis:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação restrita a administradores."
        )
    return user


@router.post(
    "/vencimento",
    response_model=TabelaVencimentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova linha de vencimento",
    description="Insere uma nova linha na tabela de referência de vencimentos básicos. Operação restrita a administradores do sistema.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        422: HTTP_422_RESPONSE
    }
)
async def criar_tabela_vencimento(
    payload: TabelaVencimentoSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Cadastra uma nova linha na tabela de referência de vencimentos.
    Apenas administradores podem acessar esta rota.
    """
    try:
        ip_origem = request.client.host if request.client else "0.0.0.0"
        tabela = await parametros_service.criar_tabela_vencimento(
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
    "/vencimento",
    response_model=list[TabelaVencimentoResponse],
    summary="Listar referências de vencimento",
    description="Retorna todas as linhas de vencimento básico cadastradas com paginação. Permite acesso a qualquer usuário autenticado.",
    responses={
        401: HTTP_401_RESPONSE
    }
)
async def listar_tabela_vencimento(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna a tabela de referência de vencimentos cadastrada com paginação.
    Acesso permitido a todos os usuários autenticados.
    """
    tabelas = await parametros_service.listar_tabela_vencimento(db=db, skip=skip, limit=limit)
    return tabelas


@router.post(
    "/gstu",
    response_model=TabelaGstuResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova referência GSTU",
    description="Cadastra uma nova linha na tabela de referência GSTU. Operação restrita a administradores do sistema.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        403: HTTP_403_RESPONSE,
        422: HTTP_422_RESPONSE
    }
)
async def criar_tabela_gstu(
    payload: TabelaGstuSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(get_current_admin_user),
):
    """
    Cadastra uma nova linha na tabela de referência GSTU.
    Apenas administradores podem acessar esta rota.
    """
    try:
        ip_origem = request.client.host if request.client else "0.0.0.0"
        tabela = await parametros_service.criar_tabela_gstu(
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
    "/gstu",
    response_model=list[TabelaGstuResponse],
    summary="Listar referências GSTU",
    description="Retorna todas as referências GSTU cadastradas com paginação. Permite acesso a qualquer usuário autenticado.",
    responses={
        401: HTTP_401_RESPONSE
    }
)
async def listar_tabela_gstu(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna a tabela de referência GSTU cadastrada com paginação.
    Acesso permitido a todos os usuários autenticados.
    """
    tabelas = await parametros_service.listar_tabela_gstu(db=db, skip=skip, limit=limit)
    return tabelas


@router.get(
    "/comissao",
    response_model=list[TabelaComissaoResponse],
    summary="Listar referências de comissão",
    description="Retorna todas as comissões cadastradas com paginação. Permite acesso a qualquer usuário autenticado.",
    responses={
        401: HTTP_401_RESPONSE
    }
)
async def listar_tabela_comissao(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna a tabela de referência de comissões cadastrada com paginação.
    Acesso permitido a todos os usuários autenticados.
    """
    tabelas = await parametros_service.listar_tabela_comissao(db=db, skip=skip, limit=limit)
    return tabelas
