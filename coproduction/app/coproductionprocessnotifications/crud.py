from app.messages import log
from typing import Any, Dict, Optional, List

from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app.models import Notification, CoproductionProcessNotification, User, Organization, Asset
from app.schemas import NotificationCreate, NotificationPatch, CoproductionProcessNotificationCreate, CoproductionProcessNotificationPatch
import uuid
from app import models
from app.users.crud import exportCrud as users_crud
from app.assets.crud import exportCrud as assets_crud
from app.treeitems.crud import exportCrud as treeitems_crud

from sqlalchemy import or_, and_
from fastapi.encoders import jsonable_encoder
from app.sockets import socket_manager
from uuid_by_string import generate_uuid
from app import crud, models, schemas
import json
import html
from app.messages import log


class CRUDCoproductionProcessNotification(CRUDBase[CoproductionProcessNotification, CoproductionProcessNotificationCreate, CoproductionProcessNotificationPatch]):
    async def get_multi(self, db: Session, user: User) -> Optional[List[CoproductionProcessNotification]]:
        return db.query(CoproductionProcessNotification).all()

    # Get all notifications by user:
    async def get_coproductionprocess_notifications(self, db: Session, coproductionprocess_id: str, user) -> Optional[List[CoproductionProcessNotification]]:

        listofCoproductionProcessNotifications = db.query(CoproductionProcessNotification).filter(
            models.CoproductionProcessNotification.coproductionprocess_id == coproductionprocess_id).order_by(models.CoproductionProcessNotification.created_at.desc()).all()

        # Filtrar las notificaciones a las que tengo permisos:
        for notification in listofCoproductionProcessNotifications:
            if notification.asset_id:
                queries = []
                queries.append(Asset.id == notification.asset_id)
                asset = db.query(Asset).filter(*queries).first()

                if (asset):
                    tienePermisosListado = assets_crud.can_list(
                        db=db, user=user, task=asset.task)

                    # Remove the notification a user dont have permissions
                    if not tienePermisosListado:
                        listofCoproductionProcessNotifications.remove(
                            notification)
                else:
                    listofCoproductionProcessNotifications.remove(notification)

        return listofCoproductionProcessNotifications

    async def get_coproductionprocess_notifications_byAseetId(self, db: Session, coproductionprocess_id: str, asset_id: str) -> Optional[List[CoproductionProcessNotification]]:
        listofCoproductionProcessNotifications = db.query(CoproductionProcessNotification).filter(and_(
            models.CoproductionProcessNotification.coproductionprocess_id == coproductionprocess_id,
            models.CoproductionProcessNotification.asset_id == asset_id
        )
        ).order_by(models.CoproductionProcessNotification.created_at.desc()).all()
        # print(listofCoproductionProcessNotifications)
        return listofCoproductionProcessNotifications

    async def get_coproductionprocess_notifications_justbyAseetId(self, db: Session, asset_id: str) -> Optional[List[CoproductionProcessNotification]]:
        listofCoproductionProcessNotifications = db.query(CoproductionProcessNotification).filter(models.CoproductionProcessNotification.asset_id == asset_id
                                                                                                  ).order_by(models.CoproductionProcessNotification.created_at.desc()).all()
        # print(listofCoproductionProcessNotifications)
        return listofCoproductionProcessNotifications

    async def create(self, db: Session, obj_in: CoproductionProcessNotificationCreate) -> CoproductionProcessNotification:

        obj_in_data = jsonable_encoder(obj_in)

        db_obj = CoproductionProcessNotification(**obj_in_data)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        parametros = json.loads(db_obj.parameters)

        selectTreeItemId = json.loads(db_obj.parameters)[
            'treeitem_id']
        await socket_manager.broadcast({"event": "contribution_created", "extra": {"task_id": selectTreeItemId}})

        # await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": "contribution_created", "extra": {"task_id": jsonable_encoder(parametros['treeitem_id'])}})

        if( db_obj.claim_type is None ):
            await self.log_on_create(db_obj)
        else:
            #When the notification is a claim, we need to create a log
            await log({"action": "CREATE","model":"CLAIM","object_id":db_obj.id,"asset_id":db_obj.asset_id,"task_id":selectTreeItemId,"coproductionprocess_id":db_obj.coproductionprocess_id})


        return db_obj

    async def createList(self, db: Session, registros: List[CoproductionProcessNotificationCreate]) -> Any:
        try:
            # Iniciar una transacción
            # with db.begin() as transaction:

            if (len(registros) > 0):

                coproductionProcessId = ''
                selectTreeItemId = ''

                for notification in registros:
                    # Crear una instancia de la entidad CoproductionProcessNotification
                    obj_in_data = jsonable_encoder(notification)
                    notification_model = CoproductionProcessNotification(
                        **obj_in_data)
                    notification_model.user_id = notification.user_id

                    # Agregar la instancia a la sesión de SQLAlchemy
                    db.add(notification_model)

                    # print('The selected coproductionProcess is:')
                    # print(notification_model.coproductionprocess_id)
                    # print('The selected treeItem is:')
                    # print(json.loads(notification_model.parameters)
                    #       ['treeitem_id'])
                    coproductionProcessId = notification_model.coproductionprocess_id
                    selectTreeItemId = json.loads(notification_model.parameters)[
                        'treeitem_id']
                    
                    db.commit()
                    db.refresh(notification_model)

                    if( notification_model.claim_type is None ):
                        await self.log_on_create(notification_model)
                    else:
                        #When the notification is a claim, we need to create a log
                        await log({"action": "CREATE","model":"CLAIM","object_id":notification_model.id,"asset_id":notification_model.asset_id,"task_id":selectTreeItemId,"coproductionprocess_id":notification_model.coproductionprocess_id})

                

                # Envio la notificacion al socket

                await socket_manager.broadcast({"event": "contribution_created", "extra": {"task_id": selectTreeItemId}})
               # await socket_manager.send_to_id(coproductionProcessId, {"event": "contribution_created", "extra": {"task_id": selectTreeItemId}})

            return True
        except Exception as e:
            # Rollback the transaction in case of any exceptions
            db.rollback()
            print(f"Error in create_notifications: {str(e)}")
            return False

    async def update(
        self,
        db: Session,
        db_obj: CoproductionProcessNotification,
        obj_in: schemas.CoproductionProcessNotificationPatch
    ) -> CoproductionProcessNotification:
        obj_data = jsonable_encoder(db_obj)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        await self.log_on_update(db_obj)
        return db_obj

    async def updateAssetNameParameter(
        self,
        db: Session,
        asset_id: str,
        name: str,
        coproductionprocess_id: str
    ) -> Optional[List[CoproductionProcessNotification]]:

        resultNot = db.query(models.CoproductionProcessNotification).filter(
            models.CoproductionProcessNotification.coproductionprocess_id == coproductionprocess_id).all()

        # Loop all notifications of the coproduction process
        for copronot in resultNot:

            # Set the dinamic parameters
            parametersJson = json.loads(copronot.parameters.replace("'", '"'))

            if ('assetName' in json.dumps(parametersJson)):

                parametersJson['assetName'] = parametersJson['assetName'].replace(
                    '{assetid:'+asset_id+'}', html.escape(name))
                parametersJson['assetLink'] = ''
                parametersJson['showIcon'] = 'hidden'
                parametersJson['showLink'] = ''

                copronot.parameters = json.dumps(parametersJson)

                # copronot.parameters=copronot.parameters.replace('{assetid:'+asset_id+'}', name)
                # print('resp '+copronot.parameters)
                db.add(copronot)

        db.commit()
        # print('Se ha reemplazado exitosamente los nombres: '+str(asset_id)+' por '+name)

        return


exportCrud = CRUDCoproductionProcessNotification(
    CoproductionProcessNotification)
