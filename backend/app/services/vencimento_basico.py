from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.vencimento_basico import VencimentoBasico
from app.models.simulacao import AuditLog, OperacaoLog
from app.schemas.vencimento_basico import VencimentoBasicoCreate, VencimentoBasicoUpdate

def serialize_for_audit(model_obj) -> dict:
    """
    Serializa um objeto ORM VencimentoBasico em um dicionário compatível com JSON para auditoria.
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

async def criar_vencimento(
    db: AsyncSession,
    payload: VencimentoBasicoCreate,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> VencimentoBasico:
    """
    Cadastra uma nova referência de vencimento básico se a combinação classe/referência
    não existir. Registra auditoria.
    """
    # 1. Verifica se já existe a combinação classe/referência
    stmt = select(VencimentoBasico).where(
        VencimentoBasico.classe == payload.classe,
        VencimentoBasico.referencia == payload.referencia
    )
    result = await db.execute(stmt)
    existente = result.scalar_one_or_none()

    if existente:
        raise ValueError("Já existe um vencimento básico cadastrado para esta classe e referência.")

    # 2. Instancia o modelo
    novo_vencimento = VencimentoBasico(
        classe=payload.classe,
        referencia=payload.referencia,
        valor=payload.valor
    )

    db.add(novo_vencimento)
    await db.flush()

    # 3. Registra auditoria
    audit_log = AuditLog(
        usuario_id=usuario_id,
        tabela_afetada="vencimento_basico",
        registro_id=novo_vencimento.id,
        operacao=OperacaoLog.INSERT,
        payload_antigo=None,
        payload_novo=serialize_for_audit(novo_vencimento),
        ip_origem=ip_origem,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(novo_vencimento)
    return novo_vencimento

async def listar_vencimentos(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[VencimentoBasico]:
    """
    Retorna a lista paginada de vencimentos básicos cadastrados.
    """
    stmt = select(VencimentoBasico).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def obter_vencimento(db: AsyncSession, id: UUID) -> VencimentoBasico | None:
    """
    Retorna um vencimento básico específico pelo ID.
    """
    stmt = select(VencimentoBasico).where(VencimentoBasico.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def atualizar_vencimento(
    db: AsyncSession,
    id: UUID,
    payload: VencimentoBasicoUpdate,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> VencimentoBasico | None:
    """
    Atualiza uma referência de vencimento básico. Verifica unicidade se classe/referência
    estão mudando. Registra auditoria.
    """
    vencimento = await obter_vencimento(db, id)
    if not vencimento:
        return None

    # Verifica duplicidade
    nova_classe = payload.classe if payload.classe is not None else vencimento.classe
    nova_referencia = payload.referencia if payload.referencia is not None else vencimento.referencia

    if nova_classe != vencimento.classe or nova_referencia != vencimento.referencia:
        stmt = select(VencimentoBasico).where(
            VencimentoBasico.classe == nova_classe,
            VencimentoBasico.referencia == nova_referencia,
            VencimentoBasico.id != id
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("Já existe um vencimento básico cadastrado para esta classe e referência.")

    payload_antigo = serialize_for_audit(vencimento)

    # Atualiza campos
    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(vencimento, key, val)

    # Registra auditoria
    audit_log = AuditLog(
        usuario_id=usuario_id,
        tabela_afetada="vencimento_basico",
        registro_id=vencimento.id,
        operacao=OperacaoLog.UPDATE,
        payload_antigo=payload_antigo,
        payload_novo=serialize_for_audit(vencimento),
        ip_origem=ip_origem,
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(vencimento)
    return vencimento

async def deletar_vencimento(
    db: AsyncSession,
    id: UUID,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> bool:
    """
    Remove uma referência de vencimento básico do sistema. Registra auditoria.
    """
    vencimento = await obter_vencimento(db, id)
    if not vencimento:
        return False

    payload_antigo = serialize_for_audit(vencimento)

    # Registra auditoria
    audit_log = AuditLog(
        usuario_id=usuario_id,
        tabela_afetada="vencimento_basico",
        registro_id=vencimento.id,
        operacao=OperacaoLog.DELETE,
        payload_antigo=payload_antigo,
        payload_novo=None,
        ip_origem=ip_origem,
    )
    db.add(audit_log)

    await db.delete(vencimento)
    await db.commit()
    return True
