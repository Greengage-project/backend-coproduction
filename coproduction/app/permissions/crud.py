import copy
import uuid
from typing import List

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app import models, schemas
from app.general.utils.CRUDBase import CRUDBase
from app.models import Permission, TreeItem, CoproductionProcessNotification, UserNotification
from app.permissions.models import DENY_ALL, PERMS, GRANT_ALL, INDEXES
from app.coproductionprocesses.crud import exportCrud as coproductionprocesses_crud
from app.notifications.crud import exportCrud as notifications_crud
from app.treeitems.crud import exportCrud as treeitems_crud
from app.teams.crud import exportCrud as teams_crud
from app.schemas import PermissionCreate
from fastapi.encoders import jsonable_encoder
from app.sockets import socket_manager
from uuid_by_string import generate_uuid
from app.general.emails import send_email, send_team_email
import html


class CRUDPermission(CRUDBase[Permission, schemas.PermissionCreate, schemas.PermissionPatch]):

    async def remove(self, db: Session, *, id: uuid.UUID) -> Permission:
        db_obj = db.query(self.model).get(id)
        await self.log_on_remove(db_obj)

        db.delete(db_obj)
        # db.commit()

        # Save the event as a notification of coproduction
        coproduction = await coproductionprocesses_crud.get(db=db, id=db_obj.coproductionprocess_id)

        if (db_obj.team_id and db_obj.treeitem_id):
            # Se ha seleccionado un equipo para trabajar sonbre un treeitem.
            notification = await notifications_crud.get_notification_by_event(db=db, event="remove_team_treeitem", language=coproduction.language)
            treeitem = await treeitems_crud.get(db=db, id=db_obj.treeitem_id)
            # Create a notification for coproduction:
            team = await teams_crud.get(db=db, id=db_obj.team_id)

            newCoproNotification = CoproductionProcessNotification()
            newCoproNotification.notification_id = notification.id
            newCoproNotification.coproductionprocess_id = coproduction.id

            newCoproNotification.parameters = "{'teamName':'"+html.escape(team.name)+"','processName':'"+html.escape(coproduction.name)+"','team_id':'"+str(
                team.id)+"','treeItemName':'"+html.escape(treeitem.name)+"','treeitem_id':'"+str(treeitem.id)+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"

            db.add(newCoproNotification)
        else:

            notification = await notifications_crud.get_notification_by_event(db=db, event="remove_team_copro", language=coproduction.language)

            if (notification and db_obj.team_id):
                team = await teams_crud.get(db=db, id=db_obj.team_id)
                newCoproNotification = CoproductionProcessNotification()
                newCoproNotification.notification_id = notification.id
                newCoproNotification.coproductionprocess_id = coproduction.id
                # newCoproNotification.asset_id=null
                newCoproNotification.parameters = "{'teamName':'"+html.escape(team.name)+"','processName':'"+html.escape(
                    coproduction.name)+"','team_id':'"+str(team.id)+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"
                db.add(newCoproNotification)

                db.add(newCoproNotification)

                # Create a notification for every user:
                user_ids = team.user_ids
                for user_id in user_ids:
                    newUserNotification = UserNotification()
                    newUserNotification.user_id = user_id

                    newUserNotification.notification_id = notification.id
                    newUserNotification.channel = "in_app"
                    newUserNotification.state = False
                    newUserNotification.coproductionprocess_id = str(
                        db_obj.coproductionprocess_id)
                    newUserNotification.parameters = "{'teamName':'"+html.escape(team.name)+"','processName':'"+html.escape(
                        coproduction.name)+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"','org_id':'"+str(team.organization_id)+"'}"

                    db.add(newUserNotification)

                    await socket_manager.send_to_id(generate_uuid(user_id), {"event": self.modelName.lower() + "_created"})

        db.commit()
        db.refresh(newCoproNotification)

        return None

    async def create(self, db: Session, obj_in: PermissionCreate, creator: models.User, notifyAfterAdded=True) -> Permission:
        #print("LlAMA AL METODO CREATE DE PERMISSIONS:")

        obj_in_data = jsonable_encoder(obj_in)
        db_obj = Permission(**obj_in_data)

        db_obj.creator_id = creator.id

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # verify if the permission is of a (team or coproductionprocess)

        coproduction = await coproductionprocesses_crud.get(db=db, id=db_obj.coproductionprocess_id)
        if notifyAfterAdded:
            # Se ha seleccionado un equipo para trabajar sonbre un treeitem.
            if (db_obj.team_id and db_obj.treeitem_id):

                notification = await notifications_crud.get_notification_by_event(db=db, event="add_team_treeitem", language=coproduction.language)
                treeitem = await treeitems_crud.get(db=db, id=db_obj.treeitem_id)
                # Create a notification for coproduction:
                team = await teams_crud.get(db=db, id=db_obj.team_id)

                newCoproNotification = CoproductionProcessNotification()
                newCoproNotification.notification_id = notification.id
                newCoproNotification.coproductionprocess_id = coproduction.id

                newCoproNotification.parameters = "{'teamName':'"+html.escape(team.name)+"','processName':'"+html.escape(coproduction.name)+"','team_id':'"+str(
                    team.id)+"','treeItemName':'"+html.escape(treeitem.name)+"','treeitem_id':'"+str(treeitem.id)+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"
                db.add(newCoproNotification)
            else:

                # Se ha seleccionado un equipo para trabajar sonbre todo un proceso de coproduction.
                notification = await notifications_crud.get_notification_by_event(db=db, event="add_team_copro", language=coproduction.language)

                if (notification and db_obj.team_id):
                    # Create a notification for coproduction:
                    team = await teams_crud.get(db=db, id=db_obj.team_id)

                    newCoproNotification = CoproductionProcessNotification()
                    newCoproNotification.notification_id = notification.id
                    newCoproNotification.coproductionprocess_id = coproduction.id

                    newCoproNotification.parameters = "{'teamName':'"+html.escape(team.name)+"','processName':'"+html.escape(
                        coproduction.name)+"','team_id':'"+str(team.id)+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"

                    db.add(newCoproNotification)

                    # Create a notification for every user:
                    user_ids = team.user_ids
                    for user_id in user_ids:
                        newUserNotification = UserNotification()
                        newUserNotification.user_id = user_id

                        newUserNotification.notification_id = notification.id
                        newUserNotification.channel = "in_app"
                        newUserNotification.state = False
                        newUserNotification.coproductionprocess_id = str(
                            db_obj.coproductionprocess_id)

                        newUserNotification.parameters = "{'teamName':'"+html.escape(team.name)+"','processName':'"+html.escape(
                            coproduction.name)+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"','org_id':'"+str(team.organization_id)+"'}"

                        db.add(newUserNotification)

                        await socket_manager.send_to_id(generate_uuid(user_id), {"event": self.modelName.lower() + "_created"})

            db.commit()
            db.refresh(newCoproNotification)

            # Send mail to a team to know they are added to a coprod or treeitem
            if db_obj.treeitem_id and db_obj.team_id:
                treeitem = await treeitems_crud.get(db=db, id=db_obj.treeitem_id)
                _ = send_team_email(team,
                                    'add_team_treeitem',
                                    {"coprod_id": db_obj.coproductionprocess_id,
                                     "coprod_name": coproduction.name,
                                     "treeitem_id": db_obj.treeitem_id,
                                     "treeitem_name": treeitem.name,
                                     "team_name": team.name,
                                     "team_id": team.id,
                                     "org_id": team.organization_id
                                     })
            else:
                _ = send_team_email(team,
                                    'add_team_coprod',
                                    {"coprod_id": db_obj.coproductionprocess_id,
                                     "coprod_name": coproduction.name,
                                     "team_name": team.name,
                                     "org_id": team.organization_id,
                                     "team_id": team.id
                                     })

        await socket_manager.send_to_id(generate_uuid(creator.id), {"event": "permission" + "_created"})

        await self.log_on_create(db_obj)
        return db_obj

    async def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, treeitem: TreeItem
    ) -> List[Permission]:
        return db.query(Permission).filter(
            Permission.treeitem_id.in_(treeitem.path_ids)
        ).order_by(Permission.created_at.asc()).offset(skip).limit(limit).all()

    async def get_permission_user_coproduction(
        self, db: Session, user: models.User, *, coproductionprocess_id: uuid.UUID
    ) -> List[Permission]:
        return db.query(Permission).filter(
            Permission.coproductionprocess_id == coproductionprocess_id
        ).order_by(Permission.created_at.asc()).filter(
            and_(
                Permission.team_id.in_(user.teams_ids),
                Permission.treeitem_id == None
            )
        ).all()

    def get_for_user_and_treeitem(
        self, db: Session, user: models.User, treeitem: models.TreeItem
    ):
        #print('Llega a preguntar por los assets:')
        #print(db)
        return db.query(
            Permission
        ).filter(
            or_(
                and_(
                    Permission.treeitem_id.in_(treeitem.path_ids),
                    Permission.coproductionprocess_id == treeitem.coproductionprocess.id
                ),
                and_(
                    Permission.treeitem_id == None,
                    Permission.coproductionprocess_id == treeitem.coproductionprocess.id
                ),
            ),
            Permission.team_id.in_(user.teams_ids)
        ).all()
    
    async def get_for_user_and_treeitem_async(
        self, db: Session, user: models.User, treeitem: models.TreeItem
    ):
        #print('Llega a preguntar por los assets:')
        #print(db)
        return db.query(
            Permission
        ).filter(
            or_(
                and_(
                    Permission.treeitem_id.in_(treeitem.path_ids),
                    Permission.coproductionprocess_id == treeitem.coproductionprocess.id
                ),
                and_(
                    Permission.treeitem_id == None,
                    Permission.coproductionprocess_id == treeitem.coproductionprocess.id
                ),
            ),
            Permission.team_id.in_(user.teams_ids)
        ).all()

    def get_user_roles(self, db: Session, treeitem: models.TreeItem, user: models.User):
        roles = []
        for perm in self.get_for_user_and_treeitem(db=db, user=user, treeitem=treeitem):
            role = perm.team.type.value
            if role not in roles:
                roles.append(role)

        if user in treeitem.coproductionprocess.administrators:
            roles.append('administrator')
        return roles

    def get_dict_for_user_and_treeitem(self, db: Session, treeitem: models.TreeItem, user: models.User):
        if user in treeitem.coproductionprocess.administrators:
            return GRANT_ALL
        permissions = self.get_for_user_and_treeitem(
            db=db, user=user, treeitem=treeitem)

        final_permissions_dict = copy.deepcopy(DENY_ALL)
        indexes_dict = copy.deepcopy(INDEXES)

        path = treeitem.path_ids

        for permission in permissions:
            path_con = permission.treeitem_id or permission.coproductionprocess_id
            index = path.index(path_con)

            for permission_key in PERMS:
                if index > indexes_dict[permission_key]:
                    final_permissions_dict[permission_key] = getattr(
                        permission, permission_key)
                    indexes_dict[permission_key] = index
                elif index == indexes_dict[permission_key] and not final_permissions_dict[permission_key] and getattr(permission, permission_key):
                    final_permissions_dict[permission_key] = True

        return final_permissions_dict

    def enrich_log_data(self, obj, logData):
        logData["model"] = "PERMISSION"
        logData["object_id"] = obj.id
        logData["coproductionprocess_id"] = obj.coproductionprocess_id
        logData["treeitem_id"] = obj.treeitem_id
        logData["team_id"] = obj.team_id
        return logData

    def user_can(self, db, user, task, permission):
        if user in task.coproductionprocess.administrators:
            return True
        if permission in PERMS:
            perms: dict = self.get_dict_for_user_and_treeitem(
                db=db, treeitem=task, user=user)
            return perms[permission]
        raise Exception(permission + " is not a valid permission")

    # CRUD Permissions
    def can_create(self, user):
        return True

    def can_list(self, user):
        return True

    def can_read(self, user, object):
        return True

    def can_update(self, user, object):
        return True

    def can_remove(self, user, object):
        return True


exportCrud = CRUDPermission(Permission, logByDefault=True)
