"""addAssignmentsTable

Revision ID: 7370fe66080a
Revises: 794605c8228b
Create Date: 2023-07-11 10:10:44.450031

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7370fe66080a'
down_revision = '794605c8228b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('assignment',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('coproductionprocess_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('state', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['asset.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('assignment')
    # ### end Alembic commands ###