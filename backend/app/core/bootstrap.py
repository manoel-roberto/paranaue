import logging
from sqlalchemy.future import select
from app.core import config
from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.usuario import Usuario, Perfil

# Configuração do logger
logger = logging.getLogger("app.bootstrap")

async def init_initial_data() -> None:
    """
    Inicializa os dados iniciais do sistema de forma idempotente.
    Cria o perfil 'ADMINISTRADOR' se não existir.
    Cria o usuário Master administrador se não existir.
    """
    username = config.settings.ADMIN_USERNAME
    password = config.settings.ADMIN_PASSWORD
    email = config.settings.ADMIN_EMAIL

    if not username or not password or not email:
        logger.warning("Credenciais de administrador não configuradas completamente no ambiente.")
        print("WARNING:  Credenciais de administrador não configuradas completamente no ambiente.")
        return

    async with async_session_maker() as session:
        try:
            # 1. Verifica/cria o perfil 'ADMINISTRADOR'
            stmt_perfil = select(Perfil).where(Perfil.nome == "ADMINISTRADOR")
            result_perfil = await session.execute(stmt_perfil)
            perfil = result_perfil.scalar_one_or_none()

            if not perfil:
                perfil = Perfil(
                    nome="ADMINISTRADOR",
                    descricao="Perfil de Administrador do Sistema"
                )
                session.add(perfil)
                # Flush para obter o ID gerado sem persistir o commit ainda
                await session.flush()

            # 2. Verifica/cria o usuário master
            stmt_usuario = select(Usuario).where(Usuario.username == username)
            result_usuario = await session.execute(stmt_usuario)
            usuario = result_usuario.scalar_one_or_none()

            if not usuario:
                senha_hash = get_password_hash(password)
                usuario = Usuario(
                    username=username,
                    senha_hash=senha_hash,
                    nome="Administrador Master",
                    email=email,
                    ativo=True
                )
                usuario.perfis.append(perfil)
                session.add(usuario)
                await session.commit()
                
                # Exibe nos logs conforme solicitado
                logger.info("Usuário Master inicializado com sucesso")
                print("INFO:     Usuário Master inicializado com sucesso")
            else:
                # Caso o perfil tenha sido adicionado mas o usuário já existia (cenário raro, mas possível)
                await session.commit()
                logger.info("Usuário Master já existente")
                print("INFO:     Usuário Master já existente")
                
        except Exception as e:
            await session.rollback()
            logger.error(f"Erro ao inicializar dados de bootstrap: {e}")
            print(f"ERROR:    Erro ao inicializar dados de bootstrap: {e}")
            raise e
