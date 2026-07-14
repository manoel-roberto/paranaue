from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.servidor import (
    ServidorCreateSchema,
    ServidorResponse,
    ServidorUpdate,
    VinculoCreateSchema,
    VinculoResponse,
    HistoricoFuncionalCreateSchema,
    HistoricoFuncionalResponse,
    AverbacaoCreateSchema,
    AverbacaoResponse,
    CargoResponse,
)
from app.schemas.errors import HTTP_400_RESPONSE, HTTP_401_RESPONSE, HTTP_422_RESPONSE
from app.services import servidor as servidor_service
from app.models.usuario import Usuario

router = APIRouter()


@router.post(
    "",
    response_model=ServidorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo servidor",
    description="Efetua o cadastro de um novo servidor na instituição (UEFS) com validação de CPF. Requer autenticação de usuário.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        422: HTTP_422_RESPONSE
    }
)
async def criar_servidor(
    payload: ServidorCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cadastra um novo servidor. Endpoint restrito a usuários autenticados.
    """
    try:
        servidor = await servidor_service.criar_servidor(db=db, payload=payload)
        return servidor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=list[ServidorResponse],
    summary="Listar servidores",
    description="Retorna a lista paginada de todos os servidores cadastrados na base de dados. Requer autenticação.",
    responses={
        401: HTTP_401_RESPONSE
    }
)
async def listar_servidores(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista servidores cadastrados com paginação. Endpoint restrito a usuários autenticados.
    """
    servidores = await servidor_service.listar_servidores(db=db, skip=skip, limit=limit)
    return servidores


@router.get(
    "/{servidor_id}",
    response_model=ServidorResponse,
    summary="Obter servidor específico",
    description="Retorna os dados detalhados de um servidor cadastrado na base de dados pelo seu ID. Requer autenticação.",
    responses={
        401: HTTP_401_RESPONSE,
        404: {
            "description": "Servidor não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Servidor não encontrado"}
                }
            }
        }
    }
)
async def obter_servidor(
    servidor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Recupera um servidor específico pelo ID. Endpoint restrito a usuários autenticados.
    """
    servidor = await servidor_service.obter_servidor(db=db, servidor_id=servidor_id)
    if not servidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servidor não encontrado"
        )
    return servidor


@router.put(
    "/{servidor_id}",
    response_model=ServidorResponse,
    summary="Atualizar servidor",
    description="Atualiza os dados de um servidor cadastrado. Requer autenticação.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        404: {
            "description": "Servidor não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Servidor não encontrado"}
                }
            }
        },
        422: HTTP_422_RESPONSE
    }
)
async def atualizar_servidor(
    servidor_id: UUID,
    payload: ServidorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Atualiza os dados de um servidor existente. Endpoint restrito a usuários autenticados.
    """
    try:
        servidor = await servidor_service.atualizar_servidor(
            db=db, servidor_id=servidor_id, payload=payload
        )
        if not servidor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servidor não encontrado"
            )
        return servidor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{servidor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir servidor",
    description="Exclui definitivamente um servidor cadastrado, contanto que ele não possua vínculos ativos. Requer autenticação.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        404: {
            "description": "Servidor não encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Servidor não encontrado"}
                }
            }
        }
    }
)
async def deletar_servidor(
    servidor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Exclui um servidor específico. Retorna 204 se excluído, 404 se não encontrado ou 400 se possuir restrições.
    """
    try:
        sucesso = await servidor_service.deletar_servidor(db=db, servidor_id=servidor_id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servidor não encontrado"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{servidor_id}/vinculos",
    response_model=VinculoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar vínculo para o servidor",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        422: HTTP_422_RESPONSE,
    }
)
async def criar_vinculo(
    servidor_id: UUID,
    payload: VinculoCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        vinculo = await servidor_service.criar_vinculo(db=db, servidor_id=servidor_id, payload=payload)
        return vinculo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{servidor_id}/vinculos",
    response_model=list[VinculoResponse],
    summary="Listar vínculos do servidor",
    responses={
        401: HTTP_401_RESPONSE,
    }
)
async def listar_vinculos(
    servidor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    vinculos = await servidor_service.listar_vinculos_do_servidor(db=db, servidor_id=servidor_id)
    return vinculos


@router.post(
    "/vinculos/{vinculo_id}/historico",
    response_model=HistoricoFuncionalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar histórico funcional para o vínculo",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        422: HTTP_422_RESPONSE,
    }
)
async def criar_historico(
    vinculo_id: UUID,
    payload: HistoricoFuncionalCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        historico = await servidor_service.criar_historico_funcional(db=db, vinculo_id=vinculo_id, payload=payload)
        return historico
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/vinculos/{vinculo_id}/historico",
    response_model=list[HistoricoFuncionalResponse],
    summary="Listar histórico funcional do vínculo",
    responses={
        401: HTTP_401_RESPONSE,
    }
)
async def listar_historico(
    vinculo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    historicos = await servidor_service.listar_historico_funcional(db=db, vinculo_id=vinculo_id)
    return historicos


@router.post(
    "/vinculos/{vinculo_id}/averbacoes",
    response_model=AverbacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar averbação para o vínculo",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        422: HTTP_422_RESPONSE,
    }
)
async def criar_averbacao(
    vinculo_id: UUID,
    payload: AverbacaoCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        averbacao = await servidor_service.criar_averbacao(db=db, vinculo_id=vinculo_id, payload=payload)
        return averbacao
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/vinculos/{vinculo_id}/averbacoes",
    response_model=list[AverbacaoResponse],
    summary="Listar averbações do vínculo",
    responses={
        401: HTTP_401_RESPONSE,
    }
)
async def listar_averbacoes(
    vinculo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    averbacoes = await servidor_service.listar_averbacoes(db=db, vinculo_id=vinculo_id)
    return averbacoes


@router.get(
    "/cargos",
    response_model=list[CargoResponse],
    summary="Listar cargos cadastrados",
    responses={
        401: HTTP_401_RESPONSE,
    }
)
async def listar_cargos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cargos = await servidor_service.listar_cargos(db=db)
    return cargos
