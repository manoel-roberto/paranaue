from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.servidor import Servidor
from app.schemas.servidor import ServidorCreateSchema, ServidorUpdate


async def criar_servidor(db: AsyncSession, payload: ServidorCreateSchema) -> Servidor:
    """
    Cadastra um novo servidor no sistema após verificar se o CPF já está em uso.
    Levanta ValueError se o CPF já existir.
    """
    # 1. Verifica se o CPF já existe
    stmt = select(Servidor).where(Servidor.cpf == payload.cpf)
    result = await db.execute(stmt)
    servidor_existente = result.scalar_one_or_none()
    
    if servidor_existente:
        raise ValueError("CPF já cadastrado")
        
    # 2. Instancia o modelo ORM
    novo_servidor = Servidor(
        cpf=payload.cpf,
        nome=payload.nome,
        data_nascimento=payload.data_nascimento
    )
    
    # 3. Salva no banco de dados
    db.add(novo_servidor)
    await db.commit()
    await db.refresh(novo_servidor)
    
    return novo_servidor


async def listar_servidores(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Servidor]:
    """
    Lista servidores cadastrados no banco com paginação (skip/limit).
    """
    stmt = select(Servidor).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def obter_servidor(db: AsyncSession, servidor_id: UUID) -> Servidor | None:
    """
    Recupera um servidor específico pelo ID.
    """
    stmt = select(Servidor).where(Servidor.id == servidor_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atualizar_servidor(
    db: AsyncSession, servidor_id: UUID, payload: ServidorUpdate
) -> Servidor | None:
    """
    Atualiza os dados de um servidor existente.
    Verifica unicidade de CPF se fornecido.
    """
    # 1. Busca o servidor existente
    servidor = await obter_servidor(db, servidor_id)
    if not servidor:
        return None

    # 2. Se o CPF está sendo alterado, verifica se já existe em outro servidor
    if payload.cpf is not None and payload.cpf != servidor.cpf:
        stmt = select(Servidor).where(Servidor.cpf == payload.cpf, Servidor.id != servidor_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("CPF já cadastrado")

    # 3. Atualiza os campos fornecidos no payload
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(servidor, field, value)

    # 4. Salva as mudanças
    await db.commit()
    await db.refresh(servidor)
    return servidor


async def deletar_servidor(db: AsyncSession, servidor_id: UUID) -> bool:
    """
    Remove um servidor do banco de dados.
    Retorna True se removido com sucesso, False se não existir.
    Levanta ValueError se houver vínculos impedindo a exclusão (ondelete RESTRICT).
    """
    # 1. Busca o servidor existente
    servidor = await obter_servidor(db, servidor_id)
    if not servidor:
        return False

    # 2. Tenta remover
    try:
        await db.delete(servidor)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        raise ValueError("Não é possível excluir o servidor pois ele possui vínculos associados")
