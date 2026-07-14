from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.tabelas import TabelaVencimento, TabelaGstu, TabelaComissao
from app.models.simulacao import AuditLog, OperacaoLog
from app.schemas.parametros import TabelaVencimentoSchema, TabelaGstuSchema


def serialize_for_audit(model_obj) -> dict:
    """
    Serializa um objeto ORM em um dicionário compatível com JSON para auditoria.
    """
    res = {}
    for col in model_obj.__table__.columns:
        val = getattr(model_obj, col.name)
        if isinstance(val, (date, datetime)):
            res[col.name] = val.isoformat()
        elif isinstance(val, Decimal):
            res[col.name] = str(val)
        elif isinstance(val, UUID):
            res[col.name] = str(val)
        else:
            res[col.name] = val
    return res


async def criar_tabela_vencimento(
    db: AsyncSession,
    payload: TabelaVencimentoSchema,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> TabelaVencimento:
    """
    Cadastra uma nova tabela de vencimento após verificar se há sobreposição de vigência
    para a mesma classe, nível e carga horária. Registra auditoria na tabela audit_log.
    Levanta ValueError em caso de sobreposição.
    """
    # Verifica sobreposição de vigência
    stmt = select(TabelaVencimento).where(
        TabelaVencimento.classe == payload.classe,
        TabelaVencimento.nivel_grau == payload.nivel_grau,
        TabelaVencimento.carga_horaria == payload.carga_horaria,
        TabelaVencimento.data_inicio_vigencia <= payload.data_fim_vigencia,
        TabelaVencimento.data_fim_vigencia >= payload.data_inicio_vigencia,
    )
    result = await db.execute(stmt)
    sobreposto = result.scalar_one_or_none()

    if sobreposto:
        raise ValueError(
            "Já existe uma tabela de vencimento cadastrada para esta classe, nível e carga horária com vigência sobreposta."
        )

    # Cria a instância do modelo
    nova_tabela = TabelaVencimento(
        codigo_vencimento=payload.codigo_vencimento,
        classe=payload.classe,
        nivel_grau=payload.nivel_grau,
        carga_horaria=payload.carga_horaria,
        valor_base=payload.valor_base,
        data_inicio_vigencia=payload.data_inicio_vigencia,
        data_fim_vigencia=payload.data_fim_vigencia,
    )

    db.add(nova_tabela)
    await db.commit()
    await db.refresh(nova_tabela)
    return nova_tabela


async def listar_tabela_vencimento(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[TabelaVencimento]:
    """
    Lista registros da tabela de vencimentos com paginação.
    """
    stmt = select(TabelaVencimento).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def criar_tabela_gstu(
    db: AsyncSession,
    payload: TabelaGstuSchema,
    usuario_id: UUID = None,
    ip_origem: str = "0.0.0.0"
) -> TabelaGstu:
    """
    Cadastra uma nova tabela GSTU após verificar se há sobreposição de vigência
    para o mesmo grau e referência. Registra auditoria na tabela audit_log.
    Levanta ValueError em caso de sobreposição.
    """
    # Verifica sobreposição de vigência
    stmt = select(TabelaGstu).where(
        TabelaGstu.grau == payload.grau,
        TabelaGstu.referencia == payload.referencia,
        TabelaGstu.data_inicio_vigencia <= payload.data_fim_vigencia,
        TabelaGstu.data_fim_vigencia >= payload.data_inicio_vigencia,
    )
    result = await db.execute(stmt)
    sobreposto = result.scalar_one_or_none()

    if sobreposto:
        raise ValueError(
            "Já existe uma tabela GSTU cadastrada para este grau e referência com vigência sobreposta."
        )

    # Cria a instância do modelo
    nova_gstu = TabelaGstu(
        codigo_gstu=payload.codigo_gstu,
        grau=payload.grau,
        referencia=payload.referencia,
        valor_gstu=payload.valor_gstu,
        data_inicio_vigencia=payload.data_inicio_vigencia,
        data_fim_vigencia=payload.data_fim_vigencia,
    )

    db.add(nova_gstu)
    await db.commit()
    await db.refresh(nova_gstu)
    return nova_gstu


async def listar_tabela_gstu(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[TabelaGstu]:
    """
    Lista registros da tabela GSTU com paginação.
    """
    stmt = select(TabelaGstu).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def listar_tabela_comissao(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[TabelaComissao]:
    """
    Lista registros da tabela de comissão com paginação.
    """
    stmt = select(TabelaComissao).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
