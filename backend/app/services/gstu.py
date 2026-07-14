from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.gstu import Gstu
from app.models.simulacao import AuditLog, OperacaoLog
from app.schemas.gstu import GstuCreate, GstuUpdate

def serialize_for_audit(model_obj) -> dict:
    """
    Serializa um objeto ORM Gstu em um dicionário compatível com JSON para auditoria.
    """
    res = {}
    for col in model_obj.__table__.columns:
        val = getattr(model_obj, col.name)
        if isinstance(val, Decimal):
            res[col.name] = str(val)
        elif isinstance(val, UUID):
            res[col.name] = str(val)
        else:
            res[col.name] = val
    return res

async def criar_gstu(
    db: AsyncSession,
    payload: GstuCreate,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> Gstu:
    """
    Cadastra uma nova referência de gratificação GSTU se o nível não existir. Registra auditoria.
    """
    # 1. Verifica se já existe o nível informado
    stmt = select(Gstu).where(Gstu.nivel == payload.nivel)
    result = await db.execute(stmt)
    existente = result.scalar_one_or_none()

    if existente:
        raise ValueError("Já existe um valor de GSTU cadastrado para este nível.")

    # 2. Instancia o modelo
    nova_gstu = Gstu(
        nivel=payload.nivel,
        valor=payload.valor
    )

    db.add(nova_gstu)
    await db.flush()

    # 3. Registra auditoria
    audit_log = AuditLog(
        usuario_id=usuario_id,
        tabela_afetada="gstu",
        registro_id=nova_gstu.id,
        operacao=OperacaoLog.INSERT,
        payload_antigo=None,
        payload_novo=serialize_for_audit(nova_gstu),
        ip_origem=ip_origem,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(nova_gstu)
    return nova_gstu

async def listar_gstu(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Gstu]:
    """
    Retorna a lista paginada de GSTUs cadastrados.
    """
    stmt = select(Gstu).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def obter_gstu(db: AsyncSession, id: UUID) -> Gstu | None:
    """
    Retorna uma gratificação GSTU específica pelo ID.
    """
    stmt = select(Gstu).where(Gstu.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def atualizar_gstu(
    db: AsyncSession,
    id: UUID,
    payload: GstuUpdate,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> Gstu | None:
    """
    Atualiza uma referência de gratificação GSTU. Verifica unicidade se o nível está mudando. Registra auditoria.
    """
    gstu = await obter_gstu(db, id)
    if not gstu:
        return None

    # Verifica duplicidade
    novo_nivel = payload.nivel if payload.nivel is not None else gstu.nivel

    if novo_nivel != gstu.nivel:
        stmt = select(Gstu).where(
            Gstu.nivel == novo_nivel,
            Gstu.id != id
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("Já existe um valor de GSTU cadastrado para este nível.")

    payload_antigo = serialize_for_audit(gstu)

    # Atualiza campos
    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(gstu, key, val)

    # Registra auditoria
    audit_log = AuditLog(
        usuario_id=usuario_id,
        tabela_afetada="gstu",
        registro_id=gstu.id,
        operacao=OperacaoLog.UPDATE,
        payload_antigo=payload_antigo,
        payload_novo=serialize_for_audit(gstu),
        ip_origem=ip_origem,
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(gstu)
    return gstu

async def deletar_gstu(
    db: AsyncSession,
    id: UUID,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> bool:
    """
    Remove uma referência de gratificação GSTU do sistema. Registra auditoria.
    """
    gstu = await obter_gstu(db, id)
    if not gstu:
        return False

    payload_antigo = serialize_for_audit(gstu)

    # Registra auditoria
    audit_log = AuditLog(
        usuario_id=usuario_id,
        tabela_afetada="gstu",
        registro_id=gstu.id,
        operacao=OperacaoLog.DELETE,
        payload_antigo=payload_antigo,
        payload_novo=None,
        ip_origem=ip_origem,
    )
    db.add(audit_log)

    await db.delete(gstu)
    await db.commit()
    return True
