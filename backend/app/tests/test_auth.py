import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.deps import get_db
from app.core import security
from app.models.usuario import Usuario

@pytest.fixture(autouse=True)
def override_db(db_session: AsyncSession):
    """
    Substitui a dependência get_db do FastAPI pela db_session da fixture do teste,
    garantindo que a API e o teste compartilhem a mesma conexão/transação do banco.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_credenciais_invalidas_retorna_401(db_session: AsyncSession, test_user: Usuario):
    """
    Garante que tentativas de login com senhas inválidas retornam HTTP 401.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "wrong_password_here"
            }
        )
        
    assert response.status_code == 401
    assert response.json()["detail"] == "Usuário ou senha incorretos"


@pytest.mark.asyncio
async def test_login_credenciais_validas_retorna_token(db_session: AsyncSession, test_user: Usuario):
    """
    Garante que login com credenciais corretas retorna HTTP 200 e o token JWT válido.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "SuperSecretPassword123"  # Senha cadastrada na fixture
            }
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expira_em_segundos" in data
