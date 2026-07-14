import uuid
from uuid import UUID
from decimal import Decimal
from sqlalchemy import String, Numeric, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class VencimentoBasico(Base):
    __tablename__ = "vencimento_basico"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    classe: Mapped[str] = mapped_column(String(100), nullable=False)
    referencia: Mapped[str] = mapped_column(String(50), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("classe", "referencia", name="uq_vencimento_basico_classe_referencia"),
        CheckConstraint("valor > 0", name="chk_vencimento_basico_valor_positivo"),
    )
