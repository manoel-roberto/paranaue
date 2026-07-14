import pytest
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core import config
from app.core.bootstrap import init_initial_data
from app.models.usuario import Usuario, Perfil

@pytest.mark.asyncio
async def test_bootstrap_initial_data(db_session: AsyncSession):
    # Salva os valores originais para restaurar no final
    orig_username = config.settings.ADMIN_USERNAME
    orig_password = config.settings.ADMIN_PASSWORD
    orig_email = config.settings.ADMIN_EMAIL

    # Define credenciais específicas de teste
    test_admin_username = "temp_bootstrap_admin"
    test_admin_password = "temp_bootstrap_password"
    test_admin_email = "temp_bootstrap@example.com"

    config.settings.ADMIN_USERNAME = test_admin_username
    config.settings.ADMIN_PASSWORD = test_admin_password
    config.settings.ADMIN_EMAIL = test_admin_email

    # Garante um estado limpo removendo resíduos de execuções anteriores falhas
    stmt_clean = select(Usuario).options(selectinload(Usuario.perfis)).where(Usuario.username == test_admin_username)
    res_clean = await db_session.execute(stmt_clean)
    user_clean = res_clean.scalar_one_or_none()
    if user_clean:
        user_clean.perfis.clear()
        await db_session.delete(user_clean)
        await db_session.commit()

    try:
        # Garante que o usuário de teste não existe antes do bootstrap
        stmt_user = select(Usuario).where(Usuario.username == test_admin_username)
        res_user = await db_session.execute(stmt_user)
        assert res_user.scalar_one_or_none() is None

        # Roda o bootstrap pela primeira vez (criação)
        await init_initial_data()

        # Verifica se o perfil 'ADMINISTRADOR' foi criado
        stmt_perfil = select(Perfil).where(Perfil.nome == "ADMINISTRADOR")
        res_perfil = await db_session.execute(stmt_perfil)
        perfil = res_perfil.scalar_one_or_none()
        assert perfil is not None
        assert perfil.nome == "ADMINISTRADOR"

        # Verifica se o usuário master foi criado e associado ao perfil
        stmt_user_created = select(Usuario).options(selectinload(Usuario.perfis)).where(Usuario.username == test_admin_username)
        res_user_created = await db_session.execute(stmt_user_created)
        user = res_user_created.scalar_one_or_none()
        assert user is not None
        assert user.username == test_admin_username
        assert user.email == test_admin_email
        assert len(user.perfis) > 0
        assert any(p.nome == "ADMINISTRADOR" for p in user.perfis)

        # Roda o bootstrap pela segunda vez (idempotência)
        # Não deve levantar exceções nem duplicar o usuário
        await init_initial_data()

        # Verifica se ainda temos exatamente um usuário com esse username
        stmt_user_check = select(Usuario).where(Usuario.username == test_admin_username)
        res_user_check = await db_session.execute(stmt_user_check)
        users = res_user_check.scalars().all()
        assert len(users) == 1

    finally:
        # Cleanup do usuário de teste
        stmt_user_cleanup = select(Usuario).options(selectinload(Usuario.perfis)).where(Usuario.username == test_admin_username)
        res_user_cleanup = await db_session.execute(stmt_user_cleanup)
        user_cleanup = res_user_cleanup.scalar_one_or_none()
        if user_cleanup:
            user_cleanup.perfis.clear()
            await db_session.delete(user_cleanup)
            await db_session.commit()

        # Restaura configurações originais
        config.settings.ADMIN_USERNAME = orig_username
        config.settings.ADMIN_PASSWORD = orig_password
        config.settings.ADMIN_EMAIL = orig_email

