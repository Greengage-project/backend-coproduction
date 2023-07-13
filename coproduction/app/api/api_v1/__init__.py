from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from app.api.api_v1 import (
    assets,
    coproductionprocesses,
    objectives,
    phases,
    tasks,
    teams,
    users,
    permissions,
    organizations,
    notifications,
    usernotifications,
    participationrequests,
    coproductionprocessnotifications,
    stories,
    utils,
    games,
    recomenders,
    tags,
    ratings,
    keywords,
    claims,
    assignments
)

api_router = APIRouter()

api_router.include_router(coproductionprocesses.router,
                          prefix="/coproductionprocesses", tags=["coproductionprocesses"])
api_router.include_router(phases.router,
                          prefix="/phases", tags=["tree"])
api_router.include_router(objectives.router,
                          prefix="/objectives", tags=["tree"])
api_router.include_router(tasks.router,
                          prefix="/tasks", tags=["tree"])
api_router.include_router(assets.router,
                          prefix="/assets", tags=["tree"])
api_router.include_router(teams.router,
                          prefix="/teams", tags=["teammanagement"])
api_router.include_router(permissions.router,
                          prefix="/permissions", tags=["teammanagement"])
api_router.include_router(users.router,
                          prefix="/users", tags=["teammanagement"])
api_router.include_router(organizations.router,
                          prefix="/organizations", tags=["teammanagement"])
api_router.include_router(notifications.router,
                          prefix="/notifications", tags=["notification"])
api_router.include_router(usernotifications.router,
                          prefix="/usernotifications", tags=["usernotification"])       
api_router.include_router(participationrequests.router,
                          prefix="/participationrequests", tags=["participationrequest"])  
api_router.include_router(claims.router,
                          prefix="/claims", tags=["claim"])      
api_router.include_router(assignments.router,
                          prefix="/assignments", tags=["assignment"])  
api_router.include_router(coproductionprocessnotifications.router,
                          prefix="/coproductionprocessnotifications", tags=["coproductionprocessnotification"])   
api_router.include_router(stories.router,
                          prefix="/stories", tags=["Stories"])    
api_router.include_router(recomenders.router,
                            prefix="/recomenders", tags=["Recomenders"])   
api_router.include_router(ratings.router,
                            prefix="/ratings", tags=["Ratings"])             
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(keywords.router, prefix="/keywords", tags=["keywords"])

@api_router.get("/")
async def main():
    return RedirectResponse(url="/api/v1/coproductionprocesses")
