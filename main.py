from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from backend.Configuration.config import Config
from api.router import api_router

# Initialize FastAPI app
app = FastAPI(
    title="Data Analyst Agent",
    description="AI-powered data analysis system",
    version="1.0.0"
)

# Add CORS middleware for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include API routes
app.include_router(api_router)


@app.get("/")
async def serve_ui():
    """Serve the UI"""
    return FileResponse(os.path.join(static_path, "index.html"))


@app.get("/health")
async def health_check():
    """Health check"""
    has_data = Config.data_config.get_df() is not None
    data_info = None
    
    if has_data:
        df = Config.data_config.get_df()
        data_info = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        }
    
    db_handler = Config.db_config.get_deleted_data_handler()
    version_handler = Config.db_config.get_version_handler()
    
    return {
        "status": "online", 
        "configured": True,
        "has_data": has_data,
        "data_info": data_info,
        "db_configured": db_handler is not None,
        "version_handler_configured": version_handler is not None,
        "db_handler_type": str(type(db_handler).__name__) if db_handler else None,
        "version_handler_type": str(type(version_handler).__name__) if version_handler else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload
        reload_dirs=["."]  # Watch current directory for changes
    )
