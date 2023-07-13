import uuid
import os.path

import requests
from typing import List, Optional

from slugify import slugify
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from app import crud, models
from app.general.utils.CRUDBase import CRUDBase
from app.models import CoproductionProcess, Permission, User, Permission, TreeItem, Asset
from app.schemas import CoproductionProcessCreate, CoproductionProcessPatch, PermissionCreate
from fastapi.encoders import jsonable_encoder
from app.messages import log
from app.treeitems.crud import exportCrud as treeitemsCrud
from app.sockets import socket_manager
from app.utils import check_prerequistes
from app.config import settings
from fastapi import HTTPException
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Query, subqueryload
from sqlalchemy import func





class CRUDCoproductionProcess(CRUDBase[CoproductionProcess, CoproductionProcessCreate, CoproductionProcessPatch]):
    async def get_multi_by_user(self, db: Session, user: User, search: str = None) -> Optional[List[CoproductionProcess]]:
        # await log({
        #     "model": self.modelName,
        #     "action": "LIST",
        # })
        admins = db.query(
            CoproductionProcess
        ).join(
            CoproductionProcess.administrators
        ).filter(
            User.id.in_([user.id])
        )

        user_permissions = db.query(
            CoproductionProcess
        ).join(
            CoproductionProcess.permissions
        ).filter(
            or_(
                Permission.user_id == user.id,
                Permission.team_id.in_(user.teams_ids)
            ),
        )

        query = admins.union(user_permissions)
        if search:
            query = query.filter(
                CoproductionProcess.name.contains(search),
            )

        return query.order_by(CoproductionProcess.created_at.asc()).all()

    async def get_multi_public(self, db: Session, exclude: list = [], search: str = "", rating: int = 0, language: str = "en", tag: list = []
                               ) -> Optional[List[CoproductionProcess]]:
        
        print("tag", tag)

        queries = []

        
        if rating:
                queries.append(CoproductionProcess.rating >= rating)

        if search!="":
            if search:
                search = search.lower()
                queries.append(or_(
                        # func.lower(Story.keywords_translations[language]).contains(
                        #     search),
                        func.lower(CoproductionProcess.name).contains(func.lower(
                            search)),
                        func.lower(
                            CoproductionProcess.description).contains(func.lower(search))
                    ))
            
        
        if tag and any(tag):
            subq = (
                db.query(CoproductionProcess.id)
                .join(CoproductionProcess.tags)
                .filter(models.Tag.name.in_(tag))
                .group_by(CoproductionProcess.id)
                .having(func.count(func.distinct(models.Tag.name)) == len(tag))
                .subquery()
            )
            queries.append(CoproductionProcess.id.in_(subq))
            query: Query = db.query(CoproductionProcess).join(CoproductionProcess.tags)
        else:
            query: Query = db.query(CoproductionProcess)

        queries.append(CoproductionProcess.is_public == True)

        
        query = query.options(subqueryload(CoproductionProcess.tags))

        query = query.filter(*queries, CoproductionProcess.id.not_in(exclude))

        return paginate(query)

       


    async def get_assets(self, db: Session, coproductionprocess: CoproductionProcess, user: models.User,token:str):

        # Query and add public info to the asset
        def obtainpublicData(listOfAssets):

            for asset in listOfAssets:
                if asset.type == "internalasset":

                    serverName=settings.SERVER_NAME
                    #print("ServerName")
                    #print(serverName)

                    if('loomio' in asset.link):
                        print("Es un loomio")
                        asset_name="Loomio File"
                        import traceback

                        try:
                            
                            print('Asset id is:'+str(asset.external_asset_id))
                            print('The request is:')

                            cookies = {'auth_token': token}
                            requestUrl=f"https://loomio/api/v1/assets/{str(asset.external_asset_id)}"
                            print(requestUrl)
                            
                            response = requests.get(requestUrl, headers={
                            "Authorization": "Bearer " + token
                            }, cookies=cookies)

                            responseDataJson=response.json()

                            print('Response:')                            
                            print(responseDataJson)
                            print('--------')

                            asset_name=responseDataJson.name
                            print(asset_name)
                        except  Exception:
                            traceback.print_exc()
                            pass



                        asset.internalData={'icon':'https://'+serverName+'/catalogue/static/loomio/logotype.png','name':asset_name,'link':asset.link}
                    else:

                        if ('servicepedia' in asset.link):
                            #print(" Es un Servicepedia")
                            # #print('Es servicepedia')

                            requestlink = f"http://augmenterservice/assets/{asset.external_asset_id}"
                            response = requests.get(requestlink)
                            datosAsset = response.json()
                            #print(datosAsset)

                            asset_uri = asset.link+'/view'
                            asset.internalData = {
                                'icon': 'https://'+serverName+'/catalogue/static/augmenter/logotype.png', 'name': datosAsset['name'], 'link': asset_uri}

                        else:
                            #print("Es un Internal Asset")
                            serviceName = os.path.split(asset.link)[0].split('/')[3]
                            requestlink = f"http://{serviceName}/assets/{asset.external_asset_id}"
                            response = requests.get(requestlink)
                            datosAsset = response.json()
                            asset.internalData = datosAsset

                if asset.type == "externalasset":
                    #print("Es un External Asset")
                    queries = []
                    queries.append(Asset.id == asset.id)
                    datosAsset = db.query(Asset).filter(*queries).first()
                    asset.internalData = {'icon': datosAsset.icon,
                                          'name': datosAsset.name, 'link': datosAsset.uri}

            return listOfAssets

        # En el caso que seas un administrador del proceso (muestro todo):

        # or self.can_read(db, user, coproductionprocess):
        if user in coproductionprocess.administrators:
            # print('Es administrador!!')
            listOfAssets = db.query(
                Asset
            ).filter(
                Asset.task_id.in_(coproductionprocess.task_ids())
            ).order_by(models.Asset.created_at.desc()).all()

            # Agrego informacion del asset interno
            listOfAssets = obtainpublicData(listOfAssets)

            return listOfAssets

        # En el caso que tengas permisos sobre todo el proceso:
        # Pregunto si tienes permisos
        listPermissionsAllProcess = await crud.permission.get_permission_user_coproduction(db=db, user=user, coproductionprocess_id=coproductionprocess.id)
        if (len(listPermissionsAllProcess) > 0):
            # print('Tiene permisos para todo el proceso!!')
            # Si es asi muestro todos los assets igual que el admin

            listOfAssets = db.query(
                Asset
            ).filter(
                Asset.task_id.in_(coproductionprocess.task_ids())
            ).order_by(models.Asset.created_at.desc()).all()

            # Agrego informacion del asset interno
            listOfAssets = obtainpublicData(listOfAssets)

            return listOfAssets

        #print('No es admin ni permisos generales, busco por treeitem')
        # En el caso que tengas permisos sobre treeitems Individuales:
        ids = [treeitem.id for treeitem in await treeitemsCrud.get_for_user_and_coproductionprocess(db=db, user=user, coproductionprocess_id=coproductionprocess.id) if not treeitem.disabled_on]

        listOfAssets = db.query(
            models.Asset
        ).filter(
            or_(
                models.Asset.phase_id.in_(ids),
                models.Asset.objective_id.in_(ids),
                models.Asset.task_id.in_(ids),
            )
        ).order_by(models.Asset.created_at.desc()).all()

        # Check if the user has the permissions to see the asset.
        for asset in listOfAssets:
            #print(asset)
            tienePermisosListado = crud.asset.can_list(
                db=db, user=user, task=asset.task)
            if not tienePermisosListado:
                listOfAssets.remove(asset)

        # Agrego informacion del asset interno
        listOfAssets = obtainpublicData(listOfAssets)

        return listOfAssets

    async def clear_schema(self, db: Session, coproductionprocess: models.CoproductionProcess):
        schema = coproductionprocess.schema_used
        for phase in coproductionprocess.children:
            await crud.phase.remove(db=db, id=phase.id, remove_definitely=True, withNotifications=False)
        enriched: dict = self.enrich_log_data(coproductionprocess, {
            "action": "CLEAR_SCHEMA",
            "coproductionprocess_id": coproductionprocess.id,
            "coproductionschema_id": schema
        })
        await log(enriched)
        db.refresh(coproductionprocess)
        await socket_manager.send_to_id(coproductionprocess.id, {"event": "schema_cleared"})
        return coproductionprocess

    async def set_logotype(self, db: Session, coproductionprocess: models.CoproductionProcess, logotype_path: str):

        coproductionprocess.logotype = logotype_path
        db.add(coproductionprocess)
        db.commit()
        db.refresh(coproductionprocess)

        # await socket_manager.send_to_id(coproductionprocess.id, {"event": "coproductionprocess_updated"})

        return coproductionprocess

    async def set_schema(self, db: Session, coproductionprocess: models.CoproductionProcess, coproductionschema: dict):
        total = {}
        schema_id = coproductionschema.get("id")
        for phasemetadata in coproductionschema.get("children", []):
            phasemetadata: dict
            db_phase = await crud.phase.create_from_metadata(
                db=db,
                phasemetadata=phasemetadata,
                coproductionprocess=coproductionprocess,
                schema_id=schema_id
            )

            #  Add new phase object and the prerequisites for later loop
            total[phasemetadata["id"]] = {
                "type": "phase",
                "prerequisites_ids": phasemetadata["prerequisites_ids"] or [],
                "newObj": db_phase,
            }

            for objectivemetadata in phasemetadata.get("children", []):
                objectivemetadata: dict
                db_obj = await crud.objective.create_from_metadata(
                    db=db,
                    objectivemetadata=objectivemetadata,
                    phase=db_phase,
                    schema_id=schema_id
                )
                #  Add new objective object and the prerequisites for later loop
                total[objectivemetadata["id"]] = {
                    "type": "objective",
                    "prerequisites_ids": objectivemetadata["prerequisites_ids"] or [],
                    "newObj": db_obj,
                }
                for taskmetadata in objectivemetadata.get("children", []):
                    if 'management' not in taskmetadata:
                        taskmetadata['management'] = 0
                    if 'development' not in taskmetadata:
                        taskmetadata['development'] = 0
                    if 'exploitation' not in taskmetadata:
                        taskmetadata['exploitation'] = 0

                    db_task = await crud.task.create_from_metadata(
                        db=db,
                        taskmetadata=taskmetadata,
                        objective=db_obj,
                        schema_id=schema_id
                    )
                    total[taskmetadata["id"]] = {
                        "type": "task",
                        "prerequisites_ids": taskmetadata["prerequisites_ids"] or [],
                        "newObj": db_task,
                    }
        db.commit()

        for key, element in total.items():
            for pre_id in element["prerequisites_ids"]:

                if element["type"] == "phase":
                    await crud.phase.add_prerequisite(db=db, phase=element["newObj"], prerequisite=total[pre_id]["newObj"], commit=False)
                if element["type"] == "objective":
                    await crud.objective.add_prerequisite(db=db, objective=element["newObj"], prerequisite=total[pre_id]["newObj"], commit=False)
                if element["type"] == "task":
                    await crud.task.add_prerequisite(db=db, task=element["newObj"], prerequisite=total[pre_id]["newObj"], commit=False)

        schema_id = coproductionschema.get("id")
        coproductionprocess.schema_used = schema_id
        db.commit()
        enriched: dict = self.enrich_log_data(coproductionprocess, {
            "action": "SET_SCHEMA",
            "coproductionprocess_id": coproductionprocess.id,
            "coproductionschema_id": schema_id
        })
        await log(enriched)
        db.refresh(coproductionprocess)
        await socket_manager.send_to_id(coproductionprocess.id, {"event": "schema_set"})
        return coproductionprocess

    async def copy(self, db: Session, coproductionprocess: CoproductionProcessCreate, user: models.User, token, label_name, from_view):

        if (label_name == ""):
            label_name = "Copy of "

        new_coproductionprocess = CoproductionProcessCreate(
            schema_used=coproductionprocess.schema_used,
            language=coproductionprocess.language,
            name=label_name + coproductionprocess.name,
            description=coproductionprocess.description,
            logotype=coproductionprocess.logotype,
            aim=coproductionprocess.aim,
            idea=coproductionprocess.idea,
            organization_desc=coproductionprocess.organization,
            challenges=coproductionprocess.challenges,
            status=coproductionprocess.status,
            cloned_from_id=coproductionprocess.id,
        )

        db_obj = await self.create(db=db, obj_in=new_coproductionprocess, creator=user, set_creator_admin=True)

        if (from_view == 'story'):
            # In case the clone is made from story the only administrator is the user.
            # The current user is set as admin of the process in the previous line.
            pass

        else:
            # In case is made from settings the administrators are the same as the process
            administrators = coproductionprocess.administrators
            for admin in administrators:
                await self.add_administrator(db=db, db_obj=db_obj, user=admin, notifyAfterAdded=False)

        #print("STARTING TREEITEMS")
        phases_temp = coproductionprocess.children.copy()
        phases = []
        indexes = []

        for id, phase in enumerate(phases_temp):
            if not len(phase.prerequisites_ids):
               # if not phase.is_disabled:
                phases.append(phase)
                indexes.append(str(phase.id))
                phases_temp.pop(id)

        while phases_temp:
            for id, phase in enumerate(phases_temp):
                if check_prerequistes(phase.prerequisites_ids, indexes):
                    # if not phase.is_disabled:
                    phases.append(phase)
                    indexes.append(str(phase.id))
                    phases_temp.pop(id)

        #  Create a dict with the old ids and the new ids
        ids_dict = {}
        for phase in phases:
            tmp_phase, phase_id_updates = await crud.phase.copy(db=db, obj_in=phase, coproductionprocess=db_obj, extra=ids_dict)
            ids_dict['Phase_'+str(phase.id)] = tmp_phase.id
            ids_dict.update(phase_id_updates)
        #print("TREEITEMS COPIED")

        #print("STARTING ASSET")
        #print(from_view)
        # Copy the assets of the project
        assets = await self.get_assets(db, coproductionprocess, user,token=token)
        contador_assets = 0
        for asset in assets:
            #print('El numero de assets es:')
            contador_assets = contador_assets+1
            #print(str(contador_assets)+'/'+str(len(assets)))

            task = await crud.task.get(db, ids_dict['Task_' + str(asset.task_id)])

            if (from_view == 'for_publication'):
                # In the case of publcation in the catalogue copy of assets as readonly:
                await crud.asset.copy(db, asset, user, task, token, True)
            else:
                await crud.asset.copy(db, asset, user, task, token)
            #print('termino el copiado de '+str(asset.id))
            #print('')

        #print("ASSETS COPIED")

        #print("STARTING PERMISSIONS")
        # Copy the permissions of the project (THE NEW CREATOR IS THE CREATOR OF THE COPY)
        if (from_view == 'story'):
            # If the copy is made from the story then the dont need to create permissions
            pass
        else:
            for permission in coproductionprocess.permissions:
                treeitem = None
                if permission.treeitem:
                    treeitem = await treeitemsCrud.get(db, ids_dict[permission.treeitem.__class__.__name__ + '_' + str(permission.treeitem.id)])
                #print("New permission")
                new_permission = PermissionCreate(
                    creator_id=user.id,
                    creator=user,
                    team_id=permission.team_id,
                    team=permission.team,
                    coproductionprocess_id=db_obj.id if permission.coproductionprocess else None,
                    coproductionprocess=db_obj if permission.coproductionprocess else None,
                    treeitem_id=treeitem.id if treeitem else None,
                    treeitem=treeitem,
                    access_assets_permission=permission.access_assets_permission,
                    create_assets_permission=permission.create_assets_permission,
                    delete_assets_permission=permission.delete_assets_permission)

                await crud.permission.create(db=db, obj_in=new_permission, creator=user, notifyAfterAdded=False)

        await log({"action": "CLONE","model":"COPRODUCTIONPROCESS","object_id":db_obj.id,"cloned_from_id":db_obj.cloned_from_id,"from_view":from_view})

        return db_obj
    
    async def add_tag(self, db: Session, db_obj: CoproductionProcess, tag_id: uuid.UUID):
        if (tag := await crud.tag.get(db=db, id=tag_id)):
            if tag not in db_obj.tags:
                db_obj.tags.append(tag)
                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)
            else:
                raise HTTPException(status_code=400, detail="Tag already exists in this coproduction process")
        
        await self.log_on_update(db_obj)
        
        return db_obj

    # Override log methods

    def enrich_log_data(self, coproductionprocess, logData):
        logData["model"] = "COPRODUCTIONPROCESS"
        logData["object_id"] = coproductionprocess.id
        logData["coproductionprocess_id"] = coproductionprocess.id
        return logData

    # CRUD Permissions
    def can_create(self, user):
        return True

    def can_list(self, user):
        return True

    def check_perm(self, db: Session, user: models.User, object, perm):
        return True

    def can_read(self, db: Session, user, object):
        first = db.query(CoproductionProcess).filter(
            CoproductionProcess.id == object.id
        ).filter(
            CoproductionProcess.id == Permission.coproductionprocess_id
        ).filter(
            or_(
                Permission.user_id == user.id,
                Permission.team_id.in_(user.teams_ids)
            )
        )
        second = db.query(CoproductionProcess).filter(
            CoproductionProcess.id == object.id
        ).filter(
            CoproductionProcess.administrators.any(models.User.id.in_([user.id]))
        )
        return len(second.union(first).all()) > 0

    def can_update(self, user, object):
        return user in object.administrators

    def can_remove(self, user, object):
        return user in object.administrators


exportCrud = CRUDCoproductionProcess(CoproductionProcess, logByDefault=True)
