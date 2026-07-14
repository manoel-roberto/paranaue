from datetime import date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, StringConstraints, ConfigDict
from typing_extensions import Annotated

# CPF contendo exatamente 11 dígitos numéricos
CpfField = Annotated[str, StringConstraints(pattern=r"^\d{11}$")]


class ServidorBaseSchema(BaseModel):
    cpf: CpfField = Field(description="CPF do servidor contendo exatamente 11 dígitos numéricos")
    nome: str = Field(min_length=1, max_length=150, description="Nome do servidor")
    data_nascimento: date = Field(description="Data de nascimento do servidor")


class ServidorCreateSchema(ServidorBaseSchema):
    model_config = {
        "json_schema_extra": {
            "example": {
                "cpf": "01234567890",
                "nome": "Dr. Adailton de Souza",
                "data_nascimento": "1980-04-12"
            }
        }
    }


class ServidorResponse(ServidorBaseSchema):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "8b51c89f-8672-4d2f-a60d-71b5695779c1",
                "cpf": "01234567890",
                "nome": "Dr. Adailton de Souza",
                "data_nascimento": "1980-04-12"
            }
        }
    )


class ServidorUpdate(BaseModel):
    cpf: Optional[CpfField] = Field(default=None, description="CPF do servidor contendo exatamente 11 dígitos numéricos")
    nome: Optional[str] = Field(default=None, min_length=1, max_length=150, description="Nome do servidor")
    data_nascimento: Optional[date] = Field(default=None, description="Data de nascimento do servidor")

    model_config = {
        "json_schema_extra": {
            "example": {
                "cpf": "01234567890",
                "nome": "Dr. Adailton de Souza (Atualizado)",
                "data_nascimento": "1980-04-12"
            }
        }
    }
