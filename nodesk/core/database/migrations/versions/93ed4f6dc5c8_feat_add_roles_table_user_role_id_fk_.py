"""feat: add roles table, user role_id fk, role endpoint and soft-delete trigger

Revision ID: 93ed4f6dc5c8
Revises: 1f28c8673862
Create Date: 2025-11-16 23:12:11.318044

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "93ed4f6dc5c8"
down_revision: Union[str, Sequence[str], None] = "1f28c8673862"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. Criação da Tabela Roles (Auto-gerado + Captura do objeto) ---
    # Atribuímos a 'roles_table' para usar no bulk_insert logo abaixo
    roles_table = op.create_table(
        "roles",
        sa.Column("role_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("role_id"),
        sa.UniqueConstraint("role_name"),
    )

    # --- 2. Alteração na Tabela Users (Auto-gerado) ---
    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "users", "roles", ["role_id"], ["role_id"])

    # ==================================================================
    # CÓDIGO MANUAL: INSERTS E TRIGGERS
    # ==================================================================

    # 3. Insere os papéis (Roles) iniciais
    op.bulk_insert(
        roles_table,
        [
            {"role_name": "admin"},
            {"role_name": "agent"},
            {"role_name": "viewer"},
        ],
    )

    # 4. Cria a Função do Trigger (Soft Delete)
    op.execute("""
    CREATE OR REPLACE FUNCTION set_user_inactive_on_key_delete()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Atualiza a tabela 'users', setando 'active' para FALSE
        -- quando a chave de criptografia correspondente é deletada
        UPDATE public.users
        SET active = FALSE,
            updated_at = NOW()
        WHERE id = OLD.user_id;

        RETURN OLD;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 5. Cria o Trigger na tabela user_keys
    op.execute("""
    CREATE TRIGGER trg_user_soft_delete
    AFTER DELETE ON public.user_keys
    FOR EACH ROW
    EXECUTE FUNCTION set_user_inactive_on_key_delete();
    """)
    # ==================================================================


def downgrade() -> None:
    # ==================================================================
    # REVERSÃO MANUAL
    # ==================================================================
    # Remove o trigger e a função
    op.execute("DROP TRIGGER IF EXISTS trg_user_soft_delete ON public.user_keys;")
    op.execute("DROP FUNCTION IF EXISTS set_user_inactive_on_key_delete();")
    # ==================================================================

    # --- Reversão das alterações de estrutura (Auto-gerado) ---
    op.drop_constraint(None, "users", type_="foreignkey")
    op.drop_column("users", "role_id")
    op.drop_table("roles")
