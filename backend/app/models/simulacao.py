import uuid
from uuid import UUID
from datetime import date, datetime
from enum import Enum as PyEnum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, Enum, text, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.servidor import Vinculo


class StatusSimulacao(str, PyEnum):
    RASCUNHO = "RASCUNHO"
    PROCESSANDO = "PROCESSANDO"
    FINALIZADO = "FINALIZADO"
    ERRO = "ERRO"


class TipoSimulacao(str, PyEnum):
    INDIVIDUAL = "INDIVIDUAL"
    LOTE = "LOTE"


class OperacaoLog(str, PyEnum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    SIMULACAO_EXECUCAO = "SIMULACAO_EXECUCAO"


class Simulacao(Base):
    __tablename__ = "simulacao"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[TipoSimulacao] = mapped_column(Enum(TipoSimulacao), nullable=False)
    status: Mapped[StatusSimulacao] = mapped_column(
        Enum(StatusSimulacao), default=StatusSimulacao.RASCUNHO, nullable=False
    )
    criado_por_usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Relacionamentos
    criado_por: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="simulacoes"
    )
    itens: Mapped[List["SimulacaoItem"]] = relationship(
        "SimulacaoItem", back_populates="simulacao", cascade="all, delete-orphan"
    )


class SimulacaoItem(Base):
    __tablename__ = "simulacao_item"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    simulacao_id: Mapped[UUID] = mapped_column(
        ForeignKey("simulacao.id", ondelete="CASCADE"), nullable=False
    )
    vinculo_id: Mapped[UUID] = mapped_column(
        ForeignKey("vinculo.id", ondelete="RESTRICT"), nullable=False
    )
    data_vigencia_proposta: Mapped[date] = mapped_column(Date, nullable=False)
    mes_gozo_ferias_proposto: Mapped[int] = mapped_column(Integer, nullable=False)
    dados_origem_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dados_propostos_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    resultado_calculo_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    justificativa_requisitos: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Relacionamentos
    simulacao: Mapped["Simulacao"] = relationship("Simulacao", back_populates="itens")
    vinculo: Mapped["Vinculo"] = relationship("Vinculo", back_populates="itens_simulacao")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    tabela_afetada: Mapped[str] = mapped_column(String(50), nullable=False)
    registro_id: Mapped[UUID] = mapped_column(nullable=False)
    operacao: Mapped[OperacaoLog] = mapped_column(Enum(OperacaoLog), nullable=False)
    payload_antigo: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    payload_novo: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_origem: Mapped[str] = mapped_column(
        String(45),
        default="0.0.0.0",
        server_default=text("'0.0.0.0'"),
        nullable=False,
    )
    data_hora: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Relacionamentos
    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario", back_populates="logs")
