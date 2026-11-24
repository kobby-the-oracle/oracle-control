"""Add agent, authority, custody, legal hold and event lineage schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from oracle_control.entities import AgentRecord, AuthorityRecord, ApprovalRecord, CustodyRecord, LegalHoldRecord

revision = "0002_enterprise_foundation"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    for model in (AgentRecord, AuthorityRecord, ApprovalRecord, CustodyRecord, LegalHoldRecord):
        if model.__tablename__ not in tables:
            model.__table__.create(bind=bind)

    columns = {column["name"] for column in inspect(bind).get_columns("events")}
    for name, column in (
        ("session_id", sa.Column("session_id", sa.String(256), nullable=True)),
        ("parent_agent_id", sa.Column("parent_agent_id", sa.String(256), nullable=True)),
        ("parent_run_id", sa.Column("parent_run_id", sa.String(256), nullable=True)),
        ("credential_ref", sa.Column("credential_ref", sa.String(256), nullable=True)),
    ):
        if name not in columns:
            op.add_column("events", column)

    case_columns = {column["name"] for column in inspect(bind).get_columns("cases")}
    if "agent_ids" not in case_columns:
        op.add_column("cases", sa.Column("agent_ids", sa.JSON(), nullable=False, server_default="[]"))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    for table in ("legal_holds", "custody_records", "approvals", "authority_records", "agents"):
        if table in tables:
            op.drop_table(table)
    event_columns = {column["name"] for column in inspect(bind).get_columns("events")}
    for name in ("credential_ref", "parent_run_id", "parent_agent_id", "session_id"):
        if name in event_columns:
            op.drop_column("events", name)
    case_columns = {column["name"] for column in inspect(bind).get_columns("cases")}
    if "agent_ids" in case_columns:
        op.drop_column("cases", "agent_ids")
