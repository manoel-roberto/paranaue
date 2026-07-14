# Especificação de Arquitetura DevOps

**Sistema de Cálculo de Impacto Financeiro da UEFS**  
**Autor:** Engenheiro DevOps Sênior & Arquiteto de Infraestrutura  
**Data:** 10 de Julho de 2026  
**Versão:** 1.0 - Oficial  
**Premissa Principal:** Simplicidade Extrema (No-K8s, No-Swarm, No-Complex-CI/CD)

---

## 1. Visão Geral da Arquitetura de Implantação

Para garantir um ciclo de desenvolvimento ágil e um deploy de baixo custo e alta manutenibilidade, a infraestrutura do **Sistema de Cálculo de Impacto Financeiro da UEFS** é projetada sobre o paradigma de **isolamento por contêineres Docker** no nível de aplicação, mantendo o banco de dados como um recurso externo e gerenciado no ambiente de produção.

A arquitetura lógica de implantação consiste em:
- **Camada de Apresentação (Frontend):** Aplicação SPA em React, construída (build de produção) e servida pelo Nginx.
- **Camada de Negócio (Backend):** API REST assíncrona em FastAPI (Python), executada via servidor ASGI Uvicorn.
- **Camada de Persistência (Banco de Dados):** PostgreSQL 15.

```mermaid
flowchart TD
    subgraph Local_Dev [Ambiente de Desenvolvimento Local (Docker Compose)]
        dev_user[Desenvolvedor] -->|localhost:5173| dev_front[Frontend: React/Vite - Contêiner]
        dev_front -->|localhost:8000| dev_back[Backend: FastAPI - Contêiner]
        dev_back -->|db:5432| dev_db[(PostgreSQL 15 - Contêiner)]
    end

    subgraph Prod_VPS [Ambiente de Produção (VPS Linux + Docker Compose)]
        prod_user[Usuário Final] -->|Porta 80/443| prod_front[Frontend: React + Nginx - Contêiner]
        prod_front -->|Proxy Reverso / API| prod_back[Backend: FastAPI - Contêiner]
    end

    prod_db[(PostgreSQL 15 Gerenciado / Dedicado Físico)]
    prod_back -->|Conexão TCP Externa| prod_db

    style Local_Dev fill:#e6f3ff,stroke:#333,stroke-width:1px
    style Prod_VPS fill:#ffe6e6,stroke:#333,stroke-width:1px
    style prod_db fill:#e6ffe6,stroke:#333,stroke-width:2px
```

---

## 2. Estratégia de Ambientes e Variáveis (.env)

Em conformidade com o **Princípio III da metodologia Twelve-Factor App (Configuração)**, toda e qualquer configuração que varie entre os ambientes (Dev e Prod) deve ser armazenada em variáveis de ambiente, isolando completamente o código-fonte da infraestrutura subjacente.

### 2.1 Variáveis de Ambiente Críticas

| Variável | Tipo | Descrição | Exemplo Local | Exemplo Produção |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String | URL de conexão com o banco de dados (asyncpg). | `postgresql+asyncpg://uefs_user:uefs_password@db:5432/uefs_financeiro` | `postgresql+asyncpg://prod_user:SuperSenha123@10.0.0.5:5432/uefs_prod` |
| `POSTGRES_USER` | String | Usuário administrativo do PostgreSQL. | `uefs_user` | `prod_user` (Usado para scripts/migrações) |
| `POSTGRES_PASSWORD`| String | Senha do PostgreSQL. | `uefs_password` | `SuperSenha123` |
| `POSTGRES_DB` | String | Nome do banco de dados. | `uefs_financeiro` | `uefs_prod` |
| `ENVIRONMENT` | String | Definição do ambiente atual. | `local` | `production` |
| `CORS_ORIGINS` | String | Origens permitidas pelo CORS. | `http://localhost:5173,http://127.0.0.1:5173` | `https://impactofinanceiro.uefs.br` |
| `PORT` | Integer| Porta exposta pela API do backend. | `8000` | `8000` |

### 2.2 Exemplo de Arquivo Local: `.env.local`

Arquivo localizado na raiz do projeto durante o desenvolvimento. Note que a string de conexão do banco de dados aponta para o host **`db`**, que é o nome do serviço orquestrado pelo Docker Compose local.

```bash
# ==============================================================================
# CONFIGURAÇÃO DE AMBIENTE LOCAL (DESENVOLVIMENTO)
# ==============================================================================

ENVIRONMENT=local
PORT=8000

# Credenciais do Banco de Dados Local (Criadas pelo contêiner 'db')
POSTGRES_USER=uefs_user
POSTGRES_PASSWORD=uefs_password
POSTGRES_DB=uefs_financeiro

# Conexão interna para o contêiner Backend -> Contêiner DB
DATABASE_URL=postgresql+asyncpg://uefs_user:uefs_password@db:5432/uefs_financeiro

# Conexão alternativa se for rodar o backend diretamente na máquina física (fora do Docker):
# DATABASE_URL=postgresql+asyncpg://uefs_user:uefs_password@localhost:5432/uefs_financeiro

# CORS & Segurança
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# URL da API para o Frontend (React/Vite) em desenvolvimento
VITE_API_URL=http://localhost:8000/api/v1
```

### 2.3 Exemplo de Arquivo de Produção: `.env.prod`

Este arquivo é mantido diretamente na VPS de produção (e **NUNCA** deve ser commitado no repositório Git). A string de conexão aponta para um endereço externo (seja um IP privado de rede de banco dedicado da UEFS, um host DNS, ou serviço de banco de dados gerenciado).

```bash
# ==============================================================================
# CONFIGURAÇÃO DE AMBIENTE DE PRODUÇÃO (VPS LINUX)
# ==============================================================================

ENVIRONMENT=production
PORT=8000

# Credenciais do PostgreSQL de Produção (Hospedado fora do Docker)
POSTGRES_USER=prod_user_uefs
POSTGRES_PASSWORD=SenhaAltamenteForteERobustaDeProducao2026#
POSTGRES_DB=uefs_financeiro_prod

# String de Conexão apontando para o IP do Servidor do Banco de Dados dedicado/externo
DATABASE_URL=postgresql+asyncpg://prod_user_uefs:SenhaAltamenteForteERobustaDeProducao2026%23@192.168.10.150:5432/uefs_financeiro_prod

# CORS & Segurança (URLs oficiais do domínio de produção)
CORS_ORIGINS=https://impactofinanceiro.uefs.br,https://api-impactofinanceiro.uefs.br
```
> [!WARNING]  
> Atente-se ao encoding de caracteres especiais na string `DATABASE_URL` (por exemplo, substituir o caractere `#` por `%23` caso exista na senha) para evitar erros de parser da biblioteca de conexão SQL.

---

## 3. Ambiente de Desenvolvimento Local (`docker-compose.yml`)

O arquivo a seguir é focado na experiência de desenvolvimento local (DX - Developer Experience). Ele garante o isolamento completo de dependências na máquina de trabalho, permitindo que com apenas um comando (`docker compose up`) todo o ecossistema suba e esteja integrado, com hot-reload ativo no Frontend e no Backend.

```yaml
version: "3.8"

services:
  # ----------------------------------------------------------------------------
  # Serviço de Banco de Dados Local (Apenas no ambiente de desenvolvimento)
  # ----------------------------------------------------------------------------
  db:
    image: postgres:15-alpine
    container_name: uefs_db_local
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-uefs_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-uefs_password}
      POSTGRES_DB: ${POSTGRES_DB:-uefs_financeiro}
    ports:
      - "5432:5432" # Mapeado para a porta da máquina física permitindo conectar via DBeaver/pgAdmin
    volumes:
      - uefs_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-uefs_user} -d ${POSTGRES_DB:-uefs_financeiro}"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ----------------------------------------------------------------------------
  # Serviço do Backend (FastAPI)
  # ----------------------------------------------------------------------------
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: uefs_backend_local
    restart: unless-stopped
    ports:
      - "${PORT:-8000}:8000"
    env_file:
      - .env.local
    volumes:
      - ./backend:/app # Mount do código-fonte para viabilizar hot-reload
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      db:
        condition: service_healthy # Garante que o DB local já aceita conexões antes do backend iniciar

  # ----------------------------------------------------------------------------
  # Serviço do Frontend (React / Vite)
  # ----------------------------------------------------------------------------
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: uefs_frontend_local
    restart: unless-stopped
    ports:
      - "5173:5173"
    env_file:
      - .env.local
    volumes:
      - ./frontend:/app # Mount do código-fonte para hot-reload
      - /app/node_modules # Impede que a pasta node_modules local da máquina física sobrescreva a do contêiner
    command: npm run dev -- --host 0.0.0.0

volumes:
  uefs_postgres_data:
    name: uefs_postgres_data # Volume nomeado para persistência de dados local
```

### Detalhes de Implementação Local:
1. **Healthcheck no DB:** Garante sincronia na inicialização. O contêiner do `backend` aguardará o PostgreSQL estar apto a responder conexões antes de tentar subir o Uvicorn, reduzindo falhas de inicialização do ORM.
2. **Volumes (Bind Mounts):** As linhas `./backend:/app` e `./frontend:/app` sincronizam os arquivos locais com os internos do contêiner, refletindo qualquer modificação no código instantaneamente na tela do desenvolvedor.
3. **Isolamento de Node Modules:** A montagem `/app/node_modules` impede conflitos de arquitetura de sistema operacional (por exemplo, se o desenvolvedor rodar `npm install` localmente no Windows/macOS, o contêiner Linux do Docker usará a sua própria pasta compilada).

---

## 4. Ambiente de Produção (`docker-compose.prod.yml`)

No ambiente de produção hospedado na VPS, o banco de dados reside fora da infraestrutura de contêineres Docker (servidor dedicado ou banco de dados relacional como serviço). Desta forma, eliminamos o serviço de banco de dados do Docker Compose e focamos exclusivamente na escalabilidade e isolamento dos serviços de aplicação.

```yaml
version: "3.8"

networks:
  uefs_prod_network:
    driver: bridge
    name: uefs_prod_network

services:
  # ----------------------------------------------------------------------------
  # Serviço de Backend (FastAPI em modo de produção)
  # ----------------------------------------------------------------------------
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: uefs_backend_prod
    restart: always
    env_file:
      - .env.prod
    ports:
      - "8000:8000" # Exposta na VPS para ser consumida pela rede interna ou proxy externo
    networks:
      - uefs_prod_network
    # Comando de execução sem o flag '--reload' para otimização de performance em produção
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  # ----------------------------------------------------------------------------
  # Serviço de Frontend (React empacotado sob Nginx de Produção)
  # ----------------------------------------------------------------------------
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: uefs_frontend_prod
    restart: always
    ports:
      - "80:80"   # HTTP padrão
      - "443:443" # HTTPS (Requer configuração de SSL com Let's Encrypt/Certbot na VPS)
    networks:
      - uefs_prod_network
    depends_on:
      - backend

# O volume uefs_postgres_data não existe neste arquivo, pois o banco de dados é externo.
```

### Arquivos auxiliares recomendados de Produção:

#### Dockerfile do Frontend para Produção (`frontend/Dockerfile.prod`):
Utiliza um build multi-stage para gerar os arquivos estáticos e servi-los de forma leve com Nginx.
```dockerfile
# Estágio de Compilação
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Estágio de Execução
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Arquivo de Configuração do Nginx (`frontend/nginx.conf`):
Configuração básica para roteamento SPA em React e repasse da API.
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Proxy reverso para o backend FastAPI (sem barra final no proxy_pass para preservar /api prefix)
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 5. Fluxo de Deploy Manual (Playbook de Produção)

Este guia provê os comandos necessários para que um administrador de sistemas ou engenheiro de software execute a implantação, atualização e rollback do sistema na VPS Linux diretamente via terminal.

### 5.1 Pré-requisitos na VPS
Antes de iniciar, certifique-se de que a VPS possui o Docker e o plugin Docker Compose instalados:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable docker --now
sudo usermod -aG docker $USER
# Reinicie a sessão SSH após adicionar o usuário ao grupo docker
```

---

### 5.2 Roteiro de Primeiro Deploy (Instalação Inicial)

Execute o passo a passo a seguir para a primeira inicialização do sistema na máquina de produção.

#### Passo 1: Acessar a VPS via SSH
```bash
ssh uefs_admin@vps-ip-uefs.br
```

#### Passo 2: Clonar o Repositório do Projeto
Recomendável armazenar o código no diretório `/var/www/` ou `/opt/`.
```bash
sudo mkdir -p /var/www/uefs-impacto-financeiro
sudo chown -R $USER:$USER /var/www/uefs-impacto-financeiro
cd /var/www/uefs-impacto-financeiro
git clone https://github.com/uefs/impacto-financeiro.git .
```

#### Passo 3: Criar o arquivo de variáveis de ambiente de Produção
Crie o arquivo `.env.prod` na pasta raiz e popule com as credenciais do banco externo da UEFS.
```bash
nano .env.prod
# Cole o conteúdo conforme detalhado na Seção 2.3 deste documento e salve (Ctrl+O, Ctrl+X)
chmod 600 .env.prod # Protege o arquivo para leitura exclusiva do proprietário
```

#### Passo 4: Executar o build das imagens Docker e inicializar a stack
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

#### Passo 5: Aplicar as Migrações do Banco de Dados
A execução de migrações é realizada chamando o comando do framework de migração (ex: Alembic/SQLAlchemy) diretamente dentro do contêiner de backend que já está conectado ao banco de dados externo.
```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

### 5.3 Roteiro de Atualização Automática (Deploy de Novas Versões)

Quando novas features forem mescladas na branch principal (`main` ou `master`), execute os seguintes comandos para atualizar o sistema em produção com zero ou mínimo downtime.

Crie um script em `/var/www/uefs-impacto-financeiro/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "=== 1. Puxando nova versão do Git ==="
git pull origin main

echo "=== 2. Reconstruindo imagens Docker e reiniciando serviços ==="
docker compose -f docker-compose.prod.yml up --build -d

echo "=== 3. Executando migrações pendentes no Banco de Dados ==="
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

echo "=== 4. Removendo imagens antigas ou órfãs para liberar espaço ==="
docker image prune -f

echo "=== DEPLOY EXECUTADO COM SUCESSO ==="
```

Torne o script executável:
```bash
chmod +x deploy.sh
```

Toda vez que precisar atualizar a aplicação, basta rodar:
```bash
./deploy.sh
```

---

### 5.4 Procedimento de Verificação de Integridade (Sanity Check)

Para garantir que o deploy foi bem sucedido, execute os comandos de validação:

```bash
# 1. Verificar se os contêineres estão em status "Up"
docker compose -f docker-compose.prod.yml ps

# 2. Monitorar os logs em tempo real procurando por erros de runtime
docker compose -f docker-compose.prod.yml logs -f --tail=100

# 3. Testar a resposta da API via cURL
curl -I http://localhost:8000/health
```

---

### 5.5 Plano de Rollback Emergencial

Se o deploy da nova versão quebrar o sistema ou gerar comportamento indesejado em produção, execute a reversão imediata:

```bash
# 1. Forçar a reversão do código para a tag estável anterior no Git
git fetch --tags
# Substitua 'v1.0.0' pela tag da última versão estável conhecida
git checkout v1.0.0

# 2. Reconstruir e subir imediatamente os contêineres baseados no commit estável
docker compose -f docker-compose.prod.yml up --build -d

# 3. Validar se o sistema voltou a operar
docker compose -f docker-compose.prod.yml ps
```

> [!CAUTION]  
> Caso o deploy quebrado tenha incluído migrações estruturais de banco de dados (que alteraram tabelas), pode ser necessário executar um downgrade de migração antes da reversão do código.
> Exemplo: `docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1`
