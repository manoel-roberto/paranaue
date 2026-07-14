from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict


class SimulacaoRequest(BaseModel):
    servidor_id: UUID = Field(..., description="ID do servidor")
    novo_vencimento_id: UUID = Field(..., description="ID da nova tabela de vencimento para o cenário proposto")
    novo_gstu_id: Optional[UUID] = Field(None, description="ID da nova tabela GSTU para o cenário proposto")
    data_vigencia: date = Field(..., description="Data de vigência da simulação")
    mes_ferias: int = Field(..., ge=1, le=12, description="Mês de férias do servidor (1 a 12)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "servidor_id": "8b51c89f-8672-4d2f-a60d-71b5695779c1",
                "novo_vencimento_id": "e4f8a37f-8672-4d2f-a60d-71b5695779c2",
                "novo_gstu_id": "e4f8a37f-8672-4d2f-a60d-71b5695779c3",
                "data_vigencia": "2026-08-01",
                "mes_ferias": 7
            }
        }
    }


class SimulacaoResponse(BaseModel):
    id: UUID = Field(..., description="ID da simulação")
    servidor_id: UUID = Field(..., description="ID do servidor")
    resultado_calculo_json: Dict[str, Any] = Field(..., description="JSON do impacto financeiro detalhado")
    justificativa: Optional[str] = Field(None, description="Justificativa dos requisitos de alteração funcional")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a9e8d7c6-b5a4-4f3e-2d1c-0b9a8e7d6c5b",
                "servidor_id": "8b51c89f-8672-4d2f-a60d-71b5695779c1",
                "resultado_calculo_json": {
                    "vencimento_atual": 4500.00,
                    "vencimento_proposto": 5420.50,
                    "gstu_atual": 1000.00,
                    "gstu_proposto": 1250.00,
                    "impacto_mensal": 1170.50,
                    "impacto_anual_estimado": 15216.50
                },
                "justificativa": "Servidor preenche os requisitos temporais e de titulação para promoção a Professor Auxiliar."
            }
        }
    )
