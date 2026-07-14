import sys
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core import config

# Se estiver rodando no escopo do pytest, usamos NullPool para evitar que conexões
# abertas no pool fiquem associadas a event loops diferentes entre testes.
if "pytest" in sys.modules:
    pool_config = {"poolclass": pool.NullPool}
else:
    pool_config = {}

# Configura o motor assíncrono do SQLAlchemy
engine = create_async_engine(config.DATABASE_URL, echo=True, **pool_config)

# Configura o gerador de sessões assíncronas
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)
