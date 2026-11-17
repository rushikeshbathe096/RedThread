from fastapi import APIRouter

from backend.app.modules.auth.router import router as auth_router
from backend.app.modules.organizations.router import router as organizations_router

api_router = APIRouter()

# Mounted feature routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])

# Remaining routers will be mounted in their respective phases:
# api_router.include_router(cases.router, prefix="/cases", tags=["Cases"])
# api_router.include_router(documents.router, prefix="/cases/{case_id}/documents", tags=["Documents"])
# api_router.include_router(entities.router, prefix="/entities", tags=["Entities"])
# api_router.include_router(claims.router, prefix="/claims", tags=["Claims"])
# api_router.include_router(recall.router, prefix="/cases/{case_id}/recall", tags=["Recall"])
# api_router.include_router(reports.router, prefix="/cases/{case_id}/reports", tags=["Reports"])


@api_router.get("/ping", tags=["System"])
async def ping():
    """Lightweight ping endpoint for load balancer health probes."""
    return {"status": "ok", "service": "redthread-api"}
