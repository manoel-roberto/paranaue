import pytest
from datetime import date
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.api.deps import get_db
from app.core import security
from app.models.usuario import Usuario
from app.models.servidor import Servidor


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


@pytest.mark.asyncio
async def test_acesso_servidores_sem_token_retorna_401():
    """
    Garante que tentativas de listar ou cadastrar servidores sem autenticação
    retornam HTTP 401 Unauthorized.
    """
    transport = ASGITransport(app=app)
    
    # 1. Teste no POST
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_post = await ac.post(
            "/api/v1/servidores",
            json={
                "cpf": "12345678901",
                "nome": "Servidor Teste",
                "data_nascimento": "1990-01-01"
            }
        )
    assert response_post.status_code == 401
    
    # 2. Teste no GET
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_get = await ac.get("/api/v1/servidores")
    assert response_get.status_code == 401


@pytest.mark.asyncio
async def test_cadastro_servidor_sucesso(db_session: AsyncSession, auth_headers: dict):
    """
    Valida que um usuário autenticado pode cadastrar um servidor com CPF válido.
    """
    transport = ASGITransport(app=app)
    cpf_teste = "00000000001"
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/servidores",
            json={
                "cpf": cpf_teste,
                "nome": "Manoel da Silva",
                "data_nascimento": "1985-05-15"
            },
            headers=auth_headers
        )
        
    assert response.status_code == 201
    data = response.json()
    assert data["cpf"] == cpf_teste
    assert data["nome"] == "Manoel da Silva"
    assert data["data_nascimento"] == "1985-05-15"
    assert "id" in data
    
    # Limpeza manual do servidor cadastrado
    stmt = select(Servidor).where(Servidor.cpf == cpf_teste)
    result = await db_session.execute(stmt)
    servidor = result.scalar_one_or_none()
    if servidor:
        await db_session.delete(servidor)
        await db_session.commit()


@pytest.mark.asyncio
async def test_cadastro_servidor_duplicado_retorna_400(db_session: AsyncSession, auth_headers: dict):
    """
    Valida que a tentativa de cadastrar dois servidores com o mesmo CPF retorna HTTP 400.
    """
    transport = ASGITransport(app=app)
    cpf_teste = "00000000002"
    payload = {
        "cpf": cpf_teste,
        "nome": "Antônio Carlos",
        "data_nascimento": "1978-10-22"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Primeiro cadastro: Sucesso
        response_ok = await ac.post(
            "/api/v1/servidores",
            json=payload,
            headers=auth_headers
        )
        assert response_ok.status_code == 201
        
        # Segundo cadastro (mesmo CPF): Erro 400
        response_fail = await ac.post(
            "/api/v1/servidores",
            json=payload,
            headers=auth_headers
        )
        
    assert response_fail.status_code == 400
    assert response_fail.json()["detail"] == "CPF já cadastrado"
    
    # Limpeza manual do servidor cadastrado
    stmt = select(Servidor).where(Servidor.cpf == cpf_teste)
    result = await db_session.execute(stmt)
    servidor = result.scalar_one_or_none()
    if servidor:
        await db_session.delete(servidor)
        await db_session.commit()


@pytest.mark.asyncio
async def test_obter_servidor_sucesso(db_session: AsyncSession, auth_headers: dict):
    """
    Garante que é possível obter um servidor existente pelo ID.
    """
    cpf_teste = "00000000010"
    servidor = Servidor(
        cpf=cpf_teste,
        nome="Servidor de Busca",
        data_nascimento=date(1990, 8, 20)
    )
    db_session.add(servidor)
    await db_session.commit()
    await db_session.refresh(servidor)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/servidores/{servidor.id}",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Servidor de Busca"
    assert data["cpf"] == cpf_teste

    # Limpeza
    await db_session.delete(servidor)
    await db_session.commit()


@pytest.mark.asyncio
async def test_obter_servidor_nao_encontrado(auth_headers: dict):
    """
    Retorna 404 para ID de servidor não existente.
    """
    import uuid
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/servidores/{uuid.uuid4()}",
            headers=auth_headers
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_atualizar_servidor_sucesso(db_session: AsyncSession, auth_headers: dict):
    """
    Valida a atualização dos dados de um servidor com sucesso.
    """
    cpf_teste = "00000000011"
    servidor = Servidor(
        cpf=cpf_teste,
        nome="Servidor Editavel",
        data_nascimento=date(1990, 8, 20)
    )
    db_session.add(servidor)
    await db_session.commit()
    await db_session.refresh(servidor)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put(
            f"/api/v1/servidores/{servidor.id}",
            json={
                "nome": "Servidor Editado Sucesso",
                "cpf": "00000000012"
            },
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Servidor Editado Sucesso"
    assert data["cpf"] == "00000000012"

    # Limpeza
    await db_session.delete(servidor)
    await db_session.commit()


@pytest.mark.asyncio
async def test_atualizar_servidor_duplicado_retorna_400(db_session: AsyncSession, auth_headers: dict):
    """
    Valida que tentar atualizar o CPF para um já existente em outro servidor retorna 400.
    """
    s1 = Servidor(cpf="00000000021", nome="Servidor Um", data_nascimento=date(1980, 1, 1))
    s2 = Servidor(cpf="00000000022", nome="Servidor Dois", data_nascimento=date(1985, 2, 2))
    db_session.add_all([s1, s2])
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put(
            f"/api/v1/servidores/{s1.id}",
            json={"cpf": "00000000022"},
            headers=auth_headers
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "CPF já cadastrado"

    # Limpeza
    await db_session.delete(s1)
    await db_session.delete(s2)
    await db_session.commit()


@pytest.mark.asyncio
async def test_deletar_servidor_sucesso(db_session: AsyncSession, auth_headers: dict):
    """
    Garante que é possível deletar um servidor existente.
    """
    servidor = Servidor(
        cpf="00000000099",
        nome="Servidor a Ser Deletado",
        data_nascimento=date(1995, 12, 1)
    )
    db_session.add(servidor)
    await db_session.commit()
    await db_session.refresh(servidor)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete(
            f"/api/v1/servidores/{servidor.id}",
            headers=auth_headers
        )

    assert response.status_code == 204

    # Garante que não está mais no banco
    stmt = select(Servidor).where(Servidor.id == servidor.id)
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_deletar_servidor_nao_encontrado(auth_headers: dict):
    """
    Retorna 404 ao tentar excluir ID de servidor inexistente.
    """
    import uuid
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete(
            f"/api/v1/servidores/{uuid.uuid4()}",
            headers=auth_headers
        )
    assert response.status_code == 404
