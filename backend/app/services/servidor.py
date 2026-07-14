from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.servidor import Servidor, Vinculo, Cargo, Averbacao
from app.models.tabelas import HistoricoFuncional, TabelaVencimento
from app.schemas.servidor import (
    ServidorCreateSchema,
    ServidorUpdate,
    VinculoCreateSchema,
    HistoricoFuncionalCreateSchema,
    AverbacaoCreateSchema,
)


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


async def criar_vinculo(db: AsyncSession, servidor_id: UUID, payload: VinculoCreateSchema) -> Vinculo:
    """
    Cria um novo vínculo para o servidor.
    """
    # 1. Verificar se o servidor existe
    servidor = await obter_servidor(db, servidor_id)
    if not servidor:
        raise ValueError("Servidor não encontrado")

    # 2. Verificar se a matrícula já existe
    stmt = select(Vinculo).where(Vinculo.matricula == payload.matricula)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ValueError("Matrícula já cadastrada")

    # 3. Verificar se o cargo existe
    stmt_cargo = select(Cargo).where(Cargo.id == payload.cargo_id)
    res_cargo = await db.execute(stmt_cargo)
    if not res_cargo.scalar_one_or_none():
        raise ValueError("Cargo não encontrado")

    novo_vinculo = Vinculo(
        servidor_id=servidor_id,
        matricula=payload.matricula,
        data_admissao=payload.data_admissao,
        cargo_id=payload.cargo_id,
        regime_previdenciario=payload.regime_previdenciario,
        participante_prev_complementar=payload.participante_prev_complementar,
        aliquota_coparticipacao_complementar=payload.aliquota_coparticipacao_complementar,
        tipo_vinculo=payload.tipo_vinculo,
        ativo=payload.ativo,
    )
    db.add(novo_vinculo)
    await db.commit()
    await db.refresh(novo_vinculo)
    return novo_vinculo


async def listar_vinculos_do_servidor(db: AsyncSession, servidor_id: UUID) -> list[Vinculo]:
    """
    Lista todos os vínculos de um servidor.
    """
    stmt = select(Vinculo).where(Vinculo.servidor_id == servidor_id)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def obter_vinculo(db: AsyncSession, vinculo_id: UUID) -> Vinculo | None:
    """
    Obtém um vínculo por ID.
    """
    stmt = select(Vinculo).where(Vinculo.id == vinculo_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def criar_historico_funcional(
    db: AsyncSession, vinculo_id: UUID, payload: HistoricoFuncionalCreateSchema
) -> HistoricoFuncional:
    """
    Adiciona um novo registro ao histórico funcional de um vínculo,
    fechando a vigência ativa anterior automaticamente, se houver.
    """
    # 1. Verificar se o vínculo existe
    vinculo = await obter_vinculo(db, vinculo_id)
    if not vinculo:
        raise ValueError("Vínculo não encontrado")

    # 2. Verificar consistência de datas
    if payload.data_fim < payload.data_inicio:
        raise ValueError("A data de início deve ser anterior ou igual à data de fim")

    # 3. Verificar se tabela_vencimento_id existe
    stmt_venc = select(TabelaVencimento).where(TabelaVencimento.id == payload.tabela_vencimento_id)
    res_venc = await db.execute(stmt_venc)
    if not res_venc.scalar_one_or_none():
        raise ValueError("Tabela de vencimento não encontrada")

    # 4. Fechar vigência anterior ativa se a nova vigência for de prazo indefinido (data_fim == 9999-12-31)
    stmt_active = select(HistoricoFuncional).where(
        HistoricoFuncional.vinculo_id == vinculo_id,
        HistoricoFuncional.data_fim == date(9999, 12, 31)
    )
    res_active = await db.execute(stmt_active)
    active_hist = res_active.scalar_one_or_none()
    
    fechou_ativo = False
    if active_hist and payload.data_fim == date(9999, 12, 31):
        if payload.data_inicio <= active_hist.data_inicio:
            raise ValueError("A data de início do novo enquadramento deve ser posterior à data de início do enquadramento ativo")
        active_hist.data_fim = payload.data_inicio - timedelta(days=1)
        db.add(active_hist)
        fechou_ativo = True

    # 5. Verificar sobreposição com registros passados
    stmt_all = select(HistoricoFuncional).where(HistoricoFuncional.vinculo_id == vinculo_id)
    res_all = await db.execute(stmt_all)
    historicos = res_all.scalars().all()
    
    for h in historicos:
        if fechou_ativo and h.id == active_hist.id:
            # Ignoramos a que acabamos de fechar, pois já mudamos seu data_fim na transação
            old_start = h.data_inicio
            old_end = payload.data_inicio - timedelta(days=1)
        else:
            old_start = h.data_inicio
            old_end = h.data_fim

        if not (payload.data_fim < old_start or payload.data_inicio > old_end):
            raise ValueError("Violação de consistência: O período solicitado se sobrepõe ao enquadramento existente.")

    novo_hist = HistoricoFuncional(
        vinculo_id=vinculo_id,
        data_inicio=payload.data_inicio,
        data_fim=payload.data_fim,
        tabela_vencimento_id=payload.tabela_vencimento_id,
        tabela_gstu_id=payload.tabela_gstu_id,
        cet_percentual=payload.cet_percentual,
        insalubridade_percentual=payload.insalubridade_percentual,
        vpess_valor=payload.vpess_valor,
        tabela_comissao_id=payload.tabela_comissao_id,
        percentual_estabilizado=payload.percentual_estabilizado,
    )
    db.add(novo_hist)
    
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("Erro de integridade ao salvar histórico funcional (possível colisão temporal no banco)") from e
        
    await db.refresh(novo_hist)
    return novo_hist


async def listar_historico_funcional(db: AsyncSession, vinculo_id: UUID) -> list[HistoricoFuncional]:
    """
    Retorna o histórico funcional de um vínculo, ordenado por data de início.
    """
    stmt = (
        select(HistoricoFuncional)
        .where(HistoricoFuncional.vinculo_id == vinculo_id)
        .options(selectinload(HistoricoFuncional.tabela_vencimento))
        .order_by(HistoricoFuncional.data_inicio)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
async def criar_averbacao(db: AsyncSession, vinculo_id: UUID, payload: AverbacaoCreateSchema) -> Averbacao:
    """
    Cria uma nova averbação para o vínculo.
    """
    vinculo = await obter_vinculo(db, vinculo_id)
    if not vinculo:
        raise ValueError("Vínculo não encontrado")

    nova_averbacao = Averbacao(
        vinculo_id=vinculo_id,
        dias_averbados=payload.dias_averbados,
        tipo_averbacao=payload.tipo_averbacao,
        data_averbacao=payload.data_averbacao,
        processo_numero=payload.processo_numero,
    )
    db.add(nova_averbacao)
    await db.commit()
    await db.refresh(nova_averbacao)
    return nova_averbacao


async def listar_averbacoes(db: AsyncSession, vinculo_id: UUID) -> list[Averbacao]:
    """
    Lista todas as averbações associadas a um vínculo.
    """
    stmt = select(Averbacao).where(Averbacao.vinculo_id == vinculo_id).order_by(Averbacao.data_averbacao)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def listar_cargos(db: AsyncSession) -> list[Cargo]:
    """
    Lista todos os cargos.
    """
    stmt = select(Cargo).order_by(Cargo.nome)
    res = await db.execute(stmt)
    return list(res.scalars().all())
