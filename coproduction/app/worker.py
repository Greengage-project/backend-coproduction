from uuid import UUID
import requests
from app.celery_app import celery_app
from app.general.db.session import SessionLocal
from app.models import (
    Permission,
    TreeItem,
    Task,
    User,
    Team,
    CoproductionProcess,
    user_team_association_table
)
from app.crud import permission as permissionsCrud


@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task
def sync_asset_users(treeitem_id: UUID) -> str:
    db = SessionLocal()
    try:

        treeitem : TreeItem = db.query(TreeItem).filter(
            TreeItem.id == treeitem_id
        ).first()

        print("treeitem", treeitem)
        
        if treeitem.type == "objective":
            tasks = treeitem.children
        elif treeitem.type == "phase":
            tasks = treeitem.tasks
        else:
            tasks = [treeitem]
        
        print("tasks", tasks)

        task: Task
        for task in tasks:
            data = []

            res = db.query(
                User
            ).join(
                user_team_association_table
            ).filter(
                Permission.coproductionprocess_id == task.coproductionprocess.id,
                Permission.treeitem_id.in_(task.path_ids),
                Permission.team_id == Team.id
            )

            res2 = db.query(
                User
            ).join(
                CoproductionProcess.administrators
            )

            users = res.union(res2).all()
            print("users", users)
            
            for user in users:
                toAdd = permissionsCrud.get_dict_for_treeitem(db=db, treeitem=task, user=user)
                toAdd["email"] = user.email
                toAdd["id"] = user.id
                data.append(toAdd)
                             
            for asset in task.assets:
                URL = asset.internal_link + "/sync_users"
                print(URL, data)
                requests.post(URL, json=data)

    except Exception as e:
        db.close()
        raise e
