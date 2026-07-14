import uuid
from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.servidor import Vinculo


class TabelaVencimento(Base):
    __tablename__ = "tabela_vencimento"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo_vencimento: Mapped[str] = mapped_column(String(20), nullable=False)
    classe: Mapped[str] = mapped_column(String(50), nullable=False)
    nivel_grau: Mapped[str] = mapped_column(String(10), nullable=False)
    carga_horaria: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_inicio_vigencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim_vigencia: Mapped[date] = mapped_column(
        Date,
        default=date(9999, 12, 31),
        server_default=text("'9999-12-31'"),
        nullable=False,
    )

    # Relacionamentos
    historicos_funcionais: Mapped[List["HistoricoFuncional"]] = relationship(
        "HistoricoFuncional", back_populates="tabela_vencimento"
    )


class TabelaGstu(Base):
    __tablename__ = "tabela_gstu"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo_gstu: Mapped[str] = mapped_column(String(30), nullable=False)
    grau: Mapped[str] = mapped_column(String(10), nullable=False)
    referencia: Mapped[str] = mapped_column(String(10), nullable=False)
    valor_gstu: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_inicio_vigencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim_vigencia: Mapped[date] = mapped_column(
        Date,
        default=date(9999, 12, 31),
        server_default=text("'9999-12-31'"),
        nullable=False,
    )

    # Relacionamentos
    historicos_funcionais: Mapped[List["HistoricoFuncional"]] = relationship(
        "HistoricoFuncional", back_populates="tabela_gstu"
    )


class TabelaComissao(Base):
    __tablename__ = "tabela_comissao"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    simbolo: Mapped[str] = mapped_column(String(10), nullable=False)
    valor_comissao: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_inicio_vigencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim_vigencia: Mapped[date] = mapped_column(
        Date,
        default=date(9999, 12, 31),
        server_default=text("'9999-12-31'"),
        nullable=False,
    )

    # Relacionamentos
    historicos_funcionais: Mapped[List["HistoricoFuncional"]] = relationship(
        "HistoricoFuncional", back_populates="tabela_comissao"
    )


class HistoricoFuncional(Base):
    __tablename__ = "historico_funcional"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vinculo_id: Mapped[UUID] = mapped_column(
        ForeignKey("vinculo.id", ondelete="RESTRICT"), nullable=False
    )
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date] = mapped_column(
        Date,
        default=date(9999, 12, 31),
        server_default=text("'9999-12-31'"),
        nullable=False,
    )
    tabela_vencimento_id: Mapped[UUID] = mapped_column(
        ForeignKey("tabela_vencimento.id", ondelete="RESTRICT"), nullable=False
    )
    tabela_gstu_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("tabela_gstu.id", ondelete="RESTRICT"), nullable=True
    )
    cet_percentual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    insalubridade_percentual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    vpess_valor: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tabela_comissao_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("tabela_comissao.id", ondelete="RESTRICT"), nullable=True
    )
    percentual_estabilizado: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )

    # Relacionamentos
    vinculo: Mapped["Vinculo"] = relationship(
        "Vinculo", back_populates="historicos_funcionais"
    )
    tabela_vencimento: Mapped["TabelaVencimento"] = relationship(
        "TabelaVencimento", back_populates="historicos_funcionais"
    )
    tabela_gstu: Mapped[Optional["TabelaGstu"]] = relationship(
        "TabelaGstu", back_populates="historicos_funcionais"
    )
    tabela_comissao: Mapped[Optional["TabelaComissao"]] = relationship(
        "TabelaComissao", back_populates="historicos_funcionais"
    )
