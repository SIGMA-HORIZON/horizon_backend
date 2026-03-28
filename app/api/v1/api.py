from fastapi import APIRouter
from app.api.v1.endpoints import placeholder

api_router = APIRouter()

# Include resource routers here
# api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(placeholder.router, prefix="/placeholder", tags=["placeholder"])
