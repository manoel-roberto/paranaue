import asyncio
import os
import sys
import socket
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Adiciona o diretório do backend ao sys.path para carregar 'app' corretamente
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.models.base import Base
# Importa o módulo de modelos para registrar as entidades no metadado
import app.models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_database_url():
    # Carrega a DATABASE_URL do arquivo .env.local na mesma pasta
    env_path = os.path.join(backend_dir, ".env.local")
    url = None
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        if key.strip() == "DATABASE_URL":
                            url = val.strip()
                            break
    if not url:
        url = os.environ.get("DATABASE_URL")
        
    # Tratamento dinâmico para ambiente de sandbox
    if url and ("localhost" in url or "127.0.0.1" in url):
        try:
            # Extrai a porta
            parts = url.split("@")[-1].split("/")[0].split(":")
            port = int(parts[1]) if len(parts) > 1 else 5432
            
            # Testa localhost
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            s.close()
        except Exception:
            # Localhost falhou. Testa o gateway da ponte do Docker (172.18.0.1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(("172.18.0.1", port))
                s.close()
                url = url.replace("localhost", "172.18.0.1").replace("127.0.0.1", "172.18.0.1")
                print(f"INFO (Alembic): Redirecionando conexao de localhost para 172.18.0.1 (Sandbox)")
            except Exception:
                pass
                
    return url

# Injeta a DATABASE_URL dinâmica carregada
db_url = get_database_url()
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# MetaData object para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
