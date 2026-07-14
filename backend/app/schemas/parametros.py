from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator, ConfigDict


class TabelaVencimentoSchema(BaseModel):
    codigo_vencimento: str = Field(min_length=1, max_length=20, description="Código de referência do vencimento")
    classe: str = Field(min_length=1, max_length=50, description="Classe do cargo")
    nivel_grau: str = Field(min_length=1, max_length=10, description="Nível/Grau do cargo")
    carga_horaria: int = Field(gt=0, description="Carga horária semanal")
    valor_base: Decimal = Field(gt=Decimal("0.00"), description="Valor base de vencimento")
    data_inicio_vigencia: date = Field(description="Data de início da vigência")
    data_fim_vigencia: date = Field(default=date(9999, 12, 31), description="Data de fim da vigência")

    model_config = {
        "json_schema_extra": {
            "example": {
                "codigo_vencimento": "VENC-2026-A",
                "classe": "Professor Auxiliar",
                "nivel_grau": "Nivel I",
                "carga_horaria": 40,
                "valor_base": "5420.50",
                "data_inicio_vigencia": "2026-01-01",
                "data_fim_vigencia": "9999-12-31"
            }
        }
    }

    @model_validator(mode="after")
    def validar_vigencia(self) -> "TabelaVencimentoSchema":
        if self.data_inicio_vigencia >= self.data_fim_vigencia:
            raise ValueError("A data de início da vigência deve ser anterior à data de fim.")
        return self


class TabelaVencimentoResponse(TabelaVencimentoSchema):
    id: UUID
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "e4f8a37f-8672-4d2f-a60d-71b5695779c2",
                "codigo_vencimento": "VENC-2026-A",
                "classe": "Professor Auxiliar",
                "nivel_grau": "Nivel I",
                "carga_horaria": 40,
                "valor_base": "5420.50",
                "data_inicio_vigencia": "2026-01-01",
                "data_fim_vigencia": "9999-12-31"
            }
        }
    )


class TabelaGstuSchema(BaseModel):
    codigo_gstu: str = Field(min_length=1, max_length=30, description="Código da referência GSTU")
    grau: str = Field(min_length=1, max_length=10, description="Grau do cargo")
    referencia: str = Field(min_length=1, max_length=10, description="Referência do cargo")
    valor_gstu: Decimal = Field(gt=Decimal("0.00"), description="Valor da GSTU")
    data_inicio_vigencia: date = Field(description="Data de início da vigência")
    data_fim_vigencia: date = Field(default=date(9999, 12, 31), description="Data de fim da vigência")

    model_config = {
        "json_schema_extra": {
            "example": {
                "codigo_gstu": "GSTU-2026-A",
                "grau": "Mestre",
                "referencia": "REF-I",
                "valor_gstu": "1250.00",
                "data_inicio_vigencia": "2026-01-01",
                "data_fim_vigencia": "9999-12-31"
            }
        }
    }

    @model_validator(mode="after")
    def validar_vigencia(self) -> "TabelaGstuSchema":
        if self.data_inicio_vigencia >= self.data_fim_vigencia:
            raise ValueError("A data de início da vigência deve ser anterior à data de fim.")
        return self


class TabelaGstuResponse(TabelaGstuSchema):
    id: UUID
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "e4f8a37f-8672-4d2f-a60d-71b5695779c3",
                "codigo_gstu": "GSTU-2026-A",
                "grau": "Mestre",
                "referencia": "REF-I",
                "valor_gstu": "1250.00",
                "data_inicio_vigencia": "2026-01-01",
                "data_fim_vigencia": "9999-12-31"
            }
        }
    )
