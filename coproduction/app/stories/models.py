import uuid
from sqlalchemy import (
    Integer,
    Numeric,
)
from sqlalchemy import Date, Column, ForeignKey, String, Table, Integer, func, Boolean, Enum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import backref, relationship, declarative_base

from app.general.db.base_class import Base as BaseModel
from app.config import settings
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_utils import aggregated
from sqlalchemy.orm import Session
from app.utils import ChannelTypes
from app.utils import ClaimTypes
from app.coproductionprocesses.models import CoproductionProcess
from app.ratings.models import Rating
from app.tables import coproductionprocess_keywords_association_table


class Story(BaseModel):
    """Association Class contains for a Notification and CoproductionProcess."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coproductionprocess_id = Column(UUID(as_uuid=True), ForeignKey("coproductionprocess.id", use_alter=True, ondelete='SET NULL'), nullable=False)
    coproductionprocess_cloneforpub_id = Column(UUID(as_uuid=True),nullable=True)
    user_id = Column(String, nullable=True)
    state = Column(Boolean, nullable=False, default=False)
    logotype = Column(String, nullable=True)

    #Json object with information relevant to a story:
    data_story = Column(JSONB, nullable=True)

    # 1 digit for decimals
    rating= Column(Numeric(2, 1), default=0)
    ratings_count = Column(Integer, default=0) 

    # Keywords
    keywords = relationship(
        'Keyword',
        secondary=coproductionprocess_keywords_association_table,
        backref='stories',
    )
    keywords_ids = association_proxy('keywords', 'id')
    
    coproductionprocess = relationship('CoproductionProcess', back_populates="coproductionprocess_story_associations")
    published_date = Column(Date, nullable=True)
    

    def __repr__(self) -> str:
        return f"<Story {self.created_at}>"