from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class GstuBase(BaseModel):
    nivel: str = Field(..., min_length=1, max_length=100, description="Nível da gratificação GSTU")
    valor: Decimal = Field(..., gt=Decimal("0.00"), description="Valor da gratificação GSTU (deve ser maior que zero)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nivel": "Nível 1",
                "valor": "1250.75"
            }
        }
    }

class GstuCreate(GstuBase):
    pass

class GstuUpdate(BaseModel):
    nivel: str | None = Field(None, min_length=1, max_length=100)
    valor: Decimal | None = Field(None, gt=Decimal("0.00"))

    model_config = {
        "json_schema_extra": {
            "example": {
                "nivel": "Nível 2",
                "valor": "1480.00"
            }
        }
    }

class GstuResponse(GstuBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
                "nivel": "Nível 1",
                "valor": "1250.75"
            }
        }
    )
