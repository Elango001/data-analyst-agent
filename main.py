from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import pandas as pd
import io
import os
from workflow.cleaner_workflow import CleanerWorkflow
from workflow.state_management import State
from Configuration.config import Config
from tools.cleaner_tools import c_tools
from prompts.prompts import Prompts
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Data Analyst Agent",
    description="AI-powered data analysis system",
    version="1.0.0"
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Request Models
class ConfigRequest(BaseModel):
    provider: str = Field(..., description="LLM Provider (e.g., 'google')")
    model_name: str = Field(..., description="Gemini model name")
    api_key: str = Field(..., description="Google API key")


# Global state
is_configured = False

@app.get("/")
async def serve_ui():
    """Serve the UI"""
    return FileResponse(os.path.join(static_path, "index.html"))

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "online", "configured": is_configured}

@app.post("/configure")
async def configure_agent(config_request: ConfigRequest):
    """Configure the agent with model and API key"""
    global is_configured
    
    try:
        print(config_request.model_name)
        # Set LLM configuration following config_test.py pattern
        llm = Config.llm_config
        llm.set_llm(config_request.provider, config_request.model_name, config_request.api_key)
        print("Model loaded")
        print(type(llm.get_llm()))
        # Set prompt configuration
        prompt = Config.prompt_config
        prompt.set_prompt(Prompts())
        
        # Set tool configuration
        tools = Config.tool_config
        tools.set_cleaner_tools(c_tools)
        print(f"Cleaner tools set: {tools.get_cleaner_tools() is not None}")
        
        # Initialize data configuration
        data = Config.data_config
        data.set_df()
        
        # Configure cleaner with proper initialization order
        cleaner = Config.cleaner_config
        cleaner.set_prompt(prompt.get_prompt())
        print(f"Tools to be set: {tools.get_cleaner_tools() is not None}")
        cleaner.set_tools(tools.get_cleaner_tools())
        cleaner.set_agent(llm.get_llm())
        
        # Update Config with configured cleaner
        Config.cleaner_config = cleaner
        
        # Validation checks
        print(f"Agent configured: {Config.cleaner_config.get_agent() is not None}")
        print(f"Tools configured: {Config.cleaner_config.get_tools() is not None}")
        print(f"Prompt configured: {Config.cleaner_config.get_prompt() is not None}")
        print(f"Agent prompt configured: {Config.cleaner_config.agent.prompt is not None}")

        is_configured = True
        
        return {
            "status": "success",
            "message": f"Configured with {config_request.model_name}"
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Configuration error: {error_msg}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")
        
@app.post("/clean")
async def clean_data():
    """Start data cleaning process"""
    if not is_configured:
        raise HTTPException(status_code=400, detail="Please configure first")
    
    if Config.data_config.get_df() is None:
        raise HTTPException(status_code=400, detail="Please upload a CSV file first")
    
    try:
        # Initialize cleaner workflow
        print("Config.cleaner_config:", Config.cleaner_config is not None)
        cleaner_workflow = CleanerWorkflow(Config.cleaner_config)
        cleaner_workflow.nodes_generator()
        
        # Get data configuration
        data = Config.data_config
        
        # Initialize state following config_test.py pattern
        initial_state = {
            "cleaner": {"count": 0, "cleaner_response": []},
            "analyser": {"count": 0, "analyzer_response": []},
            "visualizer": {"count": 0, "visualizer_response": []},
            "cur_agent": "cleaner",
            "tool_call": None,
            "success_tools": [],
            "failed_tools": [],
            "tool_result": [],
            "df_info": data.profile_data(),
        }
        
        result = cleaner_workflow.invoke(initial_state)
        
        return {
            "status": "success",
            "message": "Data cleaning completed",
            "result": str(result)  # Convert result to string for JSON serialization
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleaning failed: {str(e)}")

@app.post("/upload")
async def upload_data(file: UploadFile = File(...)):
    """Upload CSV data file"""
    if not is_configured:
        raise HTTPException(status_code=400, detail="Please configure first")
    
    try:
        contents = await file.read()
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files supported")
        
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Set dataframe following config_test.py pattern
        data = Config.data_config
        data.set_df(df)
        
        return {
            "status": "success",
            "message": f"Uploaded {file.filename}",
            "rows": len(df),
            "columns": len(df.columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload
        reload_dirs=["."]  # Watch current directory for changes
    )
