import pytest
import pytest_asyncio
import asyncio
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core import security
from app.models.usuario import Usuario

@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture que gerencia o loop de eventos asyncio para a sessão de testes.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture que fornece uma sessão assíncrona do banco de dados para os testes.
    """
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> Usuario:
    """
    Fixture que cria um usuário de teste temporário no banco de dados para os testes de integração.
    """
    username = "auth_test_user"
    password = "SuperSecretPassword123"
    nome = "Usuário Teste Auth"
    email = "auth_test@uefs.br"
    
    senha_hash = security.get_password_hash(password)
    user = Usuario(
        username=username,
        senha_hash=senha_hash,
        nome=nome,
        email=email,
        ativo=True
    )
    
    db_session.add(user)
    await db_session.commit()
    yield user
    
    # Cleanup
    await db_session.delete(user)
    await db_session.commit()

