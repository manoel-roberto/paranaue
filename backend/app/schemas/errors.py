from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    """
    Modelo padrão para respostas de erro detalhadas retornadas pela API.
    """
    detail: str = Field(..., description="Mensagem explicativa sobre o erro ocorrido")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Mensagem detalhada sobre o erro (ex: credenciais incorretas, recurso não encontrado)."
            }
        }
    }

# Definições padronizadas de respostas HTTP de erro para uso nos decorators da API
HTTP_400_RESPONSE = {"model": ErrorResponse, "description": "Requisição inválida ou violação de regra de negócio (Bad Request)"}
HTTP_401_RESPONSE = {"model": ErrorResponse, "description": "Autenticação pendente ou falha nas credenciais (Unauthorized)"}
HTTP_403_RESPONSE = {"model": ErrorResponse, "description": "Permissão insuficiente para acessar o recurso (Forbidden)"}
HTTP_404_RESPONSE = {"model": ErrorResponse, "description": "O recurso solicitado não foi encontrado (Not Found)"}
HTTP_422_RESPONSE = {"description": "Entrada inválida. Erro de validação do Pydantic (Unprocessable Entity)"}
