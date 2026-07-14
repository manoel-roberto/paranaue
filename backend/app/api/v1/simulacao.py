from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.schemas.simulacao import SimulacaoRequest, SimulacaoResponse
from app.schemas.errors import HTTP_400_RESPONSE, HTTP_401_RESPONSE, HTTP_404_RESPONSE, HTTP_422_RESPONSE
from app.services import simulacao as simulacao_service
from app.services import relatorio as relatorio_service
from app.models.usuario import Usuario
from app.models.simulacao import Simulacao, SimulacaoItem
from app.models.servidor import Vinculo

router = APIRouter()


@router.post(
    "",
    response_model=SimulacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Executar nova simulação",
    description="Calcula o impacto financeiro da evolução de carreira de um servidor com base nas tabelas salariais de vencimento base e GSTU.",
    responses={
        400: HTTP_400_RESPONSE,
        401: HTTP_401_RESPONSE,
        422: HTTP_422_RESPONSE
    }
)
async def executar_simulacao(
    payload: SimulacaoRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Executa a simulação de impacto financeiro para a alteração de cargo/vencimento de um servidor.
    """
    ip_origem = request.client.host if request.client else "0.0.0.0"
    try:
        item = await simulacao_service.executar_simulacao(
            db=db,
            payload=payload,
            usuario_id=current_user.id,
            ip_origem=ip_origem
        )
        return {
            "id": item.id,
            "servidor_id": payload.servidor_id,
            "resultado_calculo_json": item.resultado_calculo_json,
            "justificativa": item.justificativa_requisitos
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{id}",
    response_model=SimulacaoResponse,
    summary="Obter simulação por ID",
    description="Consulta as informações detalhadas de um cálculo de simulação realizado anteriormente utilizando o seu identificador único.",
    responses={
        401: HTTP_401_RESPONSE,
        404: HTTP_404_RESPONSE
    }
)
async def obter_simulacao(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Consulta os detalhes de uma simulação já realizada pelo ID do item da simulação.
    """
    item = await simulacao_service.obter_simulacao_item_por_id(db=db, item_id=id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulação não encontrada."
        )
    return {
        "id": item.id,
        "servidor_id": item.vinculo.servidor_id,
        "resultado_calculo_json": item.resultado_calculo_json,
        "justificativa": item.justificativa_requisitos
    }


@router.get(
    "/{id}/pdf",
    summary="Exportar relatório da simulação em PDF",
    description="Gera e faz o download de um relatório PDF contendo os detalhes do impacto mensal e anual estimado do cenário simulado.",
    responses={
        401: HTTP_401_RESPONSE,
        404: HTTP_404_RESPONSE
    }
)
async def exportar_pdf_simulacao(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Gera e exporta o relatório PDF consolidado de uma simulação realizada.
    """
    stmt = (
        select(SimulacaoItem)
        .where(SimulacaoItem.id == id)
        .options(
            selectinload(SimulacaoItem.simulacao).selectinload(Simulacao.itens),
            selectinload(SimulacaoItem.vinculo).selectinload(Vinculo.servidor)
        )
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulação não encontrada."
        )

    simulacao_obj = item.simulacao
    servidor_obj = item.vinculo.servidor

    pdf_buffer = relatorio_service.gerar_pdf_simulacao(simulacao_obj, servidor_obj)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=simulacao_{id}.pdf"
        }
    )
