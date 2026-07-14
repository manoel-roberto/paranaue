# Especificação de Arquitetura de Backend

**Sistema de Cálculo de Impacto Financeiro da UEFS**  
**Autor:** Arquiteto de Software Sênior  
**Data:** 10 de Julho de 2026  
**Versão:** 1.0 - Oficial  

---

## 1. Stack Tecnológica Base

Para atender aos requisitos de **simplicidade**, **facilidade de manutenção**, **precisão matemática** e **conteinerização**, definimos a seguinte stack para o microsserviço de backend:

```mermaid
graph TD
    Client[Clientes REST / Frontend] -->|HTTP / JSON| FastAPI[FastAPI 0.110+ <br> Python 3.11+]
    FastAPI -->|Pydantic v2 DTOs| Pydantic[Validação e Serialização]
    FastAPI -->|Injeção de Dependência| Auth[JWT / RBAC]
    FastAPI -->|ContextVars| Context[Session Context: User & IP]
    FastAPI -->|SQLAlchemy 2.0 Async| DB[PostgreSQL 15+]
    Context -->|Trigger after_begin| DB
```

### Detalhamento e Raciocínio das Escolhas

1. **Python 3.11+ (Runtime)**:
   * **Precisão Decimal Nativa**: O módulo `decimal` de Python é indispensável para evitar erros catastróficos de ponto flutuante em folhas de pagamento (ex: `0.1 + 0.2` resultando em `0.30000000000000004` com floats). Ele se integra nativamente ao tipo `DECIMAL` do PostgreSQL.
   * **Performance e Legibilidade**: O Python 3.11 traz melhorias substanciais de performance (entre 10% e 60% mais rápido que a versão 3.10) e tracebacks mais limpos, facilitando o diagnóstico em produção.
   
2. **FastAPI (Web Framework)**:
   * **Alta Performance Assíncrona**: Desenvolvido sobre Starlette e Uvicorn (ASGI), oferece tempos de resposta de altíssimo nível, ideais para processamento concorrente.
   * **Validação Nativa com Pydantic v2**: Garante tipagem estática e validação em tempo de execução no limite da API. O payload inválido é rejeitado antes de alcançar as camadas de serviço ou banco de dados.
   * **OpenAPI Automático (Swagger)**: Reduz o atrito entre equipes gerando documentação interativa e contratos de API atualizados em tempo real em `/docs`.
   * **Injeção de Dependências**: Sistema limpo e robusto baseado em funções (`Depends`), facilitando testes unitários por meio de overrides.

3. **SQLAlchemy 2.0 (ORM)**:
   * **API Moderna e Type-Safe**: A versão 2.0 simplifica as queries, adota tipagem estática integrada com Mypy/Pydantic e suporta transações assíncronas nativas (`AsyncSession`).
   * **Desempenho em Lote**: Permite tanto a abstração de mapeamento de objetos quanto a execução de instruções SQL brutas e bulk inserts altamente performáticos para a simulação de lotes (RF005).

4. **Docker (`python:3.11-slim` como Imagem Base)**:
   * **Redução da Superfície de Ataque**: Imagem desprovida de pacotes e compiladores desnecessários (gerando um tamanho reduzido de ~120MB), ideal para ambientes de produção seguros.
   * **Reprodutibilidade**: Isolamento total de bibliotecas de sistema, garantindo comportamento consistente localmente e nos servidores de nuvem.

---

## 2. Estrutura de Diretórios (Design Pattern)

Adotamos uma variação simplificada de **Layered Architecture (Arquitetura em Camadas)** para garantir que as rotas HTTP (camada de transporte) estejam totalmente separadas das regras de negócio (camada de domínio e serviços).

```
app/
├── main.py                  # Inicialização da aplicação FastAPI e middlewares
├── core/                    # Configurações globais e cross-cutting concerns
│   ├── config.py            # Carregamento e validação de variáveis de ambiente (.env)
│   ├── database.py          # Configuração do Engine SQLAlchemy e Session Maker assíncrono
│   └── security.py          # Utilitários de criptografia (hashing e geração de JWT)
├── api/                     # Camada de Apresentação / Transporte (Controllers)
│   ├── deps.py              # Injeção de dependências compartilhadas (Session DB, Auth)
│   └── v1/                  # Versionamento da API pública
│       ├── auth.py          # Rotas de Autenticação e Login
│       ├── servidores.py    # Rotas de cadastro e histórico funcional de servidores
│       ├── parametros.py    # Rotas para tabelas salariais e parâmetros
│       └── simulacoes.py    # Rotas do motor de simulações financeiras
├── models/                  # Camada de Persistência (Modelos de Dados do Banco)
│   ├── base.py              # Declarative Base comum para o SQLAlchemy
│   ├── servidor.py          # Entidades: Servidor, Vinculo, Averbacao
│   ├── tabelas.py           # Entidades: TabelaVencimento, TabelaGstu, TabelaComissao
│   ├── usuario.py           # Entidades: Usuario, Perfil (RBAC)
│   └── simulacao.py         # Entidades: Simulacao, SimulacaoItem, AuditLog
├── schemas/                 # Camada de Validação / DTOs (Data Transfer Objects)
│   ├── auth.py              # Pydantic Schemas de login, tokens e claims
│   ├── servidor.py          # Pydantic Schemas para Servidor e Vínculo
│   ├── parametro.py         # Pydantic Schemas para tabelas de vencimento/vigência
│   └── simulacao.py         # Pydantic Schemas para controle de entrada/saída de simulações
├── services/                # Camada de Domínio / Regras de Negócio
│   ├── calculador.py        # Algoritmos puros de cálculo financeiro (ATS, Insalubridade, GSTU)
│   ├── servidor.py          # Orquestração de regras de admissão e evolução funcional
│   └── simulacao.py         # Orquestração do processamento de simulações (Individual/Lote)
└── tests/                   # Testes Automatizados (Padrão AAA)
    ├── conftest.py          # Fixtures do Pytest (Banco de testes efêmero)
    ├── test_calculos.py     # Testes unitários do motor matemático
    └── test_api/            # Testes de integração de endpoints
```

### Responsabilidades de Cada Camada

* **Rotas (`app/api/v1/`)**: Funcionam como roteadores e controladores rápidos. Capturam a requisição, validam via Pydantic Schemas, extraem o contexto de autenticação/auditoria e delegam a execução para a camada de `services`. Retornam a resposta formatada com os devidos códigos de status HTTP. **Nenhuma lógica de cálculo financeiro ou consulta SQL complexa é escrita nesta camada.**
* **Serviços (`app/services/`)**: Contêm as regras de negócio puras do sistema. O arquivo `calculador.py` lida com o motor matemático de cálculo salarial, garantindo isolamento da infraestrutura de banco de dados (pode ser testado de forma puramente unitária). Os demais serviços gerenciam transações, orquestram mutações de dados e regras de consistência temporal.
* **Modelos (`app/models/`)**: Mapeamento objeto-relacional direto para o PostgreSQL. Definem tipos, chaves, relacionamentos SQLAlchemy e garantem tipagem estática no Python.
* **Schemas (`app/schemas/`)**: Definem os limites de dados da API. Limitam o que o cliente pode enviar e o que o servidor devolve (escondendo campos sensíveis como hashes de senha).

---

## 3. Estratégia de Integração de Auditoria (RNF006)

O banco de dados possui triggers em PL/pgSQL que interceptam alterações em tabelas críticas e consultam os parâmetros de sessão `app.current_user_id` e `app.current_ip` para registrar as alterações na tabela `audit_log` de forma atômica.

Para integrar esta capacidade sem expor lógica de banco nas rotas ou forçar os desenvolvedores a executarem queries manuais de `SET` a cada operação, desenhamos uma estratégia de injeção automática de contexto usando **FastAPI Dependencies**, **Python ContextVars** e **SQLAlchemy Events**.

```
Request HTTP ──> FastAPI Router (Captura IP e Token)
                     │
                     ▼
             deps.get_audit_context() ──> Armazena no ContextVar (Thread/Async Safe)
                     │
                     ▼
             SQLAlchemy Connection
                     │
              (Evento: after_begin)
                     │
                     ▼
             Executa na Transação: 
             SET LOCAL app.current_user_id = '...';
             SET LOCAL app.current_ip = '...';
                     │
                     ▼
             SQLAlchemy Operation (Insert/Update/Delete)
                     │
                     ▼
             PostgreSQL Trigger -> fn_auditar_alteracao_parametro()
```

### Implementação Conceitual

#### 1. Gerenciamento do Contexto Global (`app/core/context.py`)

Usamos `ContextVar` para manter as variáveis de contexto seguras no fluxo assíncrono do FastAPI (isolando cada requisição concorrente).

```python
import contextvars
from uuid import UUID

# Variáveis isoladas por requisição assíncrona (Coroutine-safe)
current_user_id: contextvars.ContextVar[UUID | None] = contextvars.ContextVar("current_user_id", default=None)
current_ip: contextvars.ContextVar[str] = contextvars.ContextVar("current_ip", default="0.0.0.0")
```

#### 2. Extração do Contexto na Requisição (`app/api/deps.py`)

Uma dependência FastAPI extrai as informações do usuário logado (via token JWT) e o IP do cabeçalho da requisição, injetando nos `ContextVars`.

```python
from fastapi import Depends, Request
from app.core import context
from app.services.auth import get_current_user  # Dependency de validação do JWT

async def set_request_context(
    request: Request,
    current_user = Depends(get_current_user)
) -> None:
    # 1. Configura o ID do usuário autenticado no ContextVar
    context.current_user_id.set(current_user.id)
    
    # 2. Configura o IP de origem (com fallback para proxy reverso)
    ip_header = request.headers.get("x-forwarded-for")
    ip = ip_header.split(",")[0].strip() if ip_header else (request.client.host if request.client else "0.0.0.0")
    context.current_ip.set(ip)
```

#### 3. Injeção Automática no SQLAlchemy (`app/core/database.py`)

Escutamos o evento `after_begin` da `Session` do SQLAlchemy. Sempre que uma nova transação for aberta (mesmo que haja múltiplos commits ou rollbacks na mesma requisição), injetamos as variáveis no escopo local da transação do PostgreSQL.

```python
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from app.core import context

@event.listens_for(Session, "after_begin")
def set_postgres_audit_variables(session, transaction, connection):
    # Obtém os valores atuais definidos no ContextVar do fluxo da requisição
    user_id = context.current_user_id.get()
    ip_origem = context.current_ip.get()

    # Executa a configuração local no PostgreSQL
    # SET LOCAL dura exatamente até o COMMIT ou ROLLBACK da transação ativa
    if user_id:
        connection.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": str(user_id)}
        )
    connection.execute(
        text("SET LOCAL app.current_ip = :ip"),
        {"ip": ip_origem}
    )
```

#### 4. Uso Limpo no Endpoint

Com isso, a rota fica completamente livre de código de auditoria. Ela apenas usa a dependência para definir o contexto:

```python
@router.post("/parametros/vencimentos", response_model=VencimentoResponse, status_code=201)
async def criar_vencimento(
    payload: VencimentoCreateSchema,
    db: AsyncSession = Depends(get_db),
    _context = Depends(set_request_context)  # Garante que os ContextVars sejam preenchidos
):
    # Qualquer operação feita via db aqui será automaticamente auditada pelo PostgreSQL
    return await parametros_service.criar_vencimento(db, payload)
```

---

## 4. Mapeamento dos Endpoints da API

Abaixo estão definidos os endpoints RESTful organizados em 4 subgrupos principais. Todos os valores salariais transitam na API como `Decimal` (mapeado pelo Pydantic para strings ou floats controlados na serialização) para preservar a precisão financeira.

### 4.1. Grupo: Autenticação (`/api/v1/auth`)

Gerencia o acesso ao sistema baseado em credenciais, retornando tokens JWT com tempo de expiração definido.

* **`POST /api/v1/auth/login`**
  * **Descrição**: Autentica o usuário e retorna o token de acesso.
  * **Payload Entrada (`LoginRequest`)**:
    ```json
    {
      "username": "usuario_financeiro",
      "senha_plain": "SenhaSegura123!"
    }
    ```
  * **Payload Saída (`TokenResponse` - HTTP 200)**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expira_em_segundos": 3600
    }
    ```

---

### 4.2. Grupo: Gestão de Servidores e Histórico (`/api/v1/servidores`)

Permite a visualização, cadastro de servidores, vínculos, registros de averbações e histórico de evolução de carreira.

* **`GET /api/v1/servidores`**
  * **Descrição**: Lista servidores cadastrados com suporte a paginação e busca por nome/CPF.
  * **Query Params**: `skip=0`, `limit=50`, `nome="Manoel"`, `cpf="12345678901"`
  * **Payload Saída (`PaginatedServidoresResponse` - HTTP 200)**:
    ```json
    {
      "total": 1,
      "skip": 0,
      "limit": 50,
      "itens": [
        {
          "id": "a3b9f4e2-6789-4b12-9c34-bcde56789012",
          "cpf": "12345678901",
          "nome": "Manoel Silva"
        }
      ]
    }
    ```

* **`POST /api/v1/servidores`**
  * **Descrição**: Cadastra um novo servidor no sistema.
  * **Payload Entrada (`ServidorCreateSchema`)**:
    ```json
    {
      "cpf": "12345678901",
      "nome": "Manoel Silva",
      "data_nascimento": "1985-05-15"
    }
    ```
  * **Payload Saída (`ServidorResponse` - HTTP 201)**:
    ```json
    {
      "id": "a3b9f4e2-6789-4b12-9c34-bcde56789012",
      "cpf": "12345678901",
      "nome": "Manoel Silva",
      "data_nascimento": "1985-05-15"
    }
    ```

* **`POST /api/v1/servidores/{id}/vinculos`**
  * **Descrição**: Cadastra um novo vínculo contratual/funcional associado ao servidor.
  * **Payload Entrada (`VinculoCreateSchema`)**:
    ```json
    {
      "matricula": "90001234",
      "data_admissao": "2015-02-01",
      "cargo_id": "c1a2e3f4-5678-90ab-cdef-1234567890ab",
      "regime_previdenciario": "BAPREV_REGIME_PROPRIO",
      "participante_prev_complementar": false,
      "aliquota_coparticipacao_complementar": 0.00,
      "tipo_vinculo": "ESTATUTARIO"
    }
    ```
  * **Payload Saída (`VinculoResponse` - HTTP 201)**:
    ```json
    {
      "id": "e4f5a6b7-8901-2345-6789-0123456789ab",
      "servidor_id": "a3b9f4e2-6789-4b12-9c34-bcde56789012",
      "matricula": "90001234",
      "data_admissao": "2015-02-01",
      "cargo_id": "c1a2e3f4-5678-90ab-cdef-1234567890ab",
      "regime_previdenciario": "BAPREV_REGIME_PROPRIO",
      "participante_prev_complementar": false,
      "aliquota_coparticipacao_complementar": 0.00,
      "tipo_vinculo": "ESTATUTARIO",
      "ativo": true
    }
    ```

* **`GET /api/v1/servidores/vinculos/{vinculo_id}/historico`**
  * **Descrição**: Retorna a linha do tempo funcional e salarial cronológica de um vínculo específico.
  * **Payload Saída (`HistoricoFuncionalTimelineResponse` - HTTP 200)**:
    ```json
    [
      {
        "id": "f8a9b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
        "data_inicio": "2015-02-01",
        "data_fim": "2020-12-31",
        "tabela_vencimento": {
          "codigo_vencimento": "ANALISTA-CL-A",
          "nivel_grau": "I",
          "valor_base": 4200.00
        },
        "insalubridade_percentual": 0.00,
        "cet_percentual": 0.00,
        "vpess_valor": 0.00
      },
      {
        "id": "d7c8b9a0-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
        "data_inicio": "2021-01-01",
        "data_fim": "9999-12-31",
        "tabela_vencimento": {
          "codigo_vencimento": "ANALISTA-CL-B",
          "nivel_grau": "II",
          "valor_base": 5100.00
        },
        "insalubridade_percentual": 20.00,
        "cet_percentual": 30.00,
        "vpess_valor": 250.00
      }
    ]
    ```

* **`POST /api/v1/servidores/vinculos/{vinculo_id}/historico`**
  * **Descrição**: Registra um novo evento funcional na vida do servidor (como promoção ou reajuste de gratificações). O backend valida a inexistência de sobreposição e atualiza a vigência anterior fechando o intervalo.
  * **Payload Entrada (`HistoricoFuncionalCreateSchema`)**:
    ```json
    {
      "data_inicio": "2026-08-01",
      "tabela_vencimento_id": "df56b219-58b2-4d22-921a-642676bfa2e2",
      "tabela_gstu_id": "00000000-0000-0000-0000-000000000000",
      "cet_percentual": 30.00,
      "insalubridade_percentual": 20.00,
      "vpess_valor": 250.00,
      "percentual_estabilizado": 0.00
    }
    ```
  * **Payload Saída (`HistoricoFuncionalResponse` - HTTP 201)**: Retorna o registro criado com sucesso.

* **`POST /api/v1/servidores/vinculos/{vinculo_id}/averbacoes`**
  * **Descrição**: Adiciona tempo de serviço externo averbado para fins de anuênio/licença prêmio (ATS).
  * **Payload Entrada (`AverbacaoCreateSchema`)**:
    ```json
    {
      "dias_averbados": 365,
      "tipo_averbacao": "ATS",
      "data_averbacao": "2026-07-10",
      "processo_numero": "UEFS-2026-00123"
    }
    ```
  * **Payload Saída (`AverbacaoResponse` - HTTP 201)**.

---

### 4.3. Grupo: Parâmetros Salariais (`/api/v1/parametros`)

Responsável pela gestão dos parâmetros base do sistema (tabelas salariais de vencimento básico, gratificação GSTU e símbolos de comissão). Todas as operações de criação (POST) ou alteração aqui disparam os triggers de auditoria do banco.

* **`POST /api/v1/parametros/vencimentos`**
  * **Descrição**: Registra um valor salarial de vencimento-base para uma classe/grau.
  * **Payload Entrada (`VencimentoCreateSchema`)**:
    ```json
    {
      "codigo_vencimento": "ANALISTA-CL-C",
      "classe": "Classe C",
      "nivel_grau": "III",
      "carga_horaria": 40,
      "valor_base": 6500.00,
      "data_inicio_vigencia": "2026-01-01",
      "data_fim_vigencia": "9999-12-31"
    }
    ```
  * **Payload Saída (`VencimentoResponse` - HTTP 201)**.

* **`POST /api/v1/parametros/gstu`**
  * **Descrição**: Registra novos valores para a Gratificação por Suporte Técnico Universitário (GSTU).
  * **Payload Entrada (`GstuCreateSchema`)**:
    ```json
    {
      "codigo_gstu": "GSTU-ANALISTA-M",
      "grau": "Mestrado",
      "referencia": "Ref 1",
      "valor_gstu": 1200.00,
      "data_inicio_vigencia": "2026-01-01",
      "data_fim_vigencia": "9999-12-31"
    }
    ```
  * **Payload Saída (`GstuResponse` - HTTP 201)**.

---

### 4.4. Grupo: Motor de Simulação (`/api/v1/simulacoes`)

Controla a execução dos cálculos salariais prospectivos. Permite criar cenários (individuais ou globais em lote) e processar as projeções financeiras.

* **`POST /api/v1/simulacoes`**
  * **Descrição**: Cria um cabeçalho/cenário de simulação.
  * **Payload Entrada (`SimulacaoCreateSchema`)**:
    ```json
    {
      "descricao": "Projeção de Promoção Geral Analistas 2026",
      "tipo": "LOTE"
    }
    ```
  * **Payload Saída (`SimulacaoResponse` - HTTP 201)**:
    ```json
    {
      "id": "7f8a9b2c-3d4e-5f6a-7b8c-9d0e1f2a3b4c",
      "descricao": "Projeção de Promoção Geral Analistas 2026",
      "tipo": "LOTE",
      "status": "RASCUNHO",
      "criado_por_usuario_id": "a3b9f4e2-6789-4b12-9c34-bcde56789012",
      "data_criacao": "2026-07-10T11:55:00"
    }
    ```

* **`POST /api/v1/simulacoes/{id}/itens`**
  * **Descrição**: Associa um vínculo a uma simulação, injetando as alterações funcionais propostas para o cenário.
  * **Payload Entrada (`SimulacaoItemCreateSchema`)**:
    ```json
    {
      "vinculo_id": "e4f5a6b7-8901-2345-6789-0123456789ab",
      "data_vigencia_proposta": "2026-09-01",
      "mes_gozo_ferias_proposto": 11,
      "alteracao_funcional_proposta": {
        "nova_tabela_vencimento_id": "df56b219-58b2-4d22-921a-642676bfa2e2",
        "novo_percentual_cet": 45.00,
        "nova_insalubridade": 20.00
      },
      "justificativa_requisitos": "Servidor apto à promoção automática por tempo."
    }
    ```
  * **Payload Saída (`SimulacaoItemResponse` - HTTP 201)**: Retorna o item cadastrado com os dados funcionais originais injetados em `dados_origem_json` e `status=RASCUNHO`.

* **`POST /api/v1/simulacoes/{id}/processar`**
  * **Descrição**: Dispara o cálculo salarial. 
    * Se `tipo == INDIVIDUAL`, o processamento ocorre imediatamente de forma síncrona.
    * Se `tipo == LOTE`, o endpoint delega a tarefa a um thread ou worker em segundo plano (`BackgroundTasks`), altera o status da simulação para `PROCESSANDO` e retorna HTTP 202 (Accepted).
  * **Isolamento de Concorrência**: Este processo executa no nível de isolamento de transação **`REPEATABLE READ`** do PostgreSQL para garantir consistência salarial transversal durante toda a execução.
  * **Payload Saída (`SimulacaoStatusResponse` - HTTP 202)**:
    ```json
    {
      "simulacao_id": "7f8a9b2c-3d4e-5f6a-7b8c-9d0e1f2a3b4c",
      "status": "PROCESSANDO",
      "mensagem": "Cálculo de impacto financeiro em lote iniciado em segundo plano."
    }
    ```

* **`GET /api/v1/simulacoes/{id}/itens`**
  * **Descrição**: Retorna os detalhes de impacto de cada item da simulação processada.
  * **Payload Saída (`List[SimulacaoItemResultSchema]` - HTTP 200)**:
    ```json
    [
      {
        "id": "b7c8d9e0-f1a2-3b4c-5d6e-7f8a9b0c1d2e",
        "vinculo_id": "e4f5a6b7-8901-2345-6789-0123456789ab",
        "dados_origem_json": {
          "salario_base": 5100.00,
          "ats": 510.00,
          "gstu": 1200.00,
          "custo_total": 6810.00
        },
        "dados_propostos_json": {
          "salario_base": 6500.00,
          "ats": 650.00,
          "gstu": 1200.00,
          "custo_total": 8350.00
        },
        "resultado_calculo_json": {
          "diferenca_mensal": 1540.00,
          "impacto_anual_com_13_e_ferias": 20533.33,
          "detalhamento_rubricas": {
            "vencimento_base_delta": 1400.00,
            "ats_delta": 140.00,
            "previdencia_patronal_delta": 338.80
          }
        }
      }
    ]
    ```

---

## 5. Estratégia de Conteinerização (Docker)

O empacotamento do backend visa a máxima portabilidade, segurança a nível de processo e otimização de imagem (redução de camadas desnecessárias).

### 5.1. Dockerfile (Orientado a Produção)

Abaixo está a estrutura declarada para o Dockerfile, aplicando o padrão de **Image Build em Duas Fases (Multi-stage Build)** e execução sem privilégios de administrador (non-root).

```dockerfile
# ============================================================================
# FASE 1: Builder (Instalação de dependências e build de pacotes)
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Instala ferramentas mínimas de sistema caso precise compilar bibliotecas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalação e cache de dependências de forma otimizada
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# FASE 2: Runner (Imagem final de execução ultra-leve)
# ============================================================================
FROM python:3.11-slim as runner

WORKDIR /app

# Instala apenas dependências de tempo de execução (runtime) do PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copia as dependências Python compiladas/instaladas na fase anterior
COPY --from=builder /root/.local /root/.local
COPY . /app

# Adiciona o caminho de pacotes instalados ao PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Criação de usuário não-privilegiado (Segurança contra escalada de privilégios)
RUN groupadd -g 10001 appgroup && \
    useradd -r -u 10001 -g appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Execução assíncrona orientada a produção
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 5.2. Configuração de Variáveis de Ambiente (`.env`)

Toda a infraestrutura do microsserviço é parametrizada em tempo de execução através de variáveis de ambiente. O arquivo `.env` local contém:

```env
# Configurações do Servidor
APP_ENV=production
PROJECT_NAME="Sistema de Impacto Financeiro UEFS"
SECRET_KEY="sua_chave_secreta_jwt_de_producao_super_segura"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Configurações do Banco de Dados
POSTGRES_SERVER=localhost
POSTGRES_USER=uefs_user
POSTGRES_PASSWORD=uefs_password
POSTGRES_DB=uefs_financeiro
POSTGRES_PORT=5432

# URL de Conexão SQLAlchemy Assíncrona
DATABASE_URL="postgresql+asyncpg://uefs_user:uefs_password@localhost:5432/uefs_financeiro"
```

No ecossistema FastAPI, essas variáveis são capturadas, tipadas e validadas através da biblioteca `pydantic-settings`, gerando um erro de inicialização do container imediatamente (fail-fast) caso algum parâmetro esteja incorreto ou ausente.

### 5.3. Docker Compose para Desenvolvimento Local

Para orquestrar o backend FastAPI e o banco de dados PostgreSQL com suas extensões de forma imediata e reprodutível:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: uefs_db_local
    environment:
      POSTGRES_USER: uefs_user
      POSTGRES_PASSWORD: uefs_password
      POSTGRES_DB: uefs_financeiro
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      # Injeta os scripts de criação do banco e triggers de auditoria gerados na etapa de DB
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U uefs_user -d uefs_financeiro"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      target: runner
    container_name: uefs_backend_local
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://uefs_user:uefs_password@db:5432/uefs_financeiro
      - SECRET_KEY=desenvolvimento_seguro_key
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
```
