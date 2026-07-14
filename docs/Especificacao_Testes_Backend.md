# Especificação de Testes e Qualidade do Backend

**Sistema de Cálculo de Impacto Financeiro da UEFS**  
**Autor:** Engenheiro de Qualidade de Software Sênior & Arquiteto Python  
**Data:** 10 de Julho de 2026  
**Versão:** 1.0 - Oficial  

---

## 1. Metodologia e Ciclo de Vida (TDD)

A regra de ouro para a construção e evolução do backend deste sistema é a adoção obrigatória do **TDD (Test-Driven Development)**. Qualquer agente ou desenvolvedor está proibido de implementar código de produção (serviços, rotas, modelos) sem antes ter um teste correspondente implementado.

### 1.1. O Ciclo de TDD Obrigatório

O ciclo de desenvolvimento de qualquer funcionalidade ou correção de bug deve seguir estritamente as três etapas:

```
 🔴 RED (Falhar)
   │  Escrever um teste automatizado que expresse o comportamento esperado.
   │  Executar o teste e garantir que ele FALHE (pela ausência do código ou asserção incorreta).
   ▼
 🟢 GREEN (Passar)
   │  Escrever a quantidade MÍNIMA de código de produção estritamente necessária para fazer o teste passar.
   │  Executar os testes novamente e garantir que todos passem (Fase de validação do comportamento).
   ▼
 🔵 REFACTOR (Refatorar)
      Melhorar a qualidade do código (design, legibilidade, duplicidade) mantendo todos os testes VERDES.
      Executar o conjunto de testes a cada alteração incremental.
```

### 1.2. Estrutura de Testes: Padrão AAA (Arrange, Act, Assert)

Toda e qualquer função de teste implementada neste projeto deve ser estruturada visual e logicamente em três blocos bem definidos, separados por uma linha em branco:

* **Arrange (Preparação)**: Configuração do cenário, inicialização de mocks, instanciação de objetos e preparação dos dados de entrada.
* **Act (Ação)**: Execução da unidade de código sob teste (chamada do método, função ou endpoint).
* **Assert (Verificação)**: Comparação do resultado obtido com o resultado esperado e asserção de efeitos colaterais.

#### Exemplo de Estrutura AAA:
```python
def test_deve_calcular_ats_com_proporcionalidade():
    # Arrange (Preparação)
    vencimento_base = Decimal("5000.00")
    anos_servico = 5
    calculador = CalculadorSalario()
    percentual_ats_esperado = Decimal("0.05")  # 1% por ano (exemplo)
    valor_ats_esperado = Decimal("250.00")

    # Act (Ação)
    resultado = calculador.calcular_ats(vencimento_base, anos_servico)

    # Assert (Verificação)
    assert resultado.percentual == percentual_ats_esperado
    assert resultado.valor == valor_ats_esperado
```

---

## 2. Ferramentas e Configuração Base

### 2.1. Frameworks Adotados
* **`pytest`**: Orquestrador e executor principal de testes.
* **`pytest-asyncio`**: Plugin para suporte à execução assíncrona (`async/await`) dos testes.
* **`httpx`**: Utilizado para realizar chamadas HTTP assíncronas contra a API FastAPI nos testes de integração.
* **`SQLAlchemy` (Async)**: Driver assíncrono para interações com o banco de dados.

### 2.2. Estratégia de Isolamento de Banco de Dados
Para garantir a fidelidade do ambiente de testes ao ambiente de produção, **o uso de SQLite em memória está TERMINANTEMENTE PROIBIDO**.

#### Justificativa Técnica:
1. **JSONB**: O SQLite não possui suporte nativo completo e otimizado para operações avançadas do tipo `JSONB` do PostgreSQL, amplamente utilizado nos payloads e históricos do motor.
2. **Triggers PL/pgSQL**: O mecanismo de auditoria transacional utiliza triggers complexos escritos em PL/pgSQL que só executam no PostgreSQL.
3. **Restrições Temporais (GiST e daterange)**: As chaves de exclusão espacial/temporal (`EXCLUDE USING gist`) com `daterange` não são suportadas pelo SQLite.

#### Solução: PostgreSQL Dedicado com Rollback Automático
Será provisionado um banco de dados PostgreSQL exclusivo para testes (ex: `uefs_payroll_test`).
A cada teste executado, uma transação SQLAlchemy é iniciada. Ao final do teste, um `ROLLBACK` é disparado automaticamente. Isso garante:
* **Isolamento Total**: O banco nunca mantém estados de testes anteriores.
* **Velocidade**: Evita a recriação do schema de banco a cada teste individual (o schema é criado uma única vez no início da sessão de testes).

---

## 3. Estratégia por Camada (Pirâmide de Testes)

```
        /\          E2E (Poucos) - Fluxos críticos de ponta a ponta
       /  \
      /----\
     /      \       Integração (Médio) - Validar Schemas, Rotas API, DTOs e Regras de Transação
    /--------\
   /          \     Banco de Dados e Auditoria - Validar Triggers, Restrições GiST e ContextVars
  /------------\
 /              \   Unitários (Muitos) - Lógica pura do calculador.py (Sem DB, Sem HTTP, Alta Performance)
/________________\
```

### 3.1. Testes Unitários: Camada de Domínio (`app/services/calculador.py`)
Esta camada lida com a matemática financeira do sistema. Por ser a mais crítica para a universidade, deve rodar de forma extremamente rápida e isolada.

* **Regras**:
  * **Zero Banco de Dados**: Nenhuma chamada ao banco deve ocorrer. Dados de tabelas de vencimento e GSTU devem ser fornecidos como instâncias puras de objetos do domínio ou mocks de dicionários.
  * **Tipagem Estrita**: Todos os valores devem usar `Decimal` e as asserções devem verificar arredondamentos e precisão centesimal.
  * **Precisão Matemática**: Garantir exatidão nos cálculos de Adicional por Tempo de Serviço (ATS), insalubridade, GSTU, estabilizações e proporcionalidade diária.

#### Exemplo de Teste Unitário Isolado:
```python
from decimal import Decimal
from app.services.calculador import calcular_folha_servidor
from app.schemas.calculo import ServidorDadosCalculo

def test_calcular_folha_com_insalubridade_e_ats():
    # Arrange
    dados = ServidorDadosCalculo(
        vencimento_base=Decimal("4200.00"),
        percentual_ats=Decimal("10.00"),  # 10% de ATS
        percentual_insalubridade=Decimal("20.00"),  # 20% sobre vencimento base
        dias_trabalhados=30
    )
    
    # Act
    resultado = calcular_folha_servidor(dados)
    
    # Assert
    assert resultado.valor_ats == Decimal("420.00")
    assert resultado.valor_insalubridade == Decimal("840.00")
    assert resultado.total_bruto == Decimal("5460.00")
```

### 3.2. Testes de Integração: Camada de Rotas da API (`/api/v1/...`)
Validar o fluxo de requisição/resposta HTTP, segurança (autenticação/autorização JWT) e contratos de dados (DTOs Pydantic).

* **Regras**:
  * O FastAPI deve rodar sob o `HTTPX AsyncClient`.
  * Os testes devem enviar payloads inválidos para garantir que o Pydantic retorna `HTTP 422 Unprocessable Entity` com detalhes dos erros.
  * As respostas devem bater com os schemas de saída cadastrados.

#### Exemplo de Teste de Integração (Validação de DTO):
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_nao_deve_permitir_cadastro_de_servidor_com_cpf_invalido(client: AsyncClient):
    # Arrange
    payload_invalido = {
        "cpf": "123.456",  # CPF muito curto e com caracteres especiais
        "nome": "João das Couves",
        "data_nascimento": "1990-01-01"
    }

    # Act
    response = await client.post("/api/v1/servidores", json=payload_invalido)

    # Assert
    assert response.status_code == 422
    detalhes = response.json()["detail"]
    assert any(err["loc"] == ["body", "cpf"] for err in detalhes)
```

### 3.3. Testes de Banco de Dados e Auditoria (CRÍTICO)
Validar se as restrições físicas (`EXCLUDE USING gist`) e os mecanismos de auditoria automática em nível de banco de dados (triggers e `ContextVars`) estão operando de forma correta e síncrona.

* **Cenário de Teste Obrigatório**:
  1. O teste inicia um escopo com contexto de auditoria simulado (usuário logado e IP de origem).
  2. Executa uma alteração de parâmetro crítico (ex: insere ou atualiza um valor na tabela `tabela_vencimento`).
  3. Commit transacional simulado.
  4. Realiza uma consulta direta na tabela `audit_log`.
  5. Asserta que o log foi criado, contendo os payloads (novo/antigo), ID do usuário que fez a ação, o IP mapeado e a operação realizada.

---

## 4. Fixtures e Mocks (`conftest.py`)

O gerenciamento de testes assíncronos que interagem com o banco de dados PostgreSQL e utilizam variáveis locais de fluxo (`contextvars`) requer atenção extrema devido ao funcionamento de tarefas assíncronas concorrentes do `asyncio`.

### 4.1. O Desafio dos `ContextVars` e `pytest-asyncio`

Por padrão, as variáveis de contexto (`ContextVars`) no Python propagam-se para corrotinas filhas dentro da mesma tarefa (`asyncio.Task`). No entanto, o `pytest-asyncio` cria e destrói loops de eventos de forma diferente, e os hooks ou fixtures podem rodar fora do contexto da tarefa que executa o teste propriamente dito.

Para garantir que o middleware do FastAPI (que roda dentro do escopo do request do HTTPX Client) ou as transações diretas executadas no teste compartilhem dos mesmos `ContextVars` do banco de dados, configuramos o gerenciador de contexto no `conftest.py` de modo a isolar e garantir a propagação.

### 4.2. Implementação do `conftest.py` de Referência

Abaixo está a infraestrutura obrigatória para o arquivo `app/tests/conftest.py`:

```python
import asyncio
import pytest
import pytest_asyncio
from uuid import UUID, uuid4
from typing import AsyncGenerator, Generator
from decimal import Decimal

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.main import app
from app.api.deps import get_db
from app.core import context
from app.models.base import Base

# Variável de ambiente de testes
DATABASE_URL_TEST = "postgresql+asyncpg://uefs_user:uefs_password@localhost:5432/uefs_financeiro_test"

# 1. Ajuste do Loop de Eventos do Asyncio para a Sessão
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Cria um loop de eventos único para toda a sessão de testes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 2. Inicialização do Banco de Dados
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Inicializa a engine de conexão e cria todas as tabelas uma única vez."""
    engine = create_async_engine(DATABASE_URL_TEST, echo=False)
    
    async with engine.begin() as conn:
        # Garante as extensões no banco de testes
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS btree_gist;'))
        
        # Recria tabelas
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    await engine.dispose()

# 3. Gerenciamento de Sessão de Teste com Rollback Automático
@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Cria uma sessão de banco de dados vinculada a uma transação.
    Ao final de cada teste, a transação sofre rollback automático.
    """
    async_session = async_sessionmaker(
        db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False, 
        autocommit=False, 
        autoflush=False
    )
    
    async with async_session() as session:
        # Iniciamos a transação explicitamente
        await session.begin()
        yield session
        # Rollback incondicional para garantir isolamento físico
        await session.rollback()

# 4. Injeção e Isolamento do Contexto de Auditoria para os Testes
@pytest_asyncio.fixture
async def mock_audit_context(db_session: AsyncSession) -> AsyncGenerator[tuple[UUID, str], None]:
    """
    Garante que o usuário de teste exista no banco, preenche os ContextVars
    de Usuário e IP no loop do pytest-asyncio e limpa após a execução.
    """
    test_user_id = uuid4()
    test_ip = "192.168.10.15"
    
    # Cria o usuário no banco para satisfazer a constraint de FK na tabela de auditoria
    await db_session.execute(
        text("""
            INSERT INTO usuario (id, username, senha_hash, nome, email, ativo)
            VALUES (:id, :username, :senha, :nome, :email, :ativo)
        """),
        {
            "id": test_user_id,
            "username": "test_user",
            "senha": "hash_seguro",
            "nome": "Usuário Teste Auditoria",
            "email": "teste_auditoria@uefs.br",
            "ativo": True
        }
    )
    
    # Define nos ContextVars do asyncio.Task atual do teste
    token_user = context.current_user_id.set(test_user_id)
    token_ip = context.current_ip.set(test_ip)
    
    yield test_user_id, test_ip
    
    # Reseta o contexto de forma limpa para evitar vazamentos entre testes
    context.current_user_id.reset(token_user)
    context.current_ip.reset(token_ip)

# 5. HTTP Client Assíncrono para Testar Rotas FastAPI
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Retorna o AsyncClient do HTTPX configurado para a aplicação FastAPI.
    Substitui a dependência do banco pela sessão transacional do teste.
    """
    # Override da injeção de dependência do FastAPI para usar a sessão do teste
    app.dependency_overrides[get_db] = lambda: db_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
        
    app.dependency_overrides.clear()
```

---

## 5. Casos de Teste Estruturados (Guias de Codificação)

Estes blocos descrevem exatamente o comportamento dos testes que devem ser implementados para validar o motor e o banco de dados.

### 5.1. Teste de Auditoria e Injeção de Contexto (Base e Triggers)
Este teste comprova que a auditoria está ocorrendo ao nível físico (PostgreSQL) usando as informações capturadas via `ContextVars` (definidas pelo middleware/fixture).

```python
import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.tabelas import TabelaVencimento

@pytest.mark.asyncio
async def test_deve_registrar_log_de_auditoria_automatico_no_banco(
    db_session: AsyncSession,
    mock_audit_context  # Injeta os ContextVars no loop de execução do teste
):
    # Arrange
    user_id, ip_origem = mock_audit_context
    
    # A fixture set_postgres_audit_variables é acionada no 'after_begin' do SQLAlchemy.
    # No entanto, como db_session já iniciou a transação no conftest, precisamos forçar
    # o SET LOCAL manualmente ou reconfigurar se a conexão já foi aberta.
    # Para testes diretos no banco sem passar pela rota (onde o request faz o setup),
    # simulamos o que o evento after_begin faria usando as variáveis injetadas:
    await db_session.execute(
        text("SET LOCAL app.current_user_id = :user_id"),
        {"user_id": str(user_id)}
    )
    await db_session.execute(
        text("SET LOCAL app.current_ip = :ip"),
        {"ip": ip_origem}
    )
    
    nova_tabela = TabelaVencimento(
        id=uuid4(),
        codigo_vencimento="VENC-TESTE-AUDIT",
        classe="Classe Teste",
        nivel_grau="G-I",
        carga_horaria=40,
        valor_base=Decimal("3500.00"),
        data_inicio_vigencia="2026-07-10",
        data_fim_vigencia="9999-12-31"
    )
    
    # Act
    db_session.add(nova_tabela)
    await db_session.flush()  # Flush na transação do teste (mantendo rollback)
    
    # Assert
    # Buscamos a auditoria correspondente ao ID do registro
    query = text("SELECT * FROM audit_log WHERE registro_id = :id")
    result = await db_session.execute(query, {"id": nova_tabela.id})
    log = result.mappings().first()
    
    assert log is not None
    assert log["tabela_afetada"] == "tabela_vencimento"
    assert log["operacao"] == "INSERT"
    assert log["usuario_id"] == user_id  # Comparação direta de objetos UUID
    assert log["ip_origem"] == ip_origem
    assert log["payload_novo"]["codigo_vencimento"] == "VENC-TESTE-AUDIT"
```

### 5.2. Teste de Sobreposição Temporal (Restrições de Histórico no DB)
Garante que chaves de exclusão temporais impeçam registros conflitantes.

```python
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.tabelas import TabelaVencimento

@pytest.mark.asyncio
async def test_nao_deve_permitir_sobreposicao_de_vigencias_salariais(db_session: AsyncSession):
    # Arrange
    vencimento_id_1 = uuid4()
    vencimento_id_2 = uuid4()
    
    # Vigência 1: 01/01/2026 a 31/12/2026
    tabela_1 = TabelaVencimento(
        id=vencimento_id_1,
        codigo_vencimento="SOBREPO-01",
        classe="Classe A",
        nivel_grau="I",
        carga_horaria=40,
        valor_base=Decimal("4000.00"),
        data_inicio_vigencia="2026-01-01",
        data_fim_vigencia="2026-12-31"
    )
    
    # Vigência 2: 01/07/2026 a 31/12/2027 (Conflita com o período de tabela_1)
    tabela_2 = TabelaVencimento(
        id=vencimento_id_2,
        codigo_vencimento="SOBREPO-01",  # Mesmo código salarial
        classe="Classe A",
        nivel_grau="I",
        carga_horaria=40,
        valor_base=Decimal("4500.00"),
        data_inicio_vigencia="2026-07-01",
        data_fim_vigencia="2027-12-31"
    )
    
    # Act
    db_session.add(tabela_1)
    await db_session.flush()
    
    # Assert
    db_session.add(tabela_2)
    with pytest.raises(IntegrityError) as exc_info:
        await db_session.flush()
        
    assert "exclude_tabela_vencimento_overlap" in str(exc_info.value)
```

---

## 6. Cobertura Mínima e Critérios de Aceitação para Homologação

A suite de testes do backend só será aceita em produção se cumprir os seguintes limites rigorosos:

| Métrica | Meta Mínima | Foco |
|---|---|---|
| **Cobertura Global de Código** | 90% | Todo o microsserviço |
| **Cobertura da Camada de Serviços** | 100% | `calculador.py` e motores de regras |
| **Cobertura de Rotas e DTOs** | 85% | Validação de endpoints e tratamento de erros |
| **Execução Unitária Individual** | < 50ms | Rapidez no ciclo RED-GREEN |

### Checklist de Revisão de Código (Quality Gate)
- [ ] O código implementado foi precedido por testes que falharam?
- [ ] Todos os testes novos e antigos estão passando (Green)?
- [ ] O padrão AAA foi explicitamente estruturado e legível?
- [ ] Mocks do banco de dados foram mantidos estritamente na camada unitária?
- [ ] Todos os valores monetários utilizam o tipo `Decimal`?
- [ ] A auditoria registrou as alterações devidamente com o IP e Usuário da fixture/middleware?
- [ ] Nenhuma transação de teste deixou lixo residual no banco PostgreSQL local?
