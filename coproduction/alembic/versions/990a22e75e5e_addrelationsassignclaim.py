"""addrelationsassignclaim

Revision ID: 990a22e75e5e
Revises: 7370fe66080a
Create Date: 2023-07-12 14:19:19.100918

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '990a22e75e5e'
down_revision = '7370fe66080a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('claim', sa.Column('assignment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'claim', 'assignment', ['assignment_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'claim', type_='foreignkey')
    op.drop_column('claim', 'assignment_id')
    # ### end Alembic commands ###
