"""Added initial table

Revision ID: a1fd01cc7558
Revises: 
Create Date: 2022-05-02 10:05:36.200059

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1fd01cc7558'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('coproductionprocess',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('language', sa.Enum('en', 'es', 'it', 'lv', name='locales', native_enum=False), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('logotype', sa.String(), nullable=True),
    sa.Column('aim', sa.Text(), nullable=True),
    sa.Column('idea', sa.Text(), nullable=True),
    sa.Column('organization', sa.Text(), nullable=True),
    sa.Column('challenges', sa.Text(), nullable=True),
    sa.Column('phases_count', sa.Integer(), nullable=True),
    sa.Column('artefact_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('creator_id', sa.String(), nullable=True),
    sa.Column('default_role_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['default_role_id'], ['role.id'], ondelete='SET NULL', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('team',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('logotype', sa.String(), nullable=True),
    sa.Column('creator_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('association_user_team',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'team_id')
    )
    op.create_table('phase',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('coproductionprocess_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('awaiting', 'in_progress', 'finished', name='status', native_enum=False), nullable=True),
    sa.Column('progress', sa.Numeric(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['coproductionprocess_id'], ['coproductionprocess.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('role',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('meta_editable', sa.Boolean(), nullable=True),
    sa.Column('perms_editable', sa.Boolean(), nullable=True),
    sa.Column('deletable', sa.Boolean(), nullable=True),
    sa.Column('selectable', sa.Boolean(), nullable=True),
    sa.Column('permissions', postgresql.ARRAY(sa.Enum('view_assets', 'create_assets', 'delete_assets', 'change_access', 'update_settings', name='permissions', native_enum=False)), nullable=True),
    sa.Column('coproductionprocess_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['coproductionprocess_id'], ['coproductionprocess.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('association_team_role',
    sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('team_id', 'role_id')
    )
    op.create_table('association_user_role',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    op.create_table('objective',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True),
    sa.Column('description_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('awaiting', 'in_progress', 'finished', name='status', native_enum=False), nullable=True),
    sa.Column('progress', sa.Numeric(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['phase_id'], ['phase.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('phase_prerequisites',
    sa.Column('phase_a_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('phase_b_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['phase_a_id'], ['phase.id'], ),
    sa.ForeignKeyConstraint(['phase_b_id'], ['phase.id'], ),
    sa.PrimaryKeyConstraint('phase_a_id', 'phase_b_id')
    )
    op.create_table('objective_prerequisites',
    sa.Column('objective_a_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('objective_b_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['objective_a_id'], ['objective.id'], ),
    sa.ForeignKeyConstraint(['objective_b_id'], ['objective.id'], ),
    sa.PrimaryKeyConstraint('objective_a_id', 'objective_b_id')
    )
    op.create_table('task',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('objective_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('problemprofiles', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('status', sa.Enum('awaiting', 'in_progress', 'finished', name='status', native_enum=False), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['objective_id'], ['objective.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('asset',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('coproductionprocess_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('creator_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['coproductionprocess_id'], ['coproductionprocess.id'], ),
    sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['task.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task_prerequisites',
    sa.Column('task_a_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('task_b_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['task_a_id'], ['task.id'], ),
    sa.ForeignKeyConstraint(['task_b_id'], ['task.id'], ),
    sa.PrimaryKeyConstraint('task_a_id', 'task_b_id')
    )
    op.create_table('exception',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('coproductionprocess_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('permission', sa.Enum('view_assets', 'create_assets', 'delete_assets', 'change_access', 'update_settings', name='permissions', native_enum=False), nullable=True),
    sa.Column('grant', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['asset.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['coproductionprocess_id'], ['coproductionprocess.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('externalasset',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('icon_path', sa.String(), nullable=True),
    sa.Column('externalinterlinker_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('uri', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['asset.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('internalasset',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('external_asset_id', sa.String(), nullable=True),
    sa.Column('softwareinterlinker_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('knowledgeinterlinker_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['asset.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('internalasset')
    op.drop_table('externalasset')
    op.drop_table('exception')
    op.drop_table('task_prerequisites')
    op.drop_table('asset')
    op.drop_table('task')
    op.drop_table('objective_prerequisites')
    op.drop_table('phase_prerequisites')
    op.drop_table('objective')
    op.drop_table('association_user_role')
    op.drop_table('association_team_role')
    op.drop_table('role')
    op.drop_table('phase')
    op.drop_table('association_user_team')
    op.drop_table('team')
    op.drop_table('coproductionprocess')
    op.drop_table('user')
    # ### end Alembic commands ###
