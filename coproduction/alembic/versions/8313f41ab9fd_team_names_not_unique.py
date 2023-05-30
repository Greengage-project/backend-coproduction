"""team_names_not_unique

Revision ID: 8313f41ab9fd
Revises: 1528ab0bd4c8
Create Date: 2023-05-26 12:02:31.735098

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8313f41ab9fd'
down_revision = '1528ab0bd4c8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('team_name_key', 'team', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('team_name_key', 'team', ['name'])
    # ### end Alembic commands ###
