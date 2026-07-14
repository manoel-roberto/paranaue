import uuid
from uuid import UUID
from decimal import Decimal
from sqlalchemy import String, Numeric, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class Gstu(Base):
    __tablename__ = "gstu"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nivel: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("nivel", name="uq_gstu_nivel"),
        CheckConstraint("valor > 0", name="chk_gstu_valor_positivo"),
    )
