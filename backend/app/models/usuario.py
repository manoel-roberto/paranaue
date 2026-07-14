import uuid
from uuid import UUID
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.simulacao import Simulacao, AuditLog


class UsuarioPerfil(Base):
    __tablename__ = "usuario_perfil"

    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    perfil_id: Mapped[UUID] = mapped_column(
        ForeignKey("perfil.id", ondelete="CASCADE"), primary_key=True
    )


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Relacionamentos
    perfis: Mapped[List["Perfil"]] = relationship(
        "Perfil", secondary="usuario_perfil", back_populates="usuarios"
    )
    simulacoes: Mapped[List["Simulacao"]] = relationship(
        "Simulacao", back_populates="criado_por"
    )
    logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="usuario")


class Perfil(Base):
    __tablename__ = "perfil"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)

    # Relacionamentos
    usuarios: Mapped[List["Usuario"]] = relationship(
        "Usuario", secondary="usuario_perfil", back_populates="perfis"
    )
