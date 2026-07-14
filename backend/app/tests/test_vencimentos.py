import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.api.deps import get_db
from app.core import security
from app.models.usuario import Usuario, Perfil
from app.models.vencimento_basico import VencimentoBasico
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
    username = "admin_test_user_venc"
    password = "AdminPassword123"
    nome = "Administrador Teste Venc"
    email = "admin_test_venc@uefs.br"
    
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
    username = "rh_test_user_venc"
    password = "RhPassword123"
    nome = "Analista de RH Teste Venc"
    email = "rh_test_venc@uefs.br"
    
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
async def test_fluxo_crud_vencimentos_basicos_sucesso(db_session: AsyncSession, admin_headers: dict, rh_headers: dict):
    transport = ASGITransport(app=app)
    
    # 1. Testar POST (Criar Vencimento Básico com Sucesso - Admin)
    payload = {
        "classe": "Classe Teste S",
        "referencia": "Referencia Teste S",
        "valor": "6200.50"
    }

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/vencimentos",
            json=payload,
            headers=admin_headers
        )

    assert response.status_code == 201
    data = response.json()
    assert data["classe"] == "Classe Teste S"
    assert data["referencia"] == "Referencia Teste S"
    assert data["valor"] == "6200.50"
    venc_id = data["id"]

    # Verificar AuditLog (INSERT)
    stmt_audit = select(AuditLog).where(AuditLog.registro_id == venc_id)
    result_audit = await db_session.execute(stmt_audit)
    audit = result_audit.scalar_one_or_none()
    assert audit is not None
    assert audit.tabela_afetada == "vencimento_basico"
    assert audit.operacao == "INSERT"
    assert audit.payload_novo["classe"] == "Classe Teste S"
    assert audit.payload_novo["valor"] == "6200.50"
    
    # 2. Testar GET (Listar Vencimentos - RH/Qualquer Usuário Autenticado)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_list = await ac.get(
            "/api/v1/vencimentos",
            headers=rh_headers
        )
    assert response_list.status_code == 200
    list_data = response_list.json()
    assert len(list_data) >= 1
    found = [v for v in list_data if v["id"] == venc_id]
    assert len(found) == 1
    assert found[0]["classe"] == "Classe Teste S"

    # 3. Testar GET por ID (Obter Vencimento por ID - RH)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_detail = await ac.get(
            f"/api/v1/vencimentos/{venc_id}",
            headers=rh_headers
        )
    assert response_detail.status_code == 200
    detail_data = response_detail.json()
    assert detail_data["classe"] == "Classe Teste S"
    assert detail_data["valor"] == "6200.50"

    # 4. Testar PUT (Atualizar Vencimento com Sucesso - Admin)
    update_payload = {
        "valor": "6800.75"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_update = await ac.put(
            f"/api/v1/vencimentos/{venc_id}",
            json=update_payload,
            headers=admin_headers
        )
    assert response_update.status_code == 200
    update_data = response_update.json()
    assert update_data["valor"] == "6800.75"

    # Verificar AuditLog (UPDATE)
    stmt_audit_up = select(AuditLog).where(
        AuditLog.registro_id == venc_id,
        AuditLog.operacao == "UPDATE"
    )
    result_audit_up = await db_session.execute(stmt_audit_up)
    audit_up = result_audit_up.scalar_one_or_none()
    assert audit_up is not None
    assert audit_up.payload_antigo["valor"] == "6200.50"
    assert audit_up.payload_novo["valor"] == "6800.75"

    # 5. Testar DELETE (Excluir Vencimento - Admin)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_del = await ac.delete(
            f"/api/v1/vencimentos/{venc_id}",
            headers=admin_headers
        )
    assert response_del.status_code == 204

    # Verificar AuditLog (DELETE)
    stmt_audit_del = select(AuditLog).where(
        AuditLog.registro_id == venc_id,
        AuditLog.operacao == "DELETE"
    )
    result_audit_del = await db_session.execute(stmt_audit_del)
    audit_del = result_audit_del.scalar_one_or_none()
    assert audit_del is not None
    assert audit_del.payload_antigo["valor"] == "6800.75"

    # Confirmar exclusão do banco
    stmt_get_deleted = select(VencimentoBasico).where(VencimentoBasico.id == venc_id)
    res_deleted = await db_session.execute(stmt_get_deleted)
    assert res_deleted.scalar_one_or_none() is None

    # Limpar audit logs gerados
    await db_session.delete(audit)
    await db_session.delete(audit_up)
    await db_session.delete(audit_del)
    await db_session.commit()


@pytest.mark.asyncio
async def test_criar_vencimento_duplicado_erro(db_session: AsyncSession, admin_headers: dict):
    transport = ASGITransport(app=app)
    
    # Criar um primeiro
    payload = {
        "classe": "Classe Unica",
        "referencia": "Referencia Unica",
        "valor": "5000.00"
    }

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res1 = await ac.post(
            "/api/v1/vencimentos",
            json=payload,
            headers=admin_headers
        )
    assert res1.status_code == 201
    venc_id = res1.json()["id"]

    # Tentar criar com a mesma classe e referencia
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res2 = await ac.post(
            "/api/v1/vencimentos",
            json=payload,
            headers=admin_headers
        )
    assert res2.status_code == 400
    assert "Já existe um vencimento básico cadastrado" in res2.json()["detail"]

    # Limpeza
    stmt = select(VencimentoBasico).where(VencimentoBasico.id == venc_id)
    result = await db_session.execute(stmt)
    venc = result.scalar_one()
    
    stmt_audit = select(AuditLog).where(AuditLog.registro_id == venc_id)
    res_audit = await db_session.execute(stmt_audit)
    audit = res_audit.scalar_one()

    await db_session.delete(audit)
    await db_session.delete(venc)
    await db_session.commit()


@pytest.mark.asyncio
async def test_criar_vencimento_valor_invalido_erro(admin_headers: dict):
    transport = ASGITransport(app=app)
    
    # Tentar criar com valor zero
    payload_zero = {
        "classe": "Classe Invalida",
        "referencia": "Ref Invalida",
        "valor": "0.00"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/vencimentos",
            json=payload_zero,
            headers=admin_headers
        )
    assert res.status_code == 422

    # Tentar criar com valor negativo
    payload_neg = {
        "classe": "Classe Invalida",
        "referencia": "Ref Invalida",
        "valor": "-150.00"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/vencimentos",
            json=payload_neg,
            headers=admin_headers
        )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_restricao_acesso_crud_comum_rh(db_session: AsyncSession, admin_headers: dict, rh_headers: dict):
    transport = ASGITransport(app=app)

    # 1. RH tenta criar -> Bloqueado (403)
    payload = {
        "classe": "Classe Acesso",
        "referencia": "Ref Acesso",
        "valor": "3000.00"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_post = await ac.post(
            "/api/v1/vencimentos",
            json=payload,
            headers=rh_headers
        )
    assert res_post.status_code == 403

    # 2. Criar com Admin para testar PUT e DELETE do RH
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_admin = await ac.post(
            "/api/v1/vencimentos",
            json=payload,
            headers=admin_headers
        )
    assert res_admin.status_code == 201
    venc_id = res_admin.json()["id"]

    # 3. RH tenta atualizar -> Bloqueado (403)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_put = await ac.put(
            f"/api/v1/vencimentos/{venc_id}",
            json={"valor": "3500.00"},
            headers=rh_headers
        )
    assert res_put.status_code == 403

    # 4. RH tenta deletar -> Bloqueado (403)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_del = await ac.delete(
            f"/api/v1/vencimentos/{venc_id}",
            headers=rh_headers
        )
    assert res_del.status_code == 403

    # Limpeza
    stmt = select(VencimentoBasico).where(VencimentoBasico.id == venc_id)
    result = await db_session.execute(stmt)
    venc = result.scalar_one()
    
    stmt_audit = select(AuditLog).where(AuditLog.registro_id == venc_id)
    res_audit = await db_session.execute(stmt_audit)
    audit = res_audit.scalar_one()

    await db_session.delete(audit)
    await db_session.delete(venc)
    await db_session.commit()
