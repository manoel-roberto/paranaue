# Sistema de Impacto Financeiro UEFS

Este sistema é uma API para o cálculo de impacto financeiro e evolução de carreira dos servidores da **Universidade Estadual de Feira de Santana (UEFS)**. Ele permite gerenciar o cadastro de servidores, definir parâmetros salariais (tabelas de vencimentos base e referências GSTU), simular cenários de reajuste e promoção funcional, e gerar relatórios consolidados em formato PDF.

---

## 🚀 Tecnologias

A API foi construída com tecnologias modernas de alto desempenho do ecossistema Python:

* **FastAPI**: Framework web rápido e assíncrono para construção de APIs.
* **SQLAlchemy 2.0 (Async)**: ORM robusto configurado para transações e operações assíncronas.
* **Alembic**: Ferramenta para gerenciamento de migrações e controle de versão do banco de dados.
* **PostgreSQL**: Banco de dados relacional de produção.
* **Docker**: Containerização do banco de dados para isolamento e reprodutibilidade.
* **Pytest**: Framework de testes automatizados unitários e de integração.
* **ReportLab**: Biblioteca para a geração dinâmica dos relatórios de simulação em PDF.

---

## 📋 Pré-requisitos

Para rodar este projeto localmente, certifique-se de possuir:

1. **Python 3.12+** instalado.
2. **Docker** instalado e em execução.
3. Gerenciador de pacotes `pip` e ferramenta para criação de ambiente virtual (`venv`).

---

## 🛠️ Instalação e Configuração

Siga os passos abaixo para preparar o ambiente local de desenvolvimento:

### 1. Clonar o Repositório e Acessar a Pasta do Backend
```bash
git clone https://github.com/seu-usuario/paranaue.git
cd paranaue/backend
```

### 2. Configurar o Ambiente Virtual
Crie e ative um ambiente virtual Python para isolar as dependências:
```bash
# Criar o ambiente virtual
python -m venv .venv

# Ativar no Linux / macOS
source .venv/bin/activate

# Ativar no Windows (Prompt de Comando)
.venv\Scripts\activate.bat

# Ativar no Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Instalar as Dependências
Com o ambiente virtual ativado, instale os pacotes necessários:
```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente
Crie um arquivo `.env.local` na raiz da pasta `backend` com as configurações do banco de dados. O projeto já vem pré-configurado para desenvolvimento com o seguinte padrão:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54315/meu_banco
```

---

## ⚙️ Instruções de Execução

### 1. Iniciar o Banco de Dados via Docker
Execute o PostgreSQL em um container Docker apontando para a porta `54315` configurada no `.env.local`:
```bash
docker run --name postgres-uefs -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=meu_banco -p 54315:5432 -d postgres
```

### 2. Aplicar as Migrações do Banco de Dados
Use o Alembic para aplicar o schema do banco de dados a partir das migrações:
```bash
alembic upgrade head
```

### 3. Executar o Servidor de Desenvolvimento
Inicie a aplicação utilizando o Uvicorn com hot-reload ativo:
```bash
uvicorn app.main:app --reload
```
A API estará acessível em: `http://localhost:8000`

---

## 📚 Documentação da API

Graças ao FastAPI, a API conta com documentação interativa e detalhada gerada automaticamente a partir das especificações OpenAPI:

* **Swagger UI (Interativa)**: `http://localhost:8000/docs` (com exemplos prontos de payload via *Try it out*)
* **ReDoc (Alternativa)**: `http://localhost:8000/redoc`

---

## 🧪 Testes Automatizados

Para validar o funcionamento correto de todas as regras de negócio e integrações da API, execute a suíte de testes usando `pytest`:

```bash
pytest
```
*(Nota: Certifique-se de que o container do banco de dados está em execução ao rodar os testes de integração).*
