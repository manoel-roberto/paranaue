from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.servidor import Servidor, Vinculo, Averbacao, TipoAverbacao
from app.models.tabelas import TabelaVencimento, TabelaGstu, TabelaComissao, HistoricoFuncional
from app.models.simulacao import Simulacao, SimulacaoItem, StatusSimulacao, TipoSimulacao, AuditLog, OperacaoLog
from app.schemas.simulacao import SimulacaoRequest
from app.services.calculador import (
    calcular_ats,
    calcular_percentual_simples,
    calcular_estabilidade,
)


def _serialize_decimals(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte todos os valores Decimal em floats para persistência segura no JSONB.
    """
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in d.items()}


async def _calcular_cenario(
    db: AsyncSession,
    vinculo: Vinculo,
    vencimento_id: UUID,
    gstu_id: Optional[UUID],
    data_vigencia: date,
    dias_averbados: int,
    cet_percentual: Decimal,
    insalubridade_percentual: Decimal,
    vpess_valor: Decimal,
    tabela_comissao_id: Optional[UUID],
    percentual_estabilizado: Decimal,
) -> Dict[str, Any]:
    # 1. Buscar a tabela de vencimento informada
    stmt_venc = select(TabelaVencimento).where(TabelaVencimento.id == vencimento_id)
    res_venc = await db.execute(stmt_venc)
    vencimento = res_venc.scalar_one_or_none()
    if not vencimento:
        raise ValueError("Tabela de vencimento não encontrada.")
    valor_base = Decimal(str(vencimento.valor_base))

    # 2. Buscar a tabela GSTU informada (se houver)
    valor_gstu = Decimal("0.00")
    if gstu_id:
        stmt_gstu = select(TabelaGstu).where(TabelaGstu.id == gstu_id)
        res_gstu = await db.execute(stmt_gstu)
        gstu = res_gstu.scalar_one_or_none()
        if not gstu:
            raise ValueError("Tabela GSTU não encontrada.")
        valor_gstu = Decimal(str(gstu.valor_gstu))

    # 3. Calcular Adicional por Tempo de Serviço (ATS)
    # total_dias = admissao ate data_vigencia + dias averbados de ATS
    dias_admissao = (data_vigencia - vinculo.data_admissao).days
    total_dias = dias_admissao + dias_averbados
    anos_servico = max(0, total_dias // 365)
    valor_ats = calcular_ats(valor_base, anos_servico)

    # 4. Calcular CET
    valor_cet = calcular_percentual_simples(valor_base, Decimal(str(cet_percentual)))

    # 5. Calcular Insalubridade
    valor_insalubridade = calcular_percentual_simples(valor_base, Decimal(str(insalubridade_percentual)))

    # 6. VPESS (Valor fixo)
    valor_vpess = Decimal(str(vpess_valor))

    # 7. Estabilidade Econômica
    valor_estabilidade = Decimal("0.00")
    if tabela_comissao_id:
        stmt_comissao = select(TabelaComissao).where(TabelaComissao.id == tabela_comissao_id)
        res_comissao = await db.execute(stmt_comissao)
        comissao = res_comissao.scalar_one_or_none()
        if comissao:
            valor_estabilidade = calcular_estabilidade(
                Decimal(str(comissao.valor_comissao)),
                Decimal(str(percentual_estabilizado))
            )

    # 8. Custo Total
    valor_total = (
        valor_base
        + valor_gstu
        + valor_ats
        + valor_cet
        + valor_insalubridade
        + valor_vpess
        + valor_estabilidade
    )

    return {
        "salario_base": valor_base,
        "gstu": valor_gstu,
        "ats": valor_ats,
        "cet": valor_cet,
        "insalubridade": valor_insalubridade,
        "vpess": valor_vpess,
        "estabilidade": valor_estabilidade,
        "valor_total": valor_total,
    }


async def executar_simulacao(
    db: AsyncSession,
    payload: SimulacaoRequest,
    usuario_id: UUID,
    ip_origem: str = "0.0.0.0"
) -> SimulacaoItem:
    # 1. Buscar o Servidor e garantir que ele existe
    stmt_servidor = select(Servidor).where(Servidor.id == payload.servidor_id)
    res_servidor = await db.execute(stmt_servidor)
    servidor = res_servidor.scalar_one_or_none()
    if not servidor:
        raise ValueError("Servidor não encontrado.")

    # 2. Buscar o vínculo ativo (ativo == True)
    stmt_vinculo = select(Vinculo).where(
        Vinculo.servidor_id == payload.servidor_id,
        Vinculo.ativo == True
    )
    res_vinculo = await db.execute(stmt_vinculo)
    vinculo = res_vinculo.scalar_one_or_none()
    if not vinculo:
        raise ValueError("Servidor não possui vínculo ativo.")

    # 3. Buscar histórico funcional ativo (data_fim == '9999-12-31')
    stmt_historico = select(HistoricoFuncional).where(
        HistoricoFuncional.vinculo_id == vinculo.id,
        HistoricoFuncional.data_fim == date(9999, 12, 31)
    )
    res_historico = await db.execute(stmt_historico)
    historico_atual = res_historico.scalar_one_or_none()
    if not historico_atual:
        raise ValueError("Histórico funcional ativo do servidor não encontrado.")

    # 4. Buscar tempo averbado para ATS
    stmt_averbacoes = select(Averbacao).where(
        Averbacao.vinculo_id == vinculo.id,
        Averbacao.tipo_averbacao == TipoAverbacao.ATS
    )
    res_averbacoes = await db.execute(stmt_averbacoes)
    averbacoes = res_averbacoes.scalars().all()
    dias_averbados = sum(a.dias_averbados for a in averbacoes)

    # 5. Executar cenário atual
    cenario_atual = await _calcular_cenario(
        db=db,
        vinculo=vinculo,
        vencimento_id=historico_atual.tabela_vencimento_id,
        gstu_id=historico_atual.tabela_gstu_id,
        data_vigencia=payload.data_vigencia,
        dias_averbados=dias_averbados,
        cet_percentual=historico_atual.cet_percentual,
        insalubridade_percentual=historico_atual.insalubridade_percentual,
        vpess_valor=historico_atual.vpess_valor,
        tabela_comissao_id=historico_atual.tabela_comissao_id,
        percentual_estabilizado=historico_atual.percentual_estabilizado,
    )

    # 6. Executar cenário proposto
    cenario_proposto = await _calcular_cenario(
        db=db,
        vinculo=vinculo,
        vencimento_id=payload.novo_vencimento_id,
        gstu_id=payload.novo_gstu_id,
        data_vigencia=payload.data_vigencia,
        dias_averbados=dias_averbados,
        cet_percentual=historico_atual.cet_percentual,
        insalubridade_percentual=historico_atual.insalubridade_percentual,
        vpess_valor=historico_atual.vpess_valor,
        tabela_comissao_id=historico_atual.tabela_comissao_id,
        percentual_estabilizado=historico_atual.percentual_estabilizado,
    )

    # 7. Comparar e obter impacto financeiro
    impacto_financeiro_bruto = cenario_proposto["valor_total"] - cenario_atual["valor_total"]
    if cenario_atual["valor_total"] > 0:
        percentual_impacto = (impacto_financeiro_bruto / cenario_atual["valor_total"]) * 100
    else:
        percentual_impacto = Decimal("0.00")

    resultado_calculo = {
        "impacto_financeiro_bruto": impacto_financeiro_bruto,
        "percentual_impacto": percentual_impacto,
    }

    # 8. Formatar resultados em floats para persistência segura
    dados_origem_json = _serialize_decimals(cenario_atual)
    dados_propostos_json = _serialize_decimals(cenario_proposto)
    resultado_calculo_json = _serialize_decimals(resultado_calculo)

    # Justificativa padrão/mínima solicitada
    justificativa = "Servidor apto à promoção automática por tempo."

    # 9. Persistir Simulação e SimulaçãoItem
    nova_simulacao = Simulacao(
        id=uuid4(),
        descricao=f"Simulação Individual - Servidor {servidor.nome}",
        tipo=TipoSimulacao.INDIVIDUAL,
        status=StatusSimulacao.FINALIZADO,
        criado_por_usuario_id=usuario_id,
    )
    db.add(nova_simulacao)
    await db.flush()  # Garante id gerado no banco

    novo_item = SimulacaoItem(
        id=uuid4(),
        simulacao_id=nova_simulacao.id,
        vinculo_id=vinculo.id,
        data_vigencia_proposta=payload.data_vigencia,
        mes_gozo_ferias_proposto=payload.mes_ferias,
        dados_origem_json=dados_origem_json,
        dados_propostos_json=dados_propostos_json,
        resultado_calculo_json=resultado_calculo_json,
        justificativa_requisitos=justificativa,
    )
    db.add(novo_item)

    # 10. Registrar Auditoria (AuditLog)
    audit_log = AuditLog(
        id=uuid4(),
        usuario_id=usuario_id,
        tabela_afetada="simulacao",
        registro_id=nova_simulacao.id,
        operacao=OperacaoLog.SIMULACAO_EXECUCAO,
        payload_antigo=None,
        payload_novo={
            "id": str(nova_simulacao.id),
            "descricao": nova_simulacao.descricao,
            "tipo": nova_simulacao.tipo.value,
            "status": nova_simulacao.status.value,
            "criado_por_usuario_id": str(nova_simulacao.criado_por_usuario_id),
        },
        ip_origem=ip_origem,
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(novo_item)

    return novo_item


async def obter_simulacao_item_por_id(db: AsyncSession, item_id: UUID) -> Optional[SimulacaoItem]:
    """
    Busca um item de simulação pelo ID.
    """
    stmt = (
        select(SimulacaoItem)
        .where(SimulacaoItem.id == item_id)
        .options(selectinload(SimulacaoItem.vinculo))
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()
