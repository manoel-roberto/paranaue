from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.servidores import router as servidores_router
from app.api.v1.parametros import router as parametros_router
from app.api.v1.vencimentos import router as vencimentos_router
from app.api.v1.gstu import router as gstu_router
from app.api.v1.simulacao import router as simulacao_router
from app.core.bootstrap import init_initial_data
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa dados do banco como perfil 'ADMINISTRADOR' e usuário master
    await init_initial_data()
    yield

app = FastAPI(
    title="Sistema de Impacto Financeiro UEFS",
    lifespan=lifespan,
    description="""
    ### API do Sistema de Impacto Financeiro e Evolução de Carreira da UEFS

    Esta API fornece endpoints para gerenciamento de servidores, parametrização salarial (tabelas de vencimento e GSTU) e execução de simulações de impacto financeiro decorrentes de alterações de cargos ou vencimentos.

    **Documentação Relacionada:**
    * [Portal Oficial da UEFS](https://www.uefs.br)
    * [Especificação OpenAPI (JSON)](/openapi.json)
    * [Documentação Interativa (Swagger UI)](/docs)
    * [Documentação Alternativa (ReDoc)](/redoc)
    """,
    version="1.0.0",
    contact={
        "name": "Núcleo de Tecnologia da Informação - UEFS",
        "url": "https://www.uefs.br",
        "email": "nti@uefs.br",
    },
    openapi_tags=[
        {
            "name": "Autenticação",
            "description": "Operações para autenticação de usuários e geração de tokens de acesso JWT.",
        },
        {
            "name": "Servidores",
            "description": "Gerenciamento e cadastro de servidores públicos da UEFS.",
        },
        {
            "name": "Parâmetros Salariais",
            "description": "Manutenção das tabelas de referência de vencimentos base e gratificações GSTU.",
        },
        {
            "name": "Simulação de Impacto",
            "description": "Cálculo e exportação em PDF de cenários de evolução funcional e impactos financeiros.",
        },
    ]
)

# Configuração do Middleware de CORS para integração com o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os roteadores da API
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(servidores_router, prefix="/api/v1/servidores", tags=["Servidores"])
app.include_router(parametros_router, prefix="/api/v1/parametros", tags=["Parâmetros Salariais"])
app.include_router(vencimentos_router, prefix="/api/v1/vencimentos", tags=["Parâmetros Salariais"])
app.include_router(gstu_router, prefix="/api/v1/gstu", tags=["Parâmetros Salariais"])
app.include_router(simulacao_router, prefix="/api/v1/simulacao", tags=["Simulação de Impacto"])
