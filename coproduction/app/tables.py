from sqlalchemy import ARRAY, Column, ForeignKey, String, Table, func, Boolean, DateTime

from app.general.db.base_class import Base as BaseModel
from app.utils import ChannelTypes

team_administrators_association_table = Table('team_administrators', BaseModel.metadata,
                                    Column('team_id', ForeignKey('team.id', ondelete="CASCADE"), primary_key=True),
                                    Column('user_id', ForeignKey('user.id', ondelete="CASCADE"), primary_key=True))


coproductionprocess_administrators_association_table = Table('coproductionprocess_administrators', BaseModel.metadata,
                                    Column('coproductionprocess_id', ForeignKey('coproductionprocess.id', ondelete="CASCADE"), primary_key=True),
                                    Column('user_id', ForeignKey('user.id', ondelete="CASCADE"), primary_key=True))

organization_administrators_association_table = Table('organization_administrators', BaseModel.metadata,
                                    Column('organization_id', ForeignKey('organization.id', ondelete="CASCADE"), primary_key=True),
                                    Column('user_id', ForeignKey('user.id', ondelete="CASCADE"), primary_key=True))

user_team_association_table = Table('association_user_team', BaseModel.metadata,
                                    Column('user_id', ForeignKey('user.id', ondelete="CASCADE"), primary_key=True),
                                    Column('team_id', ForeignKey('team.id', ondelete="CASCADE"), primary_key=True))

team_applies_association_table = Table('team_applies', BaseModel.metadata,
                                       Column('team_id', ForeignKey('team.id', ondelete="CASCADE"), primary_key=True),
                                       Column('user_id', ForeignKey('user.id', ondelete="CASCADE"), primary_key=True))

coproductionprocess_tags_association_table = Table('coproductionprocess_tags', BaseModel.metadata,
                                                   Column('coproductionprocess_id', ForeignKey('coproductionprocess.id', ondelete="CASCADE"), primary_key=True),
                                                   Column('tag_id', ForeignKey('tag.id', ondelete="CASCADE"), primary_key=True))

coproductionprocess_keywords_association_table = Table('story_keywords', BaseModel.metadata,
                                                   Column('story_id', ForeignKey('story.id', ondelete="CASCADE"), primary_key=True),
                                                   Column('keyword_id', ForeignKey('keyword.id', ondelete="CASCADE"), primary_key=True))