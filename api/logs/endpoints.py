"""
Logs and Tracking API Endpoints
Handles tool execution logs and deleted data tracking
"""
from fastapi import APIRouter
import pandas as pd
import numpy as np
from backend.Configuration.config import Config


router = APIRouter()


@router.get("/tool-logs")
async def get_tool_logs():
    """Get all tool execution logs"""
    try:
        handler = Config.db_config.get_deleted_data_handler()
        if not handler:
            # Return empty logs instead of error if DB not configured
            return {
                "status": "warning",
                "logs": [],
                "message": "Database not configured. Configure database first to see logs."
            }
        
        logs = handler.get_all_tool_logs()
        
        # Add cleaner response to each log
        for log in logs:
            cleaner_response = handler.get_cleaner_response(log['id'])
            log['cleaner_response'] = cleaner_response
        
        return {
            "status": "success",
            "logs": logs,
            "message": f"Found {len(logs)} logs"
        }
    except Exception as e:
        print(f"Error fetching logs: {str(e)}")
        # Return empty logs with error message instead of 500 error
        return {
            "status": "error",
            "logs": [],
            "message": f"Error loading logs: {str(e)}"
        }


@router.get("/deleted-data/{tool_id}")
async def get_deleted_data(tool_id: int):
    """Get deleted data for a specific tool execution"""
    try:
        handler = Config.db_config.get_deleted_data_handler()
        if not handler:
            return {
                "status": "error",
                "data": None,
                "message": "Database not configured"
            }
        
        deleted_data = handler.get_deleted_data(tool_id)
        
        if deleted_data is None:
            return {
                "status": "success",
                "data": None,
                "message": "No deleted data found"
            }
        
        # Replace NaN and inf values with None before converting to dict
        deleted_data = deleted_data.replace([np.inf, -np.inf], np.nan)
        deleted_data = deleted_data.where(pd.notna(deleted_data), None)
        
        # Convert DataFrame to records
        data_records = deleted_data.to_dict('records')
        
        return {
            "status": "success",
            "data": data_records,
            "count": len(data_records)
        }
    except Exception as e:
        print(f"Error fetching deleted data: {str(e)}")
        return {
            "status": "error",
            "data": None,
            "message": str(e)
        }
