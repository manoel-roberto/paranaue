from pydantic import BaseModel, Field

class TokenResponse(BaseModel):
    """
    Schema para representação da resposta de autenticação bem-sucedida contendo o token de acesso.
    """
    access_token: str = Field(..., description="Token de acesso JWT (JSON Web Token) gerado para a sessão")
    token_type: str = Field(..., description="Tipo do token de autenticação, sendo obrigatoriamente 'bearer'")
    expira_em_segundos: int = Field(..., description="Tempo de expiração do token de acesso em segundos")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcwMDAwMDAwMH0...",
                "token_type": "bearer",
                "expira_em_segundos": 1800
            }
        }
    }
