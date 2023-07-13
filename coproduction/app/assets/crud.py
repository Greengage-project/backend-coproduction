from fastapi import HTTPException
import requests
import os.path
from app.config import settings
from sqlalchemy.orm import Session
from typing import List
from app.models import Asset, InternalAsset, ExternalAsset, CoproductionProcessNotification
from app.tasks.crud import exportCrud as tasksCrud
from app.schemas import AssetCreate, AssetPatch, ExternalAssetCreate, InternalAssetCreate
from app.general.utils.CRUDBase import CRUDBase
from app import models
import uuid
from app.messages import log
from fastapi.encoders import jsonable_encoder
import favicon
from app.tasks.crud import update_status_and_progress
from app.permissions.crud import exportCrud as permissionsCrud
from app.general.deps import get_current_user_from_context
from app.sockets import socket_manager
from app.notifications.crud import exportCrud as notification_crud
from app.coproductionprocesses.crud import exportCrud as coproductionprocesses_crud
from fastapi import Depends
from app.general import deps
import html
from app.config import settings


class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetPatch]):
    async def get_multi(
        self, db: Session, task: models.Task, skip: int = 0, limit: int = 100
    ) -> List[Asset]:
        queries = []
        if task:
            queries.append(Asset.task_id == task.id)
        return db.query(Asset).filter(*queries).offset(skip).limit(limit).all()

    async def get_multi_withIntData(
        self, db: Session, task: models.Task, skip: int = 0, limit: int = 100, token: str = ''
    ) -> List[Asset]:
        queries = []
        if task:
            queries.append(Asset.task_id == task.id)

        listAssets = db.query(Asset).filter(
            *queries).offset(skip).limit(limit).all()

        # print('Entra en multi_withIntData')

        for asset in listAssets:
            if asset.type == "internalasset":

                serverName = settings.SERVER_NAME
                # print("ServerName")
                # print(serverName)

                if ('loomio' in asset.link):

                    print("Es un loomio")
                    asset_name = "Loomio File"
                    import traceback

                    try:

                        print('Asset id is:'+str(asset.external_asset_id))
                        print('The request is:')

                        cookies = {'auth_token': token}
                        requestUrl = f"https://loomio/api/v1/assets/{str(asset.external_asset_id)}"
                        print(requestUrl)

                        response = requests.get(requestUrl, headers={
                            "Authorization": "Bearer " + token
                        }, cookies=cookies)

                        responseDataJson = response.json()

                        print('Response:')
                        print(responseDataJson)
                        print('--------')

                        asset_name = responseDataJson.name
                        print(asset_name)
                    except Exception:
                        traceback.print_exc()
                        pass

                    print("loomio")
                    asset.internalData = {
                        'icon': 'https://'+serverName+'/catalogue/static/loomio/logotype.png', 'name': asset_name, 'link': asset.link}
                else:

                    if ('servicepedia' in asset.link):
                        # print("Servicepedia")
                        # print('Es servicepedia')

                        requestlink = f"http://augmenterservice/assets/{asset.external_asset_id}"
                        response = requests.get(requestlink)
                        datosAsset = response.json()
                        # print(datosAsset)

                        asset_uri = asset.link+'/view'
                        asset.internalData = {
                            'icon': 'https://'+serverName+'/catalogue/static/augmenter/logotype.png', 'name': datosAsset['name'], 'link': asset_uri}

                    else:
                        # print("Internal Asset")
                        serviceName = os.path.split(
                            asset.link)[0].split('/')[3]
                        requestlink = f"http://{serviceName}/assets/{asset.external_asset_id}"

                        # print(requestlink)
                        response = requests.get(requestlink)

                        # print(response)
                        datosAsset = response.json()
                        asset.internalData = datosAsset

            if asset.type == "externalasset":
                # print("External Asset")
                asset.internalData = {'icon': asset.icon,
                                      'name': asset.name, 'link': asset.uri}

        return listAssets

    def shortName(self, s):
        # split the string into a list
        l = s.split()
        new = ""
        # traverse in the list
        for i in range(len(l)-1):
            s = l[i]
            # adds the capital first character
            new += (s[0].upper()+'.')

        # l[-1] gives last item of list l. We
        # use title to print first character in
        # capital.
        new += l[-1].title()
        return new

    async def remove(self, db: Session, *, id: uuid.UUID) -> Asset:
        db_obj_Aseet = db.query(self.model).get(id)
        await self.log_on_remove(db_obj_Aseet)

        # Save the event as a notification of coproduction

        if db_obj_Aseet.type == 'externalasset':
            db_obj = db_obj_Aseet
            # External Asset
            # Create the coproductionNotification
            coproduction = await coproductionprocesses_crud.get(db=db, id=db_obj.coproductionprocess_id)
            notification = await notification_crud.get_notification_by_event(db=db, event="remove_asset_copro", language=coproduction.language)
            if (notification):
                task = await tasksCrud.get(db=db, id=db_obj.task_id)

                newCoproNotification = CoproductionProcessNotification()
                newCoproNotification.notification_id = notification.id
                newCoproNotification.coproductionprocess_id = coproduction.id
                newCoproNotification.asset_id = db_obj.id

                # print(data)
                # print(db_obj.externalinterlinker)
                asset = db_obj
                nameInterlinker = 'external'

                assetLink = asset.uri

                newCoproNotification.parameters = "{'showLink':'hidden','showIcon':'','treeitem_id':'"+str(task.id)+"','treeItemName':'"+str(html.escape(task.name))+"','assetId':'"+str(db_obj.id)+"','assetName':'"+html.escape(asset.name)+"','assetLink':'"+str(
                    assetLink)+"','interlinkerName':'"+html.escape(nameInterlinker)+"','processName':'"+html.escape(coproduction.name)+"','userName':'"+html.escape(self.shortName(db_obj.creator.full_name))+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"
                db.add(newCoproNotification)
        if db_obj_Aseet.type == 'internalasset':
            db_obj = db_obj_Aseet
            # Internal Asset
            # Create the coproductionNotification
            coproduction = await coproductionprocesses_crud.get(db=db, id=db_obj.coproductionprocess_id)
            notification = await notification_crud.get_notification_by_event(db=db, event="remove_asset_copro", language=coproduction.language)

            if (notification):

                task = await tasksCrud.get(db=db, id=db_obj.task_id)

                newCoproNotification = CoproductionProcessNotification()
                newCoproNotification.notification_id = notification.id
                newCoproNotification.coproductionprocess_id = coproduction.id
                newCoproNotification.asset_id = db_obj.id

                nameInterlinker = ''
                assetLink = ''

                assetLink = db_obj.link+'/view'
                if (db_obj.softwareinterlinker):
                    nameInterlinker = db_obj.softwareinterlinker['name']

                else:
                    if (db_obj.knowledgeinterlinker):
                        nameInterlinker = db_obj.knowledgeinterlinker['name']

                # Obtengo la info del Asset:

                newCoproNotification.parameters = "{'showLink':'hidden','showIcon':'','treeitem_id':'"+str(task.id)+"','treeItemName':'"+str(html.escape(task.name))+"','assetId':'"+str(db_obj.id)+"','assetName':'{assetid:"+str(db_obj.id)+"}','assetLink':'"+str(
                    assetLink)+"','interlinkerName':'"+html.escape(nameInterlinker)+"','processName':'"+html.escape(coproduction.name)+"','userName':'"+html.escape(self.shortName(db_obj.creator.full_name))+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"
                db.add(newCoproNotification)

        db.delete(db_obj_Aseet)
        db.commit()

        return None

    async def create(self, db: Session, asset: AssetCreate, creator: models.User, task: models.Task) -> Asset:
        data = jsonable_encoder(asset)
        icon_path = None
        if type(asset) == ExternalAssetCreate:

            data["type"] = "externalasset"

            # try to get favicon
            try:
                icons = favicon.get(asset.uri)
                if len(icons) > 0 and (icon := icons[0]) and icon.format:
                    response = requests.get(icon.url, stream=True)

                    icon_path = f'/app/static/assets/{uuid.uuid4()}.{icon.format}'
                    with open(icon_path, 'wb') as image:
                        for chunk in response.iter_content(1024):
                            image.write(chunk)
                    icon_path = icon_path.replace("/app", "")

                    data["icon_path"] = icon_path
            except:
                pass
            db_obj = ExternalAsset(**data, creator=creator, objective_id=task.objective_id,
                                   phase_id=task.objective.phase_id, coproductionprocess_id=task.objective.phase.coproductionprocess_id)

        if type(asset) == InternalAssetCreate:

            data["type"] = "internalasset"
            db_obj = InternalAsset(**data, creator=creator, objective_id=task.objective_id,
                                   phase_id=task.objective.phase_id, coproductionprocess_id=task.objective.phase.coproductionprocess_id)

        db.add(db_obj)
        db.commit()
        task: models.Task = db_obj.task
        if task.status == models.Status.awaiting:
            task.status = models.Status.in_progress
            db.add(task)
            update_status_and_progress(task.objective)
            db.add(task.objective)
            update_status_and_progress(task.objective.phase)
            db.add(task.objective.phase)
            db.commit()

        db.refresh(db_obj)

        # Save the notifications:

        if type(asset) == ExternalAssetCreate:
            #     #External Asset
            #     #Create the coproductionNotification
            coproduction = await coproductionprocesses_crud.get(db=db, id=db_obj.coproductionprocess_id)
            notification = await notification_crud.get_notification_by_event(db=db, event="add_asset_copro", language=coproduction.language)
            if (notification):
                task = await tasksCrud.get(db=db, id=db_obj.task_id)

                newCoproNotification = CoproductionProcessNotification()
                newCoproNotification.notification_id = notification.id
                newCoproNotification.coproductionprocess_id = coproduction.id
                newCoproNotification.asset_id = db_obj.id

                nameInterlinker = 'external'
                assetLink = asset.uri

                if (icon_path):
                    pass
                else:
                    icon_path = '/static/graphics/external_link.svg'

                newCoproNotification.parameters = "{'showLink':'hidden','showIcon':'','treeitem_id':'"+str(task.id)+"','treeItemName':'"+html.escape(str(task.name))+"','assetId':'"+str(db_obj.id)+"','assetIcon':'"+icon_path+"','assetName':'"+html.escape(asset.name)+"','assetLink':'"+str(
                    assetLink)+"','interlinkerName':'"+html.escape(nameInterlinker)+"','processName':'"+html.escape(coproduction.name)+"','userName':'"+html.escape(self.shortName(db_obj.creator.full_name))+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"
                db.add(newCoproNotification)
        if type(asset) == InternalAssetCreate:

            # Internal Asset
            # Create the coproductionNotification
            coproduction = await coproductionprocesses_crud.get(db=db, id=db_obj.coproductionprocess_id)
            notification = await notification_crud.get_notification_by_event(db=db, event="add_asset_copro", language=coproduction.language)

            if (notification):
                task = await tasksCrud.get(db=db, id=db_obj.task_id)

                newCoproNotification = CoproductionProcessNotification()
                newCoproNotification.notification_id = notification.id
                newCoproNotification.coproductionprocess_id = coproduction.id
                newCoproNotification.asset_id = db_obj.id

                nameInterlinker = ''
                assetLink = ''
                serverName = settings.SERVER_NAME
                optionalAssetIconText = ''

                assetLink = db_obj.link+'/view'
                if (db_obj.softwareinterlinker):
                    nameInterlinker = db_obj.softwareinterlinker['name']

                    if (nameInterlinker == 'loomio'):
                        assetIcon = 'https://'+serverName+'/catalogue/static/loomio/logotype.png'
                        optionalAssetIconText = ",'assetIcon':'"+assetIcon+"'"

                else:
                    if (db_obj.knowledgeinterlinker):
                        nameInterlinker = db_obj.knowledgeinterlinker['name']

                newCoproNotification.parameters = "{'showLink':'hidden','showIcon':'','treeitem_id':'"+str(task.id)+"','treeItemName':'"+html.escape(str(task.name))+"','assetId':'"+str(db_obj.id)+"'"+optionalAssetIconText+",'assetName':'{assetid:"+str(db_obj.id)+"}','assetLink':'"+str(
                    assetLink)+"','interlinkerName':'"+html.escape(nameInterlinker)+"','processName':'"+html.escape(coproduction.name)+"','userName':'"+html.escape(self.shortName(db_obj.creator.full_name))+"','copro_id':'"+str(db_obj.coproductionprocess_id)+"'}"
                db.add(newCoproNotification)

        db.commit()

        await self.log_on_create(db_obj)
        await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": "asset_created", "extra": {"task_id": jsonable_encoder(db_obj.task_id)}})
        return db_obj

    async def copy(self, db: Session, asset: AssetCreate, creator: models.User, task: models.Task, token, justRead=False) -> Asset:
        # print('Start to copy the assets')
        # print(asset.id)
        # print(asset.type)
        # print('')
        if asset.type == 'internalasset':
            # print('Copying internal asset')

            methodCloneCall = "/clone"
            params = {'justRead': justRead}

            # print(methodCloneCall)
            data_from_interlinker = None
            try:
                # print('The request is:')
                # print(asset.internal_link + methodCloneCall)
                data_from_interlinker = requests.post(asset.internal_link + methodCloneCall, params=params, headers={
                    "Authorization": "Bearer " + token
                }).json()
            except:
                try:
                    # print('The request try again with:')
                    # print(asset.link + methodCloneCall)
                    data_from_interlinker = requests.post(asset.link + methodCloneCall, params=params, headers={
                        "Authorization": "Bearer " + token
                    }).json()
                except:
                    pass
            if (data_from_interlinker):
                # print(data_from_interlinker)
                external_asset_id = data_from_interlinker[
                    "id"] if "id" in data_from_interlinker else data_from_interlinker["_id"]

                new_asset = InternalAssetCreate(task_id=task.id,
                                                softwareinterlinker_id=asset.softwareinterlinker_id,
                                                knowledgeinterlinker_id=asset.knowledgeinterlinker_id,
                                                external_asset_id=external_asset_id)
                await self.create(db=db, asset=new_asset, creator=creator, task=task)

        elif asset.type == 'externalasset':
            # print('Copying external asset')
            new_asset = ExternalAssetCreate(task_id=task.id,
                                            externalinterlinker_id=asset.externalinterlinker_id,
                                            name=asset.name,
                                            uri=asset.uri)
            await self.create(db=db, asset=new_asset, creator=creator, task=task)

        return None

    # Override log methods
    def enrich_log_data(self, asset, logData):
        db = Session.object_session(asset)
        user = get_current_user_from_context(db=db)

        logData["model"] = "ASSET"
        logData["object_id"] = asset.id
        logData["type"] = asset.type
        logData["phase_id"] = asset.task.objective.phase_id
        logData["objective_id"] = asset.task.objective_id
        logData["task_id"] = asset.task_id
        logData["coproductionprocess_id"] = asset.task.objective.phase.coproductionprocess_id
        logData["roles"] = permissionsCrud.get_user_roles(
            db=db, user=user, treeitem=asset.task)

        if type(asset) == models.InternalAsset:
            if ki := asset.knowledgeinterlinker:
                logData["knowledgeinterlinker_id"] = ki.get("id")
                logData["knowledgeinterlinker_name"] = ki.get("name")
            if si := asset.softwareinterlinker:
                logData["softwareinterlinker_id"] = si.get("id")
                logData["softwareinterlinker_name"] = si.get("name")
        elif type(asset) == models.ExternalAsset:
            if ei := asset.externalinterlinker:
                logData["externalinterlinker_id"] = ei.get("id")
                logData["externalinterlinker_name"] = ei.get("name")
        return logData

    # CRUD Permissions

    def can_create(self, db: Session, user: models.User, task: models.TreeItem):
        # print('entra en can_create')
        # print(db)
        return permissionsCrud.user_can(db=db, user=user, task=task, permission="create_assets_permission")

    def can_list(self, db: Session, user: models.User, task: models.TreeItem):
        return permissionsCrud.user_can(db=db, user=user, task=task, permission="access_assets_permission")

    def can_read(self, db: Session, user: models.User, task: models.TreeItem):
        return permissionsCrud.user_can(db=db, user=user, task=task, permission="access_assets_permission")

    def can_update(self, db: Session, user: models.User, task: models.TreeItem):
        return permissionsCrud.user_can(db=db, user=user, task=task, permission="create_assets_permission")

    def can_remove(self, db: Session, user: models.User, task: models.TreeItem):
        return permissionsCrud.user_can(db=db, user=user, task=task, permission="delete_assets_permission")


exportCrud = CRUDAsset(Asset, logByDefault=True)
