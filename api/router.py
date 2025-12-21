"""
Main API Router
Combines all API endpoint routers
"""
from fastapi import APIRouter
from api.configure.endpoints import router as configure_router
from api.data.endpoints import router as data_router
from api.cleaning.endpoints import router as cleaning_router
from api.visualization.endpoints import router as visualization_router
from api.logs.endpoints import router as logs_router
from api.versions.endpoints import router as versions_router


# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(configure_router, tags=["Configuration"])
api_router.include_router(data_router, tags=["Data Management"])
api_router.include_router(cleaning_router, tags=["Cleaning Workflow"])
api_router.include_router(visualization_router, tags=["Visualization"])
api_router.include_router(logs_router, tags=["Logs & Tracking"])
api_router.include_router(versions_router, tags=["Version Management"])
