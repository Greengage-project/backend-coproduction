from email.policy import default

from app.general.db.base_class import Base as BaseModel
from sqlalchemy import ARRAY, Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

class User(BaseModel):
    id = Column(String, primary_key=True)
    is_superuser = Column(Boolean, default=False)
    
    picture = Column(String)
    full_name = Column(String)
    last_login = Column(DateTime)
    email = Column(String)
    additionalEmails = Column(ARRAY(String), server_default='{}')

    teams_ids = association_proxy('teams', 'id')
    administered_teams_ids = association_proxy('administered_teams', 'id')

    user_notification_associations = relationship(
        "UserNotification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

  

    notifications = association_proxy("user_notification_associations", "notification")


    applied_teams_ids = association_proxy("applied_teams", "id")

    def __repr__(self) -> str:
        return f"<User {self.id}>"