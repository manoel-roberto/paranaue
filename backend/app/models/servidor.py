import uuid
from uuid import UUID
from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Boolean, Date, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tabelas import HistoricoFuncional
    from app.models.simulacao import SimulacaoItem


class RegimePrevidenciario(str, PyEnum):
    BAPREV_REGIME_PROPRIO = "BAPREV_REGIME_PROPRIO"
    PREVBAHIA_COMPLEMENTAR = "PREVBAHIA_COMPLEMENTAR"


class TipoVinculo(str, PyEnum):
    ESTATUTARIO = "ESTATUTARIO"
    REDA = "REDA"
    CLT = "CLT"


class TipoCargo(str, PyEnum):
    DOCENTE = "DOCENTE"
    ANALISTA = "ANALISTA"
    TECNICO = "TECNICO"
    AUXILIAR = "AUXILIAR"


class TipoAverbacao(str, PyEnum):
    ATS = "ATS"
    APOSENTADORIA = "APOSENTADORIA"


class Servidor(Base):
    __tablename__ = "servidor"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)

    # Relacionamentos
    vinculos: Mapped[List["Vinculo"]] = relationship(
        "Vinculo", back_populates="servidor", cascade="all, delete-orphan"
    )


class Cargo(Base):
    __tablename__ = "cargo"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoCargo] = mapped_column(Enum(TipoCargo), nullable=False)
    carga_horaria_padrao: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relacionamentos
    vinculos: Mapped[List["Vinculo"]] = relationship("Vinculo", back_populates="cargo")


class Vinculo(Base):
    __tablename__ = "vinculo"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    servidor_id: Mapped[UUID] = mapped_column(
        ForeignKey("servidor.id", ondelete="RESTRICT"), nullable=False
    )
    matricula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    data_admissao: Mapped[date] = mapped_column(Date, nullable=False)
    cargo_id: Mapped[UUID] = mapped_column(
        ForeignKey("cargo.id", ondelete="RESTRICT"), nullable=False
    )
    regime_previdenciario: Mapped[RegimePrevidenciario] = mapped_column(
        Enum(RegimePrevidenciario), nullable=False
    )
    participante_prev_complementar: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    aliquota_coparticipacao_complementar: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), default=Decimal("0.00"), nullable=False
    )
    tipo_vinculo: Mapped[TipoVinculo] = mapped_column(Enum(TipoVinculo), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    servidor: Mapped["Servidor"] = relationship("Servidor", back_populates="vinculos")
    cargo: Mapped["Cargo"] = relationship("Cargo", back_populates="vinculos")
    averbacoes: Mapped[List["Averbacao"]] = relationship(
        "Averbacao", back_populates="vinculo", cascade="all, delete-orphan"
    )
    historicos_funcionais: Mapped[List["HistoricoFuncional"]] = relationship(
        "HistoricoFuncional", back_populates="vinculo", cascade="all, delete-orphan"
    )
    itens_simulacao: Mapped[List["SimulacaoItem"]] = relationship(
        "SimulacaoItem", back_populates="vinculo"
    )


class Averbacao(Base):
    __tablename__ = "averbacao"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vinculo_id: Mapped[UUID] = mapped_column(
        ForeignKey("vinculo.id", ondelete="RESTRICT"), nullable=False
    )
    dias_averbados: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo_averbacao: Mapped[TipoAverbacao] = mapped_column(
        Enum(TipoAverbacao), nullable=False
    )
    data_averbacao: Mapped[date] = mapped_column(Date, nullable=False)
    processo_numero: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relacionamentos
    vinculo: Mapped["Vinculo"] = relationship("Vinculo", back_populates="averbacoes")
