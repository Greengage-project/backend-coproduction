"""Added initial table

Revision ID: 45a99ad69c75
Revises: 
Create Date: 2022-01-17 17:45:24.093180

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '45a99ad69c75'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('coproductionschema',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('phase',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('team',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('logotype', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('coproductionprocess',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True),
    sa.Column('description_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True),
    sa.Column('logotype', sa.Text(), nullable=True),
    sa.Column('aim', sa.Text(), nullable=True),
    sa.Column('idea', sa.Text(), nullable=True),
    sa.Column('organization', sa.Text(), nullable=True),
    sa.Column('challenges', sa.Text(), nullable=True),
    sa.Column('artefact_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('acl_id', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('coproductionschema_phase',
    sa.Column('coproductionschema_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['coproductionschema_id'], ['coproductionschema.id'], ),
    sa.ForeignKeyConstraint(['phase_id'], ['phase.id'], )
    )
    op.create_table('membership',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('objective',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['phase_id'], ['phase.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('phaseinstantiation',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('coproductionprocess_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['coproductionprocess_id'], ['coproductionprocess.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['phase_id'], ['phase.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('role',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('type', sa.Text(), nullable=True),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('coproductionprocess_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('user_id', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['coproductionprocess_id'], ['coproductionprocess.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('objective_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('recommended_interlinkers', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['objective_id'], ['objective.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('objectiveinstantiation',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('phaseinstantiation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('objective_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('progress', sa.Integer(), nullable=True),
    sa.Column('start_date', sa.String(), nullable=True),
    sa.Column('end_date', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['objective_id'], ['objective.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['phaseinstantiation_id'], ['phaseinstantiation.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('taskinstantiation',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('objectiveinstantiation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['objectiveinstantiation_id'], ['objectiveinstantiation.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('asset',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('external_id', sa.String(), nullable=True),
    sa.Column('interlinker_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('taskinstantiation_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['taskinstantiation_id'], ['taskinstantiation.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('asset')
    op.drop_table('taskinstantiation')
    op.drop_table('objectiveinstantiation')
    op.drop_table('task')
    op.drop_table('role')
    op.drop_table('phaseinstantiation')
    op.drop_table('objective')
    op.drop_table('membership')
    op.drop_table('coproductionschema_phase')
    op.drop_table('coproductionprocess')
    op.drop_table('team')
    op.drop_table('phase')
    op.drop_table('coproductionschema')
    # ### end Alembic commands ###
# 
