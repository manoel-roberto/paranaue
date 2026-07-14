import os
import sys
import asyncio
import socket
from sqlalchemy.ext.asyncio import create_async_engine

# Adiciona o diretório do backend ao sys.path para carregar 'app' corretamente
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models.base import Base
# Importa o módulo de modelos para registrar as entidades no metadado
import app.models

def get_database_url():
    # Carrega a DATABASE_URL do arquivo .env.local na mesma pasta
    env_path = os.path.join(os.path.dirname(__file__), ".env.local")
    url = None
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        if key.strip() == "DATABASE_URL":
                            url = val.strip()
                            break
    if not url:
        url = os.environ.get("DATABASE_URL")
        
    # Tratamento dinâmico para ambiente de sandbox
    # Se a URL aponta para localhost mas a porta não está aberta localmente,
    # tentamos redirecionar para o host real (gateway Docker 172.18.0.1)
    if url and ("localhost" in url or "127.0.0.1" in url):
        try:
            # Extrai a porta
            parts = url.split("@")[-1].split("/")[0].split(":")
            port = int(parts[1]) if len(parts) > 1 else 5432
            
            # Testa localhost
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            s.close()
        except Exception:
            # Localhost falhou. Testa o gateway da ponte do Docker (172.18.0.1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(("172.18.0.1", port))
                s.close()
                url = url.replace("localhost", "172.18.0.1").replace("127.0.0.1", "172.18.0.1")
                print(f"INFO: Redirecionando conexao de localhost para 172.18.0.1 (Ambiente Sandbox)")
            except Exception:
                pass
                
    return url

async def main():
    database_url = get_database_url()
    if not database_url:
        print("Erro: DATABASE_URL não definida no .env.local ou no ambiente.")
        sys.exit(1)
        
    print(f"DATABASE_URL identificada: {database_url}")
    print("Conectando ao banco de dados e preparando para recriar as tabelas...")
    
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        print("Removendo tabelas existentes (drop_all)...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Tabelas removidas.")
        
        print("Criando esquema físico de tabelas (create_all)...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tabelas criadas com sucesso no banco de dados!")
        
    await engine.dispose()
    print("Operação concluída.")

if __name__ == "__main__":
    asyncio.run(main())
