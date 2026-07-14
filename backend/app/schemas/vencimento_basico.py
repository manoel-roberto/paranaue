from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class VencimentoBasicoBase(BaseModel):
    classe: str = Field(..., min_length=1, max_length=100, description="Classe do cargo")
    referencia: str = Field(..., min_length=1, max_length=50, description="Referência do cargo")
    valor: Decimal = Field(..., gt=Decimal("0.00"), description="Valor do vencimento básico (deve ser maior que zero)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "classe": "Professor Adjunto",
                "referencia": "Classe A - Nível 1",
                "valor": "7500.50"
            }
        }
    }

class VencimentoBasicoCreate(VencimentoBasicoBase):
    pass

class VencimentoBasicoUpdate(BaseModel):
    classe: str | None = Field(None, min_length=1, max_length=100)
    referencia: str | None = Field(None, min_length=1, max_length=50)
    valor: Decimal | None = Field(None, gt=Decimal("0.00"))

    model_config = {
        "json_schema_extra": {
            "example": {
                "classe": "Professor Adjunto",
                "referencia": "Classe A - Nível 2",
                "valor": "8100.00"
            }
        }
    }

class VencimentoBasicoResponse(VencimentoBasicoBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "e4f8a37f-8672-4d2f-a60d-71b5695779c2",
                "classe": "Professor Adjunto",
                "referencia": "Classe A - Nível 1",
                "valor": "7500.50"
            }
        }
    )
