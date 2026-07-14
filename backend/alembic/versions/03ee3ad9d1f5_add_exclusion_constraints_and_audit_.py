"""add_exclusion_constraints_and_audit_triggers

Revision ID: 03ee3ad9d1f5
Revises: b87c2fb0e734
Create Date: 2026-07-14 15:17:47.630842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03ee3ad9d1f5'
down_revision: Union[str, Sequence[str], None] = 'b87c2fb0e734'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Habilitar extensões necessárias
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')

    # Ajustar a coluna id de audit_log para gerar UUID automaticamente no banco
    op.execute("ALTER TABLE audit_log ALTER COLUMN id SET DEFAULT gen_random_uuid()")

    # 2. Adicionar chaves de exclusão temporal (EXCLUDE USING GIST)
    op.execute("""
        ALTER TABLE tabela_vencimento
        ADD CONSTRAINT exclude_tabela_vencimento_overlap
        EXCLUDE USING gist (
            codigo_vencimento WITH =,
            daterange(data_inicio_vigencia, data_fim_vigencia, '[]') WITH &&
        )
    """)

    op.execute("""
        ALTER TABLE tabela_gstu
        ADD CONSTRAINT exclude_tabela_gstu_overlap
        EXCLUDE USING gist (
            codigo_gstu WITH =,
            daterange(data_inicio_vigencia, data_fim_vigencia, '[]') WITH &&
        )
    """)

    op.execute("""
        ALTER TABLE tabela_comissao
        ADD CONSTRAINT exclude_tabela_comissao_overlap
        EXCLUDE USING gist (
            simbolo WITH =,
            daterange(data_inicio_vigencia, data_fim_vigencia, '[]') WITH &&
        )
    """)

    op.execute("""
        ALTER TABLE historico_funcional
        ADD CONSTRAINT exclude_historico_funcional_overlap
        EXCLUDE USING gist (
            vinculo_id WITH =,
            daterange(data_inicio, data_fim, '[]') WITH &&
        )
    """)

    # 3. Criar função de auditoria em PL/pgSQL
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_auditar_alteracao_parametro()
        RETURNS TRIGGER AS $$
        DECLARE
            v_usuario_id UUID;
            v_ip_origem VARCHAR(45);
            v_registro_id UUID;
            v_payload_antigo JSONB := NULL;
            v_payload_novo JSONB := NULL;
        BEGIN
            -- Captura do usuário da sessão definida pelo middleware com tratamento seguro
            BEGIN
                v_usuario_id := NULLIF(current_setting('app.current_user_id', true), '')::UUID;
            EXCEPTION WHEN OTHERS THEN
                v_usuario_id := NULL;
            END;

            -- Captura do IP de origem da requisição
            BEGIN
                v_ip_origem := COALESCE(NULLIF(current_setting('app.current_ip', true), ''), '0.0.0.0');
            EXCEPTION WHEN OTHERS THEN
                v_ip_origem := '0.0.0.0';
            END;

            -- Identificação da operação e estruturação dos payloads
            IF (TG_OP = 'INSERT') THEN
                v_registro_id := NEW.id;
                v_payload_novo := to_jsonb(NEW);
            ELSIF (TG_OP = 'UPDATE') THEN
                v_registro_id := NEW.id;
                v_payload_antigo := to_jsonb(OLD);
                v_payload_novo := to_jsonb(NEW);
            ELSIF (TG_OP = 'DELETE') THEN
                v_registro_id := OLD.id;
                v_payload_antigo := to_jsonb(OLD);
            END IF;

            -- Gravação atômica no log de auditoria
            INSERT INTO audit_log (
                usuario_id,
                tabela_afetada,
                registro_id,
                operacao,
                payload_antigo,
                payload_novo,
                ip_origem,
                data_hora
            ) VALUES (
                v_usuario_id,
                TG_TABLE_NAME,
                v_registro_id,
                TG_OP::operacaolog,
                v_payload_antigo,
                v_payload_novo,
                v_ip_origem,
                CURRENT_TIMESTAMP
            );

            IF (TG_OP = 'DELETE') THEN
                RETURN OLD;
            ELSE
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # 4. Atribuir os triggers às tabelas críticas
    op.execute("""
        CREATE TRIGGER trg_audit_tabela_vencimento
        AFTER INSERT OR UPDATE OR DELETE ON tabela_vencimento
        FOR EACH ROW EXECUTE FUNCTION fn_auditar_alteracao_parametro();
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_tabela_gstu
        AFTER INSERT OR UPDATE OR DELETE ON tabela_gstu
        FOR EACH ROW EXECUTE FUNCTION fn_auditar_alteracao_parametro();
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_tabela_comissao
        AFTER INSERT OR UPDATE OR DELETE ON tabela_comissao
        FOR EACH ROW EXECUTE FUNCTION fn_auditar_alteracao_parametro();
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_usuario
        AFTER INSERT OR UPDATE OR DELETE ON usuario
        FOR EACH ROW EXECUTE FUNCTION fn_auditar_alteracao_parametro();
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_perfil
        AFTER INSERT OR UPDATE OR DELETE ON perfil
        FOR EACH ROW EXECUTE FUNCTION fn_auditar_alteracao_parametro();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Remover triggers
    op.execute("DROP TRIGGER IF EXISTS trg_audit_perfil ON perfil")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_usuario ON usuario")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_tabela_comissao ON tabela_comissao")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_tabela_gstu ON tabela_gstu")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_tabela_vencimento ON tabela_vencimento")

    # 2. Remover função de auditoria
    op.execute("DROP FUNCTION IF EXISTS fn_auditar_alteracao_parametro()")

    # 3. Remover chaves de exclusão
    op.execute("ALTER TABLE historico_funcional DROP CONSTRAINT IF EXISTS exclude_historico_funcional_overlap")
    op.execute("ALTER TABLE tabela_comissao DROP CONSTRAINT IF EXISTS exclude_tabela_comissao_overlap")
    op.execute("ALTER TABLE tabela_gstu DROP CONSTRAINT IF EXISTS exclude_tabela_gstu_overlap")
    op.execute("ALTER TABLE tabela_vencimento DROP CONSTRAINT IF EXISTS exclude_tabela_vencimento_overlap")

    # Remover valor padrão da coluna id em audit_log
    op.execute("ALTER TABLE audit_log ALTER COLUMN id DROP DEFAULT")

    # 4. Desabilitar extensão (opcional, pode manter se for usada por outros índices)
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
