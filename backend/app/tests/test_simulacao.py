import pytest
import pytest_asyncio
from datetime import date
from uuid import UUID, uuid4
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.api.deps import get_db
from app.core import security
from app.core.database import async_session_maker
from app.models.usuario import Usuario
from app.models.servidor import (
    Servidor,
    Cargo,
    Vinculo,
    Averbacao,
    TipoAverbacao,
    RegimePrevidenciario,
    TipoVinculo,
    TipoCargo,
)
from app.models.tabelas import (
    TabelaVencimento,
    TabelaGstu,
    TabelaComissao,
    HistoricoFuncional,
)
from app.models.simulacao import AuditLog, Simulacao, SimulacaoItem


@pytest.fixture(autouse=True)
def override_db(db_session: AsyncSession):
    """
    Substitui a dependência get_db do FastAPI pela db_session do teste.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user: Usuario) -> dict:
    """
    Gera o cabeçalho de autenticação Bearer JWT para o usuário de teste.
    """
    token = security.create_access_token(subject=test_user.username)
    return {"Authorization": f"Bearer {token}"}


async def cleanup_test_data(session: AsyncSession):
    """
    Remove de forma robusta e ordenada qualquer dado de teste remanescente.
    """
    # 1. Buscar o usuário de teste e limpar dados relacionados
    stmt_user = select(Usuario).where(Usuario.username == "auth_test_user")
    res_user = await session.execute(stmt_user)
    user = res_user.scalar_one_or_none()

    if user:
        stmt_audit = select(AuditLog).where(AuditLog.usuario_id == user.id)
        res_audit = await session.execute(stmt_audit)
        for audit in res_audit.scalars().all():
            await session.delete(audit)

        stmt_sim = select(Simulacao).where(Simulacao.criado_por_usuario_id == user.id)
        res_sim = await session.execute(stmt_sim)
        for sim in res_sim.scalars().all():
            stmt_items = select(SimulacaoItem).where(SimulacaoItem.simulacao_id == sim.id)
            res_items = await session.execute(stmt_items)
            for item in res_items.scalars().all():
                await session.delete(item)
            await session.delete(sim)

    # 2. Remover servidores e seus vínculos
    for cpf in ["99999999999", "88888888888"]:
        stmt_serv = select(Servidor).where(Servidor.cpf == cpf)
        res_serv = await session.execute(stmt_serv)
        serv = res_serv.scalar_one_or_none()
        if serv:
            stmt_vincs = select(Vinculo).where(Vinculo.servidor_id == serv.id)
            res_vincs = await session.execute(stmt_vincs)
            for v in res_vincs.scalars().all():
                stmt_items = select(SimulacaoItem).where(SimulacaoItem.vinculo_id == v.id)
                res_items = await session.execute(stmt_items)
                for item in res_items.scalars().all():
                    await session.delete(item)

                stmt_hist = select(HistoricoFuncional).where(HistoricoFuncional.vinculo_id == v.id)
                res_hist = await session.execute(stmt_hist)
                for h in res_hist.scalars().all():
                    await session.delete(h)

                stmt_averb = select(Averbacao).where(Averbacao.vinculo_id == v.id)
                res_averb = await session.execute(stmt_averb)
                for a in res_averb.scalars().all():
                    await session.delete(a)

                await session.delete(v)
            await session.delete(serv)

    # 3. Remover tabelas paramétricas de teste
    for cod in ["VENC_ATUAL", "VENC_PROPOSTO"]:
        stmt = select(TabelaVencimento).where(TabelaVencimento.codigo_vencimento == cod)
        res = await session.execute(stmt)
        for tab in res.scalars().all():
            await session.delete(tab)

    for cod in ["GSTU_ATUAL", "GSTU_PROPOSTO"]:
        stmt = select(TabelaGstu).where(TabelaGstu.codigo_gstu == cod)
        res = await session.execute(stmt)
        for tab in res.scalars().all():
            await session.delete(tab)

    stmt = select(TabelaComissao).where(TabelaComissao.simbolo == "DAS-1")
    res = await session.execute(stmt)
    for tab in res.scalars().all():
        await session.delete(tab)

    stmt_cargo = select(Cargo).where(Cargo.nome == "Cargo Teste Simulação")
    res_cargo = await session.execute(stmt_cargo)
    for cargo in res_cargo.scalars().all():
        await session.delete(cargo)

    # 4. Remover o próprio usuário de teste
    if user:
        await session.delete(user)

    await session.commit()


@pytest_asyncio.fixture(scope="module", autouse=True)
async def cleanup_database_module():
    """
    Fixture autouse no escopo do módulo para garantir que o banco esteja limpo
    antes e depois da execução dos testes do módulo.
    """
    async with async_session_maker() as session:
        await cleanup_test_data(session)
    yield
    async with async_session_maker() as session:
        await cleanup_test_data(session)


@pytest.mark.asyncio
async def test_fluxo_completo_simulacao_impacto(db_session: AsyncSession, auth_headers: dict, test_user: Usuario):
    try:
        # 1. Arrange: Criar a massa de dados necessária para o teste
        # a) Criar Servidor
        servidor = Servidor(
            cpf="99999999999",
            nome="Servidor Teste Simulação",
            data_nascimento=date(1990, 1, 1),
        )
        db_session.add(servidor)
        await db_session.flush()

        # b) Criar Cargo
        cargo = Cargo(
            nome="Cargo Teste Simulação",
            tipo=TipoCargo.TECNICO,
            carga_horaria_padrao=40,
        )
        db_session.add(cargo)
        await db_session.flush()

        # c) Criar Vínculo Ativo (Admissão em 2020-01-01)
        vinculo = Vinculo(
            servidor_id=servidor.id,
            matricula="MATR-SIMULACAO-01",
            data_admissao=date(2020, 1, 1),
            cargo_id=cargo.id,
            regime_previdenciario=RegimePrevidenciario.BAPREV_REGIME_PROPRIO,
            participante_prev_complementar=False,
            tipo_vinculo=TipoVinculo.ESTATUTARIO,
            ativo=True,
        )
        db_session.add(vinculo)
        await db_session.flush()

        # d) Criar Averbacão de ATS (365 dias)
        averbacao = Averbacao(
            vinculo_id=vinculo.id,
            dias_averbados=365,
            tipo_averbacao=TipoAverbacao.ATS,
            data_averbacao=date(2022, 1, 1),
            processo_numero="PROC-ATS-123",
        )
        db_session.add(averbacao)
        await db_session.flush()

        # e) Criar Tabelas Paramétricas Atuais e Propostas
        # Vencimento Atual: 4000.00
        vencimento_atual = TabelaVencimento(
            codigo_vencimento="VENC_ATUAL",
            classe="CLASSE_A",
            nivel_grau="NIVEL_1",
            carga_horaria=40,
            valor_base=4000.00,
            data_inicio_vigencia=date(2020, 1, 1),
        )
        # Vencimento Proposto: 5000.00
        vencimento_proposto = TabelaVencimento(
            codigo_vencimento="VENC_PROPOSTO",
            classe="CLASSE_B",
            nivel_grau="NIVEL_2",
            carga_horaria=40,
            valor_base=5000.00,
            data_inicio_vigencia=date(2020, 1, 1),
        )
        # GSTU Atual: 1000.00
        gstu_atual = TabelaGstu(
            codigo_gstu="GSTU_ATUAL",
            grau="GRAU_1",
            referencia="REF_1",
            valor_gstu=1000.00,
            data_inicio_vigencia=date(2020, 1, 1),
        )
        # GSTU Proposto: 1200.00
        gstu_proposto = TabelaGstu(
            codigo_gstu="GSTU_PROPOSTO",
            grau="GRAU_2",
            referencia="REF_2",
            valor_gstu=1200.00,
            data_inicio_vigencia=date(2020, 1, 1),
        )
        # Comissão (para Estabilidade): 1500.00
        comissao = TabelaComissao(
            simbolo="DAS-1",
            valor_comissao=1500.00,
            data_inicio_vigencia=date(2020, 1, 1),
        )
        db_session.add_all([vencimento_atual, vencimento_proposto, gstu_atual, gstu_proposto, comissao])
        await db_session.flush()

        # f) Criar histórico funcional ativo
        historico = HistoricoFuncional(
            vinculo_id=vinculo.id,
            data_inicio=date(2020, 1, 1),
            data_fim=date(9999, 12, 31),
            tabela_vencimento_id=vencimento_atual.id,
            tabela_gstu_id=gstu_atual.id,
            cet_percentual=10.00,
            insalubridade_percentual=20.00,
            vpess_valor=300.00,
            tabela_comissao_id=comissao.id,
            percentual_estabilizado=30.00,
        )
        db_session.add(historico)
        await db_session.commit()

        # 2. Act: Executar a chamada POST para o endpoint de simulação
        transport = ASGITransport(app=app)
        payload = {
            "servidor_id": str(servidor.id),
            "novo_vencimento_id": str(vencimento_proposto.id),
            "novo_gstu_id": str(gstu_proposto.id),
            "data_vigencia": "2026-01-01",
            "mes_ferias": 6,
        }

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response_post = await ac.post(
                "/api/v1/simulacao",
                json=payload,
                headers=auth_headers
            )

        # 3. Assert: Verificar o retorno da simulação
        assert response_post.status_code == 201, response_post.text
        data_post = response_post.json()

        assert "id" in data_post
        assert data_post["servidor_id"] == str(servidor.id)
        assert data_post["justificativa"] == "Servidor apto à promoção automática por tempo."

        res_json = data_post["resultado_calculo_json"]
        assert abs(res_json["impacto_financeiro_bruto"] - 1570.00) < 0.01
        assert abs(res_json["percentual_impacto"] - 21.715) < 0.1

        # 4. Act & Assert: Buscar a simulação via GET
        sim_id = data_post["id"]
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response_get = await ac.get(
                f"/api/v1/simulacao/{sim_id}",
                headers=auth_headers
            )
        assert response_get.status_code == 200
        data_get = response_get.json()
        assert data_get["id"] == sim_id
        assert data_get["servidor_id"] == str(servidor.id)
        assert abs(data_get["resultado_calculo_json"]["impacto_financeiro_bruto"] - 1570.00) < 0.01

        # 5. Assert: Verificar se o AuditLog de simulação foi criado
        stmt_audit = select(AuditLog).where(
            AuditLog.registro_id == (
                select(Simulacao.id).where(Simulacao.criado_por_usuario_id == test_user.id).scalar_subquery()
            )
        )
        result_audit = await db_session.execute(stmt_audit)
        audit = result_audit.scalar_one_or_none()
        assert audit is not None
        assert audit.tabela_afetada == "simulacao"
        assert audit.operacao == "SIMULACAO_EXECUCAO"
        assert audit.payload_novo is not None

        # 6. Act & Assert: Buscar a exportação em PDF da simulação
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response_pdf = await ac.get(
                f"/api/v1/simulacao/{sim_id}/pdf",
                headers=auth_headers
            )
        assert response_pdf.status_code == 200
        assert response_pdf.headers["content-type"] == "application/pdf"
        assert f"attachment; filename=simulacao_{sim_id}.pdf" in response_pdf.headers["content-disposition"]
        assert len(response_pdf.content) > 0

    finally:
        # Limpeza local do teste para evitar problemas de integridade de chave estrangeira
        # antes que a fixture test_user faça o delete/commit dela.
        stmt_sim = select(Simulacao).where(Simulacao.criado_por_usuario_id == test_user.id)
        res_sim = await db_session.execute(stmt_sim)
        sims = res_sim.scalars().all()
        for sim in sims:
            stmt_items = select(SimulacaoItem).where(SimulacaoItem.simulacao_id == sim.id)
            res_items = await db_session.execute(stmt_items)
            for item in res_items.scalars().all():
                await db_session.delete(item)
            stmt_audit = select(AuditLog).where(AuditLog.registro_id == sim.id)
            res_audit = await db_session.execute(stmt_audit)
            for audit in res_audit.scalars().all():
                await db_session.delete(audit)
            await db_session.delete(sim)

        # Deletar servidor e relacionamentos
        stmt_serv = select(Servidor).where(Servidor.cpf == "99999999999")
        res_serv = await db_session.execute(stmt_serv)
        serv = res_serv.scalar_one_or_none()
        if serv:
            stmt_vincs = select(Vinculo).where(Vinculo.servidor_id == serv.id)
            res_vincs = await db_session.execute(stmt_vincs)
            for v in res_vincs.scalars().all():
                stmt_hist = select(HistoricoFuncional).where(HistoricoFuncional.vinculo_id == v.id)
                res_hist = await db_session.execute(stmt_hist)
                for h in res_hist.scalars().all():
                    await db_session.delete(h)

                stmt_averb = select(Averbacao).where(Averbacao.vinculo_id == v.id)
                res_averb = await db_session.execute(stmt_averb)
                for a in res_averb.scalars().all():
                    await db_session.delete(a)

                await db_session.delete(v)
            await db_session.delete(serv)

        # Deletar tabelas paramétricas
        for cod in ["VENC_ATUAL", "VENC_PROPOSTO"]:
            stmt = select(TabelaVencimento).where(TabelaVencimento.codigo_vencimento == cod)
            res = await db_session.execute(stmt)
            for tab in res.scalars().all():
                await db_session.delete(tab)

        for cod in ["GSTU_ATUAL", "GSTU_PROPOSTO"]:
            stmt = select(TabelaGstu).where(TabelaGstu.codigo_gstu == cod)
            res = await db_session.execute(stmt)
            for tab in res.scalars().all():
                await db_session.delete(tab)

        stmt = select(TabelaComissao).where(TabelaComissao.simbolo == "DAS-1")
        res = await db_session.execute(stmt)
        for tab in res.scalars().all():
            await db_session.delete(tab)

        stmt_cargo = select(Cargo).where(Cargo.nome == "Cargo Teste Simulação")
        res_cargo = await db_session.execute(stmt_cargo)
        for cargo in res_cargo.scalars().all():
            await db_session.delete(cargo)

        await db_session.commit()


@pytest.mark.asyncio
async def test_simulacao_servidor_sem_vinculo_ativo(db_session: AsyncSession, auth_headers: dict):
    try:
        # Criar servidor sem vínculo
        servidor = Servidor(
            cpf="88888888888",
            nome="Servidor Sem Vínculo",
            data_nascimento=date(1990, 1, 1),
        )
        db_session.add(servidor)
        await db_session.commit()

        # Tentar rodar simulação
        transport = ASGITransport(app=app)
        payload = {
            "servidor_id": str(servidor.id),
            "novo_vencimento_id": "00000000-0000-0000-0000-000000000000",
            "novo_gstu_id": None,
            "data_vigencia": "2026-01-01",
            "mes_ferias": 1,
        }

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/simulacao",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 400
        assert "vínculo ativo" in response.json()["detail"]

    finally:
        stmt_serv = select(Servidor).where(Servidor.cpf == "88888888888")
        res_serv = await db_session.execute(stmt_serv)
        serv = res_serv.scalar_one_or_none()
        if serv:
            await db_session.delete(serv)
            await db_session.commit()
