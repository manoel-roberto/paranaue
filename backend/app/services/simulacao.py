from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
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


def _serialize_decimals(obj: Any) -> Any:
    """
    Converte recursivamente todos os valores Decimal em floats/estruturas nativas para persistência no JSONB.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _serialize_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_decimals(v) for v in obj]
    return obj


async def _obter_vencimento_historico(db: AsyncSession, venc: TabelaVencimento, data_ref: date) -> TabelaVencimento:
    stmt = select(TabelaVencimento).where(
        TabelaVencimento.classe == venc.classe,
        TabelaVencimento.nivel_grau == venc.nivel_grau,
        TabelaVencimento.carga_horaria == venc.carga_horaria,
        TabelaVencimento.data_inicio_vigencia <= data_ref,
        TabelaVencimento.data_fim_vigencia >= data_ref
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none() or venc


async def _obter_gstu_historico(db: AsyncSession, gstu: TabelaGstu, data_ref: date) -> TabelaGstu:
    stmt = select(TabelaGstu).where(
        TabelaGstu.grau == gstu.grau,
        TabelaGstu.referencia == gstu.referencia,
        TabelaGstu.data_inicio_vigencia <= data_ref,
        TabelaGstu.data_fim_vigencia >= data_ref
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none() or gstu


async def _obter_comissao_historico(db: AsyncSession, com: TabelaComissao, data_ref: date) -> TabelaComissao:
    stmt = select(TabelaComissao).where(
        TabelaComissao.simbolo == com.simbolo,
        TabelaComissao.data_inicio_vigencia <= data_ref,
        TabelaComissao.data_fim_vigencia >= data_ref
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none() or com


async def _obter_historico_servidor_na_data(db: AsyncSession, vinculo_id: UUID, data_ref: date) -> Optional[HistoricoFuncional]:
    stmt = select(HistoricoFuncional).where(
        HistoricoFuncional.vinculo_id == vinculo_id,
        HistoricoFuncional.data_inicio <= data_ref,
        HistoricoFuncional.data_fim >= data_ref
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def _calcular_valores_na_data(
    db: AsyncSession,
    vinculo: Vinculo,
    vencimento_grade: TabelaVencimento,
    gstu_grade: Optional[TabelaGstu],
    hist_func: Any,  # HistoricoFuncional ou MockHist
    data_ref: date,
    dias_averbados: int,
) -> Dict[str, Any]:
    # 1. Obter vencimento reajustado na data_ref
    venc = await _obter_vencimento_historico(db, vencimento_grade, data_ref)
    valor_base = Decimal(str(venc.valor_base))
    
    # 2. Obter GSTU reajustado na data_ref
    valor_gstu = Decimal("0.00")
    if gstu_grade:
        gstu = await _obter_gstu_historico(db, gstu_grade, data_ref)
        valor_gstu = Decimal(str(gstu.valor_gstu))
        
    # 3. Calcular Adicional por Tempo de Serviço (ATS)
    dias_admissao = (data_ref - vinculo.data_admissao).days
    total_dias = dias_admissao + dias_averbados
    anos_servico = max(0, total_dias // 365)
    valor_ats = calcular_ats(valor_base, anos_servico)
    
    # 4. CET e Insalubridade
    valor_cet = calcular_percentual_simples(valor_base, Decimal(str(hist_func.cet_percentual)))
    valor_insalubridade = calcular_percentual_simples(valor_base, Decimal(str(hist_func.insalubridade_percentual)))
    
    # 5. VPESS
    valor_vpess = Decimal(str(hist_func.vpess_valor))
    
    # 6. Estabilidade Econômica
    valor_estabilidade = Decimal("0.00")
    if hist_func.tabela_comissao_id:
        stmt_com = select(TabelaComissao).where(TabelaComissao.id == hist_func.tabela_comissao_id)
        res_com = await db.execute(stmt_com)
        com_grade = res_com.scalar_one_or_none()
        if com_grade:
            com = await _obter_comissao_historico(db, com_grade, data_ref)
            valor_estabilidade = calcular_estabilidade(
                Decimal(str(com.valor_comissao)),
                Decimal(str(hist_func.percentual_estabilizado))
            )
            
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
    stmt_venc = select(TabelaVencimento).where(TabelaVencimento.id == vencimento_id)
    res_venc = await db.execute(stmt_venc)
    vencimento = res_venc.scalar_one_or_none()
    if not vencimento:
        raise ValueError("Tabela de vencimento não encontrada.")

    gstu = None
    if gstu_id:
        stmt_gstu = select(TabelaGstu).where(TabelaGstu.id == gstu_id)
        res_gstu = await db.execute(stmt_gstu)
        gstu = res_gstu.scalar_one_or_none()

    class MockHist:
        def __init__(self):
            self.cet_percentual = cet_percentual
            self.insalubridade_percentual = insalubridade_percentual
            self.vpess_valor = vpess_valor
            self.tabela_comissao_id = tabela_comissao_id
            self.percentual_estabilizado = percentual_estabilizado

    return await _calcular_valores_na_data(
        db=db,
        vinculo=vinculo,
        vencimento_grade=vencimento,
        gstu_grade=gstu,
        hist_func=MockHist(),
        data_ref=data_vigencia,
        dias_averbados=dias_averbados
    )


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

    # 5. Buscar tabelas propostas do payload
    stmt_v_proposto = select(TabelaVencimento).where(TabelaVencimento.id == payload.novo_vencimento_id)
    res_v_proposto = await db.execute(stmt_v_proposto)
    vencimento_proposto = res_v_proposto.scalar_one_or_none()
    if not vencimento_proposto:
        raise ValueError("Tabela de vencimento proposta não encontrada.")

    gstu_proposto = None
    if payload.novo_gstu_id:
        stmt_g_proposto = select(TabelaGstu).where(TabelaGstu.id == payload.novo_gstu_id)
        res_g_proposto = await db.execute(stmt_g_proposto)
        gstu_proposto = res_g_proposto.scalar_one_or_none()

    # 6. Executar cenário atual na data_vigencia
    cenario_atual = await _calcular_valores_na_data(
        db=db,
        vinculo=vinculo,
        vencimento_grade=historico_atual.tabela_vencimento,
        gstu_grade=historico_atual.tabela_gstu,
        hist_func=historico_atual,
        data_ref=payload.data_vigencia,
        dias_averbados=dias_averbados
    )

    # 7. Executar cenário proposto na data_vigencia
    cenario_proposto = await _calcular_valores_na_data(
        db=db,
        vinculo=vinculo,
        vencimento_grade=vencimento_proposto,
        gstu_grade=gstu_proposto,
        hist_func=historico_atual,
        data_ref=payload.data_vigencia,
        dias_averbados=dias_averbados
    )

    # 7.1 Comparar e obter impacto financeiro bruto mensal
    impacto_financeiro_bruto = cenario_proposto["valor_total"] - cenario_atual["valor_total"]
    if cenario_atual["valor_total"] > 0:
        percentual_impacto = (impacto_financeiro_bruto / cenario_atual["valor_total"]) * 100
    else:
        percentual_impacto = Decimal("0.00")

    # 8. Cálculo de Retroativos Históricos (RND015) e Proporcionalidade Diária (RND013)
    today_date = date.today()
    retroativo_total = Decimal("0.00")
    detalhes_retroativos = []

    if payload.data_vigencia < today_date:
        ano, mes = payload.data_vigencia.year, payload.data_vigencia.month
        fim_ano, fim_mes = today_date.year, today_date.month

        while (ano < fim_ano) or (ano == fim_ano and mes <= fim_mes):
            ref_data = date(ano, mes, 1)

            # Verificar se há histórico funcional na data
            hist_ref = await _obter_historico_servidor_na_data(db, vinculo.id, ref_data)
            if not hist_ref:
                hist_ref = historico_atual

            # Mês de transição: aplica proporcionalidade diária (RND013) apenas se o início for após o dia 1
            if ano == payload.data_vigencia.year and mes == payload.data_vigencia.month:
                dia_inicio = payload.data_vigencia.day
                if dia_inicio == 1:
                    actual_m = await _calcular_valores_na_data(
                        db, vinculo, hist_ref.tabela_vencimento, hist_ref.tabela_gstu,
                        hist_ref, ref_data, dias_averbados
                    )
                    proposed_m = await _calcular_valores_na_data(
                        db, vinculo, vencimento_proposto, gstu_proposto,
                        hist_ref, ref_data, dias_averbados
                    )
                    impacto_m = proposed_m["valor_total"] - actual_m["valor_total"]
                else:
                    dias_antigo = dia_inicio - 1
                    dias_novo = 30 - dias_antigo

                    actual_m = await _calcular_valores_na_data(
                        db, vinculo, hist_ref.tabela_vencimento, hist_ref.tabela_gstu,
                        hist_ref, ref_data, dias_averbados
                    )
                    proposed_m = await _calcular_valores_na_data(
                        db, vinculo, vencimento_proposto, gstu_proposto,
                        hist_ref, ref_data, dias_averbados
                    )

                    impacto_m = Decimal("0.00")
                    for key in ["salario_base", "gstu", "ats", "cet", "insalubridade", "estabilidade"]:
                        diff_rubrica = proposed_m[key] - actual_m[key]
                        valor_diario = diff_rubrica / Decimal("30.0")
                        valor_diario_truncado = valor_diario.quantize(Decimal("0.001"), rounding=ROUND_DOWN)
                        prop_rubrica = (valor_diario_truncado * Decimal(dias_novo)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        impacto_m += prop_rubrica
            else:
                # Mês cheio
                actual_m = await _calcular_valores_na_data(
                    db, vinculo, hist_ref.tabela_vencimento, hist_ref.tabela_gstu,
                    hist_ref, ref_data, dias_averbados
                )
                proposed_m = await _calcular_valores_na_data(
                    db, vinculo, vencimento_proposto, gstu_proposto,
                    hist_ref, ref_data, dias_averbados
                )
                impacto_m = proposed_m["valor_total"] - actual_m["valor_total"]

            retroativo_total += impacto_m
            detalhes_retroativos.append({
                "competencia": f"{mes:02d}/{ano}",
                "impacto": float(impacto_m)
            })

            # Incrementar mês
            if mes == 12:
                mes = 1
                ano += 1
            else:
                mes += 1

    # 9. Cálculo de Impacto no Primeiro Ano (RND014)
    vig_ano = payload.data_vigencia.year
    vig_mes = payload.data_vigencia.month

    # 9.1 Mês de transição proporcional
    dia_inicio = payload.data_vigencia.day
    actual_vig = await _calcular_valores_na_data(
        db, vinculo, historico_atual.tabela_vencimento, historico_atual.tabela_gstu,
        historico_atual, payload.data_vigencia, dias_averbados
    )
    proposed_vig = await _calcular_valores_na_data(
        db, vinculo, vencimento_proposto, gstu_proposto,
        historico_atual, payload.data_vigencia, dias_averbados
    )

    if dia_inicio == 1:
        impacto_transicao = proposed_vig["valor_total"] - actual_vig["valor_total"]
    else:
        dias_antigo = dia_inicio - 1
        dias_novo = 30 - dias_antigo
        impacto_transicao = Decimal("0.00")
        for key in ["salario_base", "gstu", "ats", "cet", "insalubridade", "estabilidade"]:
            diff_rubrica = proposed_vig[key] - actual_vig[key]
            valor_diario = diff_rubrica / Decimal("30.0")
            valor_diario_truncado = valor_diario.quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            prop_rubrica = (valor_diario_truncado * Decimal(dias_novo)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            impacto_transicao += prop_rubrica

    # 9.2 Meses cheios pós-vigência no primeiro ano
    impacto_meses_cheios = Decimal("0.00")
    for m in range(vig_mes + 1, 13):
        ref_data = date(vig_ano, m, 1)
        actual_m = await _calcular_valores_na_data(
            db, vinculo, historico_atual.tabela_vencimento, historico_atual.tabela_gstu,
            historico_atual, ref_data, dias_averbados
        )
        proposed_m = await _calcular_valores_na_data(
            db, vinculo, vencimento_proposto, gstu_proposto,
            historico_atual, ref_data, dias_averbados
        )
        impacto_meses_cheios += (proposed_m["valor_total"] - actual_m["valor_total"])

    # 9.3 Proporcionalidade de 13º Salário
    impacto_13 = proposed_vig["valor_total"] - actual_vig["valor_total"]

    # 9.4 Proporcionalidade de Férias (mes_ferias)
    if payload.mes_ferias >= vig_mes:
        impacto_ferias = (proposed_vig["valor_total"] - actual_vig["valor_total"]) / Decimal("3.0")
    else:
        impacto_ferias = Decimal("0.00")
    impacto_ferias = impacto_ferias.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Total primeiro ano
    impacto_anual_primeiro_ano = impacto_transicao + impacto_meses_cheios + impacto_13 + impacto_ferias

    # 10. Impacto anual padrão estimado
    impacto_anual_estimado = (impacto_financeiro_bruto * Decimal("12.0")) + impacto_13 + impacto_ferias

    resultado_calculo = {
        "impacto_financeiro_bruto": impacto_financeiro_bruto,
        "percentual_impacto": percentual_impacto,
        "vencimento_atual": cenario_atual["salario_base"],
        "vencimento_proposto": cenario_proposto["salario_base"],
        "gstu_atual": cenario_atual["gstu"],
        "gstu_proposto": cenario_proposto["gstu"],
        "ats_atual": cenario_atual["ats"],
        "ats_proposto": cenario_proposto["ats"],
        "cet_atual": cenario_atual["cet"],
        "cet_proposto": cenario_proposto["cet"],
        "insalubridade_atual": cenario_atual["insalubridade"],
        "insalubridade_proposto": cenario_proposto["insalubridade"],
        "estabilidade_atual": cenario_atual["estabilidade"],
        "estabilidade_proposto": cenario_proposto["estabilidade"],
        "vpess_atual": cenario_atual["vpess"],
        "vpess_proposto": cenario_proposto["vpess"],
        "valor_total_atual": cenario_atual["valor_total"],
        "valor_total_proposto": cenario_proposto["valor_total"],
        "impacto_mensal": impacto_financeiro_bruto,
        "impacto_transicao": impacto_transicao,
        "impacto_13": impacto_13,
        "impacto_ferias": impacto_ferias,
        "impacto_anual_primeiro_ano": impacto_anual_primeiro_ano,
        "impacto_anual_estimado": impacto_anual_estimado,
        "retroativo_total": retroativo_total,
        "detalhes_retroativos": detalhes_retroativos
    }

    # 11. Formatar resultados em floats para persistência segura
    dados_origem_json = _serialize_decimals(cenario_atual)
    dados_propostos_json = _serialize_decimals(cenario_proposto)
    resultado_calculo_json = _serialize_decimals(resultado_calculo)

    # Justificativa padrão/mínima
    justificativa = "Servidor apto à promoção automática por tempo."

    # 12. Persistir Simulação e SimulaçãoItem
    nova_simulacao = Simulacao(
        id=uuid4(),
        descricao=f"Simulação Individual - Servidor {servidor.nome}",
        tipo=TipoSimulacao.INDIVIDUAL,
        status=StatusSimulacao.FINALIZADO,
        criado_por_usuario_id=usuario_id,
    )
    db.add(nova_simulacao)
    await db.flush()

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

    # 13. Registrar Auditoria (AuditLog)
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
