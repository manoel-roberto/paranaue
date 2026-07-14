import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.api.deps import get_db
from app.core import security
from app.models.usuario import Usuario, Perfil
from app.models.tabelas import TabelaVencimento, TabelaGstu
from app.models.simulacao import AuditLog


@pytest.fixture(autouse=True)
def override_db(db_session: AsyncSession):
    """
    Substitui a dependência get_db do FastAPI pela db_session do teste.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_role(db_session: AsyncSession) -> Perfil:
    stmt = select(Perfil).where(Perfil.nome == "ADMINISTRADOR")
    result = await db_session.execute(stmt)
    perfil = result.scalar_one_or_none()
    if not perfil:
        perfil = Perfil(nome="ADMINISTRADOR", descricao="Administrador Geral")
        db_session.add(perfil)
        await db_session.commit()
        await db_session.refresh(perfil)
    return perfil


@pytest_asyncio.fixture
async def rh_role(db_session: AsyncSession) -> Perfil:
    stmt = select(Perfil).where(Perfil.nome == "ANALISTA_RH")
    result = await db_session.execute(stmt)
    perfil = result.scalar_one_or_none()
    if not perfil:
        perfil = Perfil(nome="ANALISTA_RH", descricao="Analista de RH")
        db_session.add(perfil)
        await db_session.commit()
        await db_session.refresh(perfil)
    return perfil


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, admin_role: Perfil) -> Usuario:
    username = "admin_test_user_param"
    password = "AdminPassword123"
    nome = "Administrador Teste Param"
    email = "admin_test_param@uefs.br"
    
    senha_hash = security.get_password_hash(password)
    user = Usuario(
        username=username,
        senha_hash=senha_hash,
        nome=nome,
        email=email,
        ativo=True
    )
    user.perfis.append(admin_role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    yield user
    
    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest_asyncio.fixture
async def rh_user(db_session: AsyncSession, rh_role: Perfil) -> Usuario:
    username = "rh_test_user_param"
    password = "RhPassword123"
    nome = "Analista de RH Teste Param"
    email = "rh_test_param@uefs.br"
    
    senha_hash = security.get_password_hash(password)
    user = Usuario(
        username=username,
        senha_hash=senha_hash,
        nome=nome,
        email=email,
        ativo=True
    )
    user.perfis.append(rh_role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    yield user
    
    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
def admin_headers(admin_user: Usuario) -> dict:
    token = security.create_access_token(subject=admin_user.username)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def rh_headers(rh_user: Usuario) -> dict:
    token = security.create_access_token(subject=rh_user.username)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_criar_tabela_vencimento_sucesso(db_session: AsyncSession, admin_headers: dict):
    transport = ASGITransport(app=app)
    payload = {
        "codigo_vencimento": "VENC_TEST_01",
        "classe": "TST_CL_SUC",
        "nivel_grau": "TST_NV_SUC",
        "carga_horaria": 40,
        "valor_base": "5500.50",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-12-31"
    }

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/parametros/vencimento",
            json=payload,
            headers=admin_headers
        )

    assert response.status_code == 201
    data = response.json()
    assert data["codigo_vencimento"] == "VENC_TEST_01"
    assert data["classe"] == "TST_CL_SUC"
    assert data["valor_base"] == "5500.50"

    # Verifica o AuditLog correspondente
    stmt_audit = select(AuditLog).where(AuditLog.registro_id == data["id"])
    result_audit = await db_session.execute(stmt_audit)
    audit = result_audit.scalar_one_or_none()
    assert audit is not None
    assert audit.tabela_afetada == "tabela_vencimento"
    assert audit.operacao == "INSERT"
    assert audit.payload_novo is not None

    # Cleanup
    stmt = select(TabelaVencimento).where(TabelaVencimento.codigo_vencimento == "VENC_TEST_01")
    result = await db_session.execute(stmt)
    tabela = result.scalar_one_or_none()
    if tabela:
        await db_session.delete(audit)
        await db_session.delete(tabela)
        await db_session.commit()


@pytest.mark.asyncio
async def test_criar_tabela_gstu_sucesso(db_session: AsyncSession, admin_headers: dict):
    transport = ASGITransport(app=app)
    payload = {
        "codigo_gstu": "GSTU_TEST_01",
        "grau": "TST_GR_SUC",
        "referencia": "TST_RF_SUC",
        "valor_gstu": "1250.75",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-12-31"
    }

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/parametros/gstu",
            json=payload,
            headers=admin_headers
        )

    assert response.status_code == 201
    data = response.json()
    assert data["codigo_gstu"] == "GSTU_TEST_01"
    assert data["grau"] == "TST_GR_SUC"
    assert data["valor_gstu"] == "1250.75"

    # Verifica o AuditLog correspondente
    stmt_audit = select(AuditLog).where(AuditLog.registro_id == data["id"])
    result_audit = await db_session.execute(stmt_audit)
    audit = result_audit.scalar_one_or_none()
    assert audit is not None
    assert audit.tabela_afetada == "tabela_gstu"
    assert audit.operacao == "INSERT"

    # Cleanup
    stmt = select(TabelaGstu).where(TabelaGstu.codigo_gstu == "GSTU_TEST_01")
    result = await db_session.execute(stmt)
    tabela = result.scalar_one_or_none()
    if tabela:
        await db_session.delete(audit)
        await db_session.delete(tabela)
        await db_session.commit()


@pytest.mark.asyncio
async def test_criar_tabela_sem_permissao_retorna_403(rh_headers: dict):
    transport = ASGITransport(app=app)
    
    # Usuário ANALISTA_RH tenta criar Vencimento
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_venc = await ac.post(
            "/api/v1/parametros/vencimento",
            json={
                "codigo_vencimento": "VENC_RH",
                "classe": "TST_CL_RH",
                "nivel_grau": "TST_NV_RH",
                "carga_horaria": 40,
                "valor_base": "3000.00",
                "data_inicio_vigencia": "2026-01-01",
                "data_fim_vigencia": "2026-12-31"
            },
            headers=rh_headers
        )
    assert response_venc.status_code == 403

    # Usuário ANALISTA_RH tenta criar GSTU
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_gstu = await ac.post(
            "/api/v1/parametros/gstu",
            json={
                "codigo_gstu": "GSTU_RH",
                "grau": "TST_GR_RH",
                "referencia": "TST_RF_RH",
                "valor_gstu": "800.00",
                "data_inicio_vigencia": "2026-01-01",
                "data_fim_vigencia": "2026-12-31"
            },
            headers=rh_headers
        )
    assert response_gstu.status_code == 403


@pytest.mark.asyncio
async def test_criar_tabela_datas_invalidas_retorna_422(admin_headers: dict):
    transport = ASGITransport(app=app)
    # Fim da vigência anterior ao início
    payload = {
        "codigo_vencimento": "VENC_INV_DATE",
        "classe": "TST_CL_INV",
        "nivel_grau": "TST_NV_INV",
        "carga_horaria": 40,
        "valor_base": "5000.00",
        "data_inicio_vigencia": "2026-12-31",
        "data_fim_vigencia": "2026-01-01"
    }

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/parametros/vencimento",
            json=payload,
            headers=admin_headers
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_tabela_valores_invalidos_retorna_422(admin_headers: dict):
    transport = ASGITransport(app=app)
    
    # 1. Valor base negativo
    payload_val_neg = {
        "codigo_vencimento": "VENC_INV_VAL",
        "classe": "TST_CL_VAL",
        "nivel_grau": "TST_NV_VAL",
        "carga_horaria": 40,
        "valor_base": "-10.00",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-12-31"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/parametros/vencimento",
            json=payload_val_neg,
            headers=admin_headers
        )
    assert response.status_code == 422

    # 2. Carga horária negativa/zero
    payload_ch_zero = {
        "codigo_vencimento": "VENC_INV_CH",
        "classe": "TST_CL_CH",
        "nivel_grau": "TST_NV_CH",
        "carga_horaria": 0,
        "valor_base": "5000.00",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-12-31"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/parametros/vencimento",
            json=payload_ch_zero,
            headers=admin_headers
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_tabela_vencimento_sobreposta_retorna_400(db_session: AsyncSession, admin_headers: dict):
    transport = ASGITransport(app=app)
    
    # Cadastra o primeiro registro com sucesso
    payload1 = {
        "codigo_vencimento": "VENC_SOB_01",
        "classe": "TST_CL_SOB",
        "nivel_grau": "TST_NV_SOB",
        "carga_horaria": 40,
        "valor_base": "5000.00",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-12-31"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response1 = await ac.post(
            "/api/v1/parametros/vencimento",
            json=payload1,
            headers=admin_headers
        )
    assert response1.status_code == 201
    id1 = response1.json()["id"]

    # Tenta cadastrar um segundo com vigência sobreposta
    payload2 = {
        "codigo_vencimento": "VENC_SOB_02",
        "classe": "TST_CL_SOB",  # Mesma classe
        "nivel_grau": "TST_NV_SOB", # Mesmo nível
        "carga_horaria": 40,     # Mesma carga horária
        "valor_base": "5200.00",
        "data_inicio_vigencia": "2026-06-01",  # Sobrepõe com [2026-01-01, 2026-12-31]
        "data_fim_vigencia": "2027-06-01"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response2 = await ac.post(
            "/api/v1/parametros/vencimento",
            json=payload2,
            headers=admin_headers
        )
    assert response2.status_code == 400
    assert "sobreposta" in response2.json()["detail"]

    # Tenta cadastrar para classe/nível diferente ou carga horária diferente (deve permitir)
    payload_ok = {
        "codigo_vencimento": "VENC_SOB_OK",
        "classe": "TST_CL_SOB",
        "nivel_grau": "TST_NV_SOB",
        "carga_horaria": 20,     # Carga horária diferente, deve permitir!
        "valor_base": "2500.00",
        "data_inicio_vigencia": "2026-06-01",
        "data_fim_vigencia": "2026-12-31"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_ok = await ac.post(
            "/api/v1/parametros/vencimento",
            json=payload_ok,
            headers=admin_headers
        )
    assert response_ok.status_code == 201
    id_ok = response_ok.json()["id"]

    # Cleanup
    stmt = select(TabelaVencimento).where(TabelaVencimento.id.in_([id1, id_ok]))
    result = await db_session.execute(stmt)
    tabelas = result.scalars().all()
    for t in tabelas:
        # Apaga os logs de auditoria correspondentes primeiro
        stmt_audit = select(AuditLog).where(AuditLog.registro_id == t.id)
        res_audit = await db_session.execute(stmt_audit)
        audit = res_audit.scalar_one_or_none()
        if audit:
            await db_session.delete(audit)
        await db_session.delete(t)
    await db_session.commit()


@pytest.mark.asyncio
async def test_listar_tabelas_sucesso(db_session: AsyncSession, admin_headers: dict, rh_headers: dict):
    transport = ASGITransport(app=app)
    
    # 1. Cadastra referências de Vencimento e GSTU
    venc_payload = {
        "codigo_vencimento": "VENC_LIST_01",
        "classe": "TST_CL_LIS",
        "nivel_grau": "TST_NV_LIS",
        "carga_horaria": 40,
        "valor_base": "6000.00",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-12-31"
    }
    gstu_payload = {
        "codigo_gstu": "GSTU_LIST_01",
        "grau": "TST_GR_LIS",
        "referencia": "TST_RF_LIS",
        "valor_gstu": "1500.00",
        "data_inicio_vigencia": "2026-01-01",
        "data_fim_vigencia": "2026-12-31"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_v = await ac.post("/api/v1/parametros/vencimento", json=venc_payload, headers=admin_headers)
        res_g = await ac.post("/api/v1/parametros/gstu", json=gstu_payload, headers=admin_headers)
        
    assert res_v.status_code == 201
    assert res_g.status_code == 201
    v_id = res_v.json()["id"]
    g_id = res_g.json()["id"]

    # 2. Usuário com perfil ANALISTA_RH lista os parâmetros
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        list_v = await ac.get("/api/v1/parametros/vencimento", headers=rh_headers)
        list_g = await ac.get("/api/v1/parametros/gstu", headers=rh_headers)

    assert list_v.status_code == 200
    assert any(item["id"] == v_id for item in list_v.json())
    
    assert list_g.status_code == 200
    assert any(item["id"] == g_id for item in list_g.json())

    # Cleanup
    t_v = await db_session.get(TabelaVencimento, v_id)
    t_g = await db_session.get(TabelaGstu, g_id)
    for t in [t_v, t_g]:
        if t:
            stmt_audit = select(AuditLog).where(AuditLog.registro_id == t.id)
            res_audit = await db_session.execute(stmt_audit)
            audit = res_audit.scalar_one_or_none()
            if audit:
                await db_session.delete(audit)
            await db_session.delete(t)
    await db_session.commit()
