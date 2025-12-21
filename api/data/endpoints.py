"""
Data Management API Endpoints
Handles data upload and preview
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
import pandas as pd
import io
from backend.Configuration.config import Config

router = APIRouter()


@router.post("/upload")
async def upload_data(file: UploadFile = File(...)):
    """Upload CSV data file"""
    try:
        contents = await file.read()
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files supported")
        
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Set dataframe following config_test.py pattern
        data = Config.data_config
        data.set_df(df)
        
        # Get preview of first 20 rows
        preview_df = df.head(20)
        data_preview = preview_df.to_dict('records')
        
        return {
            "status": "success",
            "message": f"Uploaded {file.filename}",
            "rows": len(df),
            "columns": len(df.columns),
            "preview": data_preview
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-preview")
async def get_data_preview():
    """Get current data preview"""
    try:
        df = Config.data_config.get_df()
        
        if df is None:
            return {
                "status": "success",
                "has_data": False,
                "preview": None,
                "rows": 0,
                "columns": 0
            }
        
        # Get preview of first 20 rows
        preview_df = df.head(20)
        data_preview = preview_df.to_dict('records')
        
        return {
            "status": "success",
            "has_data": True,
            "preview": data_preview,
            "rows": len(df),
            "columns": len(df.columns)
        }
    except Exception as e:
        return {
            "status": "error",
            "has_data": False,
            "preview": None,
            "message": str(e)
        }
