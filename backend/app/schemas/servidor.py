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


from decimal import Decimal
from app.models.servidor import RegimePrevidenciario, TipoVinculo, TipoAverbacao, TipoCargo

class AverbacaoBaseSchema(BaseModel):
    dias_averbados: int = Field(gt=0, description="Dias averbados (deve ser maior que zero)")
    tipo_averbacao: TipoAverbacao = Field(description="Tipo de averbação")
    data_averbacao: date = Field(description="Data da averbação")
    processo_numero: str = Field(min_length=1, max_length=50, description="Número do processo administrativo")

class AverbacaoCreateSchema(AverbacaoBaseSchema):
    pass

class AverbacaoResponse(AverbacaoBaseSchema):
    id: UUID
    vinculo_id: UUID

    model_config = ConfigDict(from_attributes=True)


class VinculoBaseSchema(BaseModel):
    matricula: str = Field(min_length=1, max_length=20, description="Matrícula funcional")
    data_admissao: date = Field(description="Data de admissão/ingresso")
    cargo_id: UUID = Field(description="ID do Cargo")
    regime_previdenciario: RegimePrevidenciario = Field(description="Regime Previdenciário")
    participante_prev_complementar: bool = Field(default=False, description="Flag de adesão à Previdência Complementar")
    aliquota_coparticipacao_complementar: Decimal = Field(default=Decimal("0.00"), ge=0.00, le=100.00, description="Alíquota de coparticipação")
    tipo_vinculo: TipoVinculo = Field(description="Tipo de Vínculo")
    ativo: bool = Field(default=True, description="Status do vínculo")

class VinculoCreateSchema(VinculoBaseSchema):
    pass

class VinculoResponse(VinculoBaseSchema):
    id: UUID
    servidor_id: UUID

    model_config = ConfigDict(from_attributes=True)


class HistoricoFuncionalBaseSchema(BaseModel):
    data_inicio: date = Field(description="Data de início da vigência")
    data_fim: date = Field(default=date(9999, 12, 31), description="Data de fim da vigência")
    tabela_vencimento_id: UUID = Field(description="ID do Vencimento Básico")
    tabela_gstu_id: Optional[UUID] = Field(default=None, description="ID da Gratificação GSTU")
    cet_percentual: Decimal = Field(default=Decimal("0.00"), ge=0.00, description="Percentual da CET")
    insalubridade_percentual: Decimal = Field(default=Decimal("0.00"), ge=0.00, description="Percentual de Insalubridade")
    vpess_valor: Decimal = Field(default=Decimal("0.00"), ge=0.00, description="Valor da Vantagem Pessoal")
    tabela_comissao_id: Optional[UUID] = Field(default=None, description="ID da Função Comissionada/Estabilidade")
    percentual_estabilizado: Decimal = Field(default=Decimal("0.00"), ge=0.00, le=100.00, description="Percentual de Estabilização")

class HistoricoFuncionalCreateSchema(HistoricoFuncionalBaseSchema):
    pass

class TabelaVencimentoMinResponse(BaseModel):
    codigo_vencimento: str
    nivel_grau: str
    valor_base: Decimal
    model_config = ConfigDict(from_attributes=True)

class HistoricoFuncionalResponse(HistoricoFuncionalBaseSchema):
    id: UUID
    vinculo_id: UUID
    tabela_vencimento: Optional[TabelaVencimentoMinResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CargoResponse(BaseModel):
    id: UUID
    nome: str
    tipo: TipoCargo
    carga_horaria_padrao: int

    model_config = ConfigDict(from_attributes=True)
