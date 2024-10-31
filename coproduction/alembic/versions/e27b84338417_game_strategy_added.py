"""game strategy added

Revision ID: e27b84338417
Revises: 66bb2581f96a
Create Date: 2024-09-24 16:56:10.750646

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e27b84338417'
down_revision = '66bb2581f96a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('coproductionprocess', sa.Column('game_strategy', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('coproductionprocess', 'game_strategy')
    # ### end Alembic commands ###