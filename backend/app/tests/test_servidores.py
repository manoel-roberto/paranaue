import pytest
from datetime import date
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from sqlalchemy.future import select

from app.main import app
from app.api.deps import get_db
from app.core import security
from app.models.usuario import Usuario
from app.models.servidor import Servidor, Cargo, Vinculo, RegimePrevidenciario, TipoVinculo, TipoCargo
from app.models.tabelas import HistoricoFuncional, TabelaVencimento


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


@pytest.mark.asyncio
async def test_criar_e_listar_vinculo_sucesso(db_session: AsyncSession, auth_headers: dict):
    """
    Testa o fluxo de cadastro e listagem de vínculos de um servidor.
    """
    # Limpeza prévia
    await db_session.execute(delete(Vinculo).where(Vinculo.matricula == "MATR-VINC-01"))
    await db_session.execute(delete(Servidor).where(Servidor.cpf == "00000000030"))
    await db_session.execute(delete(Cargo).where(Cargo.nome == "Cargo Vínculos"))
    await db_session.commit()

    # Arrange
    servidor = Servidor(cpf="00000000030", nome="Servidor Vínculos", data_nascimento=date(1990, 1, 1))
    cargo = Cargo(nome="Cargo Vínculos", tipo=TipoCargo.TECNICO, carga_horaria_padrao=30)
    db_session.add_all([servidor, cargo])
    await db_session.commit()

    transport = ASGITransport(app=app)
    
    # Act - criar vínculo
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_create = await ac.post(
            f"/api/v1/servidores/{servidor.id}/vinculos",
            json={
                "matricula": "MATR-VINC-01",
                "data_admissao": "2020-01-01",
                "cargo_id": str(cargo.id),
                "regime_previdenciario": "BAPREV_REGIME_PROPRIO",
                "participante_prev_complementar": False,
                "aliquota_coparticipacao_complementar": 0.00,
                "tipo_vinculo": "ESTATUTARIO",
                "ativo": True,
            },
            headers=auth_headers
        )
    
    assert response_create.status_code == 201
    data_create = response_create.json()
    assert data_create["matricula"] == "MATR-VINC-01"

    # Act - listar vínculos
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_list = await ac.get(
            f"/api/v1/servidores/{servidor.id}/vinculos",
            headers=auth_headers
        )
        
    assert response_list.status_code == 200
    data_list = response_list.json()
    assert len(data_list) == 1
    assert data_list[0]["matricula"] == "MATR-VINC-01"

    # Cleanup
    stmt_v = select(Vinculo).where(Vinculo.servidor_id == servidor.id)
    res_v = await db_session.execute(stmt_v)
    for v in res_v.scalars().all():
        await db_session.delete(v)
    await db_session.delete(servidor)
    await db_session.delete(cargo)
    await db_session.commit()


@pytest.mark.asyncio
async def test_criar_historico_funcional_sucesso_e_sobreposicao(db_session: AsyncSession, auth_headers: dict):
    """
    Testa o fluxo de cadastro de histórico funcional e validação de sobreposição temporal.
    """
    # Limpeza prévia
    await db_session.execute(delete(HistoricoFuncional).where(HistoricoFuncional.vinculo.has(Vinculo.matricula == "MATR-HIST-01")))
    await db_session.execute(delete(Vinculo).where(Vinculo.matricula == "MATR-HIST-01"))
    await db_session.execute(delete(Servidor).where(Servidor.cpf == "00000000035"))
    await db_session.execute(delete(Cargo).where(Cargo.nome == "Cargo Histórico"))
    await db_session.execute(delete(TabelaVencimento).where(TabelaVencimento.codigo_vencimento.in_(["V-TEST-1", "V-TEST-2"])))
    await db_session.commit()

    # Arrange
    servidor = Servidor(cpf="00000000035", nome="Servidor Histórico", data_nascimento=date(1990, 1, 1))
    cargo = Cargo(nome="Cargo Histórico", tipo=TipoCargo.ANALISTA, carga_horaria_padrao=40)
    venc1 = TabelaVencimento(codigo_vencimento="V-TEST-1", classe="A", nivel_grau="I", carga_horaria=40, valor_base=3000.00, data_inicio_vigencia=date(2020, 1, 1))
    venc2 = TabelaVencimento(codigo_vencimento="V-TEST-2", classe="A", nivel_grau="II", carga_horaria=40, valor_base=3500.00, data_inicio_vigencia=date(2020, 1, 1))
    db_session.add_all([servidor, cargo, venc1, venc2])
    await db_session.commit()

    vinculo = Vinculo(
        servidor_id=servidor.id,
        matricula="MATR-HIST-01",
        data_admissao=date(2020, 1, 1),
        cargo_id=cargo.id,
        regime_previdenciario=RegimePrevidenciario.BAPREV_REGIME_PROPRIO,
        participante_prev_complementar=False,
        tipo_vinculo=TipoVinculo.ESTATUTARIO,
        ativo=True,
    )
    db_session.add(vinculo)
    await db_session.commit()

    transport = ASGITransport(app=app)
    
    # Act - criar primeiro histórico (vigência indefinida 2020-01-01 a 9999-12-31)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res1 = await ac.post(
            f"/api/v1/servidores/vinculos/{vinculo.id}/historico",
            json={
                "data_inicio": "2020-01-01",
                "data_fim": "9999-12-31",
                "tabela_vencimento_id": str(venc1.id),
                "cet_percentual": 0.00,
                "insalubridade_percentual": 0.00,
                "vpess_valor": 0.00,
                "percentual_estabilizado": 0.00,
            },
            headers=auth_headers
        )
    assert res1.status_code == 201
    
    # Act - criar segundo histórico (a partir de 2022-01-01)
    # Isso deve fechar o primeiro histórico em 2021-12-31 automaticamente
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res2 = await ac.post(
            f"/api/v1/servidores/vinculos/{vinculo.id}/historico",
            json={
                "data_inicio": "2022-01-01",
                "data_fim": "9999-12-31",
                "tabela_vencimento_id": str(venc2.id),
                "cet_percentual": 10.00,
                "insalubridade_percentual": 20.00,
                "vpess_valor": 0.00,
                "percentual_estabilizado": 0.00,
            },
            headers=auth_headers
        )
    assert res2.status_code == 201

    # Verificar se o primeiro foi fechado no banco
    stmt_h = select(HistoricoFuncional).where(HistoricoFuncional.tabela_vencimento_id == venc1.id)
    res_h = await db_session.execute(stmt_h)
    h1 = res_h.scalar_one_or_none()
    assert h1 is not None
    assert h1.data_fim == date(2021, 12, 31)

    # Act - tentar inserir um histórico que colide (ex: 2021-06-01 a 2021-12-01)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_fail = await ac.post(
            f"/api/v1/servidores/vinculos/{vinculo.id}/historico",
            json={
                "data_inicio": "2021-06-01",
                "data_fim": "2021-12-01",
                "tabela_vencimento_id": str(venc1.id),
                "cet_percentual": 0.00,
                "insalubridade_percentual": 0.00,
                "vpess_valor": 0.00,
                "percentual_estabilizado": 0.00,
            },
            headers=auth_headers
        )
    assert res_fail.status_code == 400
    assert "sobrepõe" in res_fail.json()["detail"]

    # Cleanup
    stmt_all_h = select(HistoricoFuncional).where(HistoricoFuncional.vinculo_id == vinculo.id)
    res_all_h = await db_session.execute(stmt_all_h)
    for h in res_all_h.scalars().all():
        await db_session.delete(h)
    await db_session.delete(vinculo)
    await db_session.delete(servidor)
    await db_session.delete(cargo)
    await db_session.delete(venc1)
    await db_session.delete(venc2)
    await db_session.commit()
