"""Create initial ORACLE CONTROL schema."""
from alembic import op
from oracle_control.db import Base
import oracle_control.entities

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind())

def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
