from app.messages import log
from typing import Any, Dict, Optional, List

from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app.models import Team, User, Organization, UserNotification
from app.schemas import TeamCreate, TeamPatch
import uuid
from app import models
from app.users.crud import exportCrud as users_crud
from app.organizations.crud import exportCrud as organizations_crud
from app.usernotifications.crud import exportCrud as usernotification_crud
from app.notifications.crud import exportCrud as notification_crud
from sqlalchemy import or_, and_
from fastapi.encoders import jsonable_encoder
from app.sockets import socket_manager
from uuid_by_string import generate_uuid
from app.general.emails import send_email, send_team_email
from app.locales import get_language
from fastapi import HTTPException
import html


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamPatch]):
    async def get_multi(
        self, db: Session, user: User, organization: Organization = None
    ) -> Optional[List[Team]]:
        if organization:
            return db.query(Team).filter(Team.organization_id == organization.id).all()
        return (
            db.query(Team)
            .filter(
                or_(
                    Team.id.in_(user.teams_ids),
                    Team.id.in_(user.administered_teams_ids),
                )
            )
            .all()
        )
    
    

    async def add_user(self, db: Session, team: Team, user: models.User) -> Team:
        from app.worker import sync_asset_treeitems

        sync_asset_treeitems.delay(
            [permission.treeitem_id for permission in team.permissions]
        )
        team.users.append(user)
        db.commit()
        db.refresh(team)
        await log(
            self.enrich_log_data(team, {"action": "ADD_USER", "added_user_id": user.id})
        )

        # Send mail to user to know is added to a team
        _ = send_email(
            user.email,
            "add_member_team",
            environment={
                "team_id": team.id,
                "team_name": team.name,
                "org_id": team.organization_id,
            },
        )

        # Agrego la notificacion cuando un usuario es removido de un equipo:
        newUserNotification = UserNotification()
        newUserNotification.user_id = user.id
        notification = await notification_crud.get_notification_by_event(
            db=db, event="add_user_team", language=get_language()
        )
        if notification:
            newUserNotification.notification_id = notification.id
            newUserNotification.channel = "in_app"
            newUserNotification.state = False
            newUserNotification.parameters = (
                "{'teamName':'"
                + html.escape(team.name)
                + "','team_id':'"
                + str(team.id)
                + "','org_id':'"
                + str(team.organization_id)
                + "'}"
            )

            db.add(newUserNotification)
            db.commit()
            db.refresh(newUserNotification)

        # Send a msn to the user to know is added to a team
        await socket_manager.send_to_id(
            generate_uuid(user.id), {"event": "team" + "_created"}
        )

        return team

    async def remove_user(self, db: Session, team: Team, user: models.User) -> Team:
        from app.worker import sync_asset_treeitems

        team.users.remove(user)
        db.commit()
        db.refresh(team)
        sync_asset_treeitems.delay(
            [permission.treeitem_id for permission in team.permissions]
        )
        await log(
            self.enrich_log_data(
                team, {"action": "REMOVE_USER", "removed_user_id": user.id}
            )
        )

        # Agrego la notificacion cuando un usuario es removido de un equipo:
        newUserNotification = UserNotification()
        newUserNotification.user_id = user.id
        notification = await notification_crud.get_notification_by_event(
            db=db, event="remove_user_team", language=get_language()
        )
        if notification:
            newUserNotification.notification_id = notification.id
            newUserNotification.channel = "in_app"
            newUserNotification.state = False
            newUserNotification.parameters = (
                "{'teamName':'"
                + html.escape(team.name)
                + "','team_id':'"
                + str(team.id)
                + "','org_id':'"
                + str(team.organization_id)
                + "'}"
            )

            db.add(newUserNotification)
            db.commit()
            db.refresh(newUserNotification)

        # Send a msn to the user to know is removed to a team
        await socket_manager.send_to_id(
            generate_uuid(user.id), {"event": "team" + "_created"}
        )

        return team

    async def create(
        self, db: Session, obj_in: TeamCreate, creator: models.User
    ) -> Team:
        obj_in_data = jsonable_encoder(obj_in)
        user_ids = obj_in_data['user_ids']
        del obj_in_data["user_ids"]

        db_obj = Team(**obj_in_data)
        db_obj.creator_id = creator.id
        db_obj.administrators.append(creator)
        for user in await users_crud.get_multi_by_ids(db=db, ids=user_ids):
            db_obj.users.append(user)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Send mail to user to know is added to a team
        _ = send_team_email(
            team=db_obj,
            type='add_member_team',
            environment={
                "team_id": db_obj.id,
                "team_name": db_obj.name,
                "org_id": db_obj.organization_id,
            },
        )

        # Send msn to all user part of a team create
        #print("El team model is:"+get_language())
        #print(user_ids)
        for user_id in user_ids:

            # Create a notification for every user
            newUserNotification = UserNotification()
            newUserNotification.user_id = user_id

            notification = await notification_crud.get_notification_by_event(
                db=db, event="add_user_team", language=get_language()
            )
            #print("La notification es:::::")
            #print(notification)
            if notification:
                #print("Entra a crear notificacion"+str(notification.id))

                newUserNotification.notification_id = notification.id
                newUserNotification.channel = "in_app"
                newUserNotification.state = False
                newUserNotification.parameters = (
                    "{'teamName':'"
                    + html.escape(db_obj.name)
                    + "','team_id':'"
                    + str(db_obj.id)
                    + "','org_id':'"
                    + str(db_obj.organization_id)
                    + "'}"
                )

                db.add(newUserNotification)
                db.commit()
                db.refresh(newUserNotification)

            await socket_manager.send_to_id(
                generate_uuid(user_id), {"event": "team" + "_created"}
            )

        await self.log_on_create(db_obj)
        return db_obj

    async def add_application(self, db: Session, db_obj: Team, user: models.User):
        if user not in db_obj.users:
            if user.id not in db_obj.appliers_ids:
                db_obj.applies.append(user)
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="The user already applied to the team",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="The user is part of the team",
            )
        #print(db_obj.organization_id)
        #print(db_obj.id)
        # Send mail to administrators to know there is an application to the team
        for admin in db_obj.administrators:
            _ = send_email(
                admin.email,
                'user_apply_team',
                {"org_id": db_obj.organization_id,
                 "team_id": db_obj.id,
                 "team_name": db_obj.name,
                 "user_email": user.email,
                 "user_name": user.full_name})

        await self.log_on_create(db_obj)
        return db_obj.applies

    # Override log methods
    def enrich_log_data(self, obj, logData):
        logData["model"] = "TEAM"
        logData["object_id"] = obj.id
        logData["team_id"] = obj.id
        logData["type"] = obj.type
        return logData

    # CRUD Permissions
    async def can_create(
        self, db: Session, organization_id: uuid.UUID, user: models.User
    ):
        org = await organizations_crud.get(db=db, id=organization_id)
        if org:
            if org.team_creation_permission == models.TeamCreationPermissions.anyone:
                return True
            elif (
                org.team_creation_permission
                == models.TeamCreationPermissions.administrators
            ):
                return user in org.administrators
            elif org.team_creation_permission == models.TeamCreationPermissions.members:
                return (
                    org
                    in db.query(models.Organization)
                    .join(Team)
                    .filter(Team.id.in_(user.teams_ids))
                    .all()
                    or user in org.administrators
                )
        return True

    def can_list(self, user):
        return True

    def can_read(self, user, object):
        return True

    def can_update(self, user, object):
        return user in object.administrators

    def can_remove(self, user, object):
        return user in object.administrators


exportCrud = CRUDTeam(Team)
