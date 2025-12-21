"""
Version Management API Endpoints
Handles data versioning, saving, reverting, and deletion
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from backend.Configuration.config import Config


router = APIRouter()

# Request Models
class SaveVersionRequest(BaseModel):
    tool_details: str = Field(..., description="Description of the version/tool that created it")

class RevertVersionRequest(BaseModel):
    timestamp: str = Field(..., description="Timestamp of the version to revert to (ISO format)")


@router.post("/save-version")
async def save_version(request: SaveVersionRequest):
    """Save current data as a version"""
    try:
        print(f"Save version called with tool_details: {request.tool_details}")
        
        # Check if data is available
        current_df = Config.data_config.get_df()
        print(f"Current data available: {current_df is not None}")
        if current_df is None:
            raise HTTPException(status_code=400, detail="No data available to version")
        
        # Check if version handler is configured
        version_handler = Config.db_config.get_version_handler()
        print(f"Version handler configured: {version_handler is not None}")
        if version_handler is None:
            raise HTTPException(status_code=400, detail="Database not configured. Please configure database first.")
        
        # Import versioner
        from backend.db.revert import Versioner
        
        # Create versioner and save version
        versioner = Versioner(Config)
        timestamp = versioner.save_version(request.tool_details)
        print(f"Version saved with timestamp: {timestamp}")
        
        return {
            "status": "success",
            "message": "Version saved successfully",
            "timestamp": timestamp.isoformat()
        }
    except ValueError as e:
        print(f"ValueError in save_version: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception in save_version: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save version: {str(e)}")


@router.get("/versions")
async def get_versions():
    """Get all saved data versions"""
    try:
        handler = Config.db_config.get_version_handler()
        if not handler:
            return {
                "status": "warning",
                "versions": [],
                "message": "Database not configured. Configure database first to see versions."
            }
        
        versions = handler.get_all_versions()
        
        # Convert timestamps to ISO format for JSON serialization
        for version in versions:
            if 'timestamp' in version and version['timestamp']:
                version['timestamp'] = version['timestamp'].isoformat()
        
        return {
            "status": "success",
            "versions": versions,
            "message": f"Found {len(versions)} version(s)"
        }
    except Exception as e:
        print(f"Error fetching versions: {str(e)}")
        return {
            "status": "error",
            "versions": [],
            "message": f"Error loading versions: {str(e)}"
        }


@router.post("/revert-version")
async def revert_version(request: RevertVersionRequest):
    """Revert to a specific data version"""
    try:
        from backend.db.revert import Revert
        from datetime import datetime
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(request.timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Create revert instance and revert
        revert = Revert(Config)
        success = revert.revert_to_version(timestamp)
        
        if success:
            # Get preview of reverted data
            current_df = Config.data_config.get_df()
            data_preview = None
            if current_df is not None:
                preview_df = current_df.head(20)
                data_preview = preview_df.to_dict('records')
            
            return {
                "status": "success",
                "message": "Successfully reverted to selected version",
                "rows": len(current_df) if current_df is not None else 0,
                "columns": len(current_df.columns) if current_df is not None else 0,
                "preview": data_preview
            }
        else:
            raise HTTPException(status_code=500, detail="Revert operation failed")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revert: {str(e)}")


@router.delete("/delete-version")
async def delete_version(request: RevertVersionRequest):
    """Delete a specific data version from both database and CSV file"""
    try:
        from datetime import datetime
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(request.timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Get version handler
        version_handler = Config.db_config.get_version_handler()
        if not version_handler:
            raise HTTPException(status_code=500, detail="Version handler not available")
        
        # Delete the version
        success = version_handler.delete_data_version(timestamp)
        
        if success:
            return {
                "status": "success",
                "message": "Successfully deleted version",
                "timestamp": request.timestamp
            }
        else:
            raise HTTPException(status_code=404, detail="Version not found or could not be deleted")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete version: {str(e)}")
