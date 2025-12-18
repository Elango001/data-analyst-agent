from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import io
import os
import asyncio
from backend.workflow.cleaner_workflow import CleanerWorkflow
from backend.Configuration.config import Config
from backend.tools.cleaner_tools import c_tools
from backend.prompts.prompts import Prompts
from sse_starlette.sse import EventSourceResponse
import json
from datetime import datetime

# Custom JSON encoder to handle pandas/numpy types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)

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

# Request Models
class ConfigRequest(BaseModel):
    provider: str = Field(..., description="LLM Provider (e.g., 'google')")
    model_name: str = Field(..., description="Gemini model name")
    api_key: str = Field(..., description="Google API key")

class DBConfigRequest(BaseModel):
    host: str = Field(default="localhost")
    database: str = Field(default="preprocessing_logs")
    user: str = Field(default="postgres")
    password: str = Field(...)
    port: int = Field(default=5432)
    csv_path: str = Field(default="deleted_data.csv")


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

@app.post("/configure-db")
async def configure_database(db_config: DBConfigRequest):
    """Configure database for deleted data tracking"""
    try:
        Config.db_config.set_db_config(
            host=db_config.host,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
            port=db_config.port,
            csv_path=db_config.csv_path
        )
        
        return {
            "status": "success",
            "message": "Database configured successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB configuration failed: {str(e)}")

@app.get("/tool-logs")
async def get_tool_logs():
    """Get all tool execution logs"""
    try:
        handler = Config.db_config.get_deleted_data_handler()
        if not handler:
            raise HTTPException(status_code=400, detail="Database not configured")
        
        logs = handler.get_all_tool_logs()
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/deleted-data/{tool_id}")
async def get_deleted_data(tool_id: int):
    """Get deleted data for a specific tool execution"""
    try:
        handler = Config.db_config.get_deleted_data_handler()
        if not handler:
            raise HTTPException(status_code=400, detail="Database not configured")
        
        deleted_data = handler.get_deleted_data(tool_id)
        
        if deleted_data is None:
            return {"status": "success", "data": None, "message": "No deleted data found"}
        
        # Convert DataFrame to records
        data_records = deleted_data.to_dict('records')
        
        return {
            "status": "success",
            "data": data_records,
            "count": len(data_records)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/clean")
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
        async def event_generator():
            # Run the synchronous generator in an executor to allow interleaving
            loop = asyncio.get_event_loop()
            
            for event in cleaner_workflow.invoke(initial_state):
                node = list(event.keys())[0]
                state = event[node]
                
                # Log each event being sent
                print(f"Streaming event - Node: {node}")
                
                # Convert state to dict if it has model_dump method
                state_dict = state.model_dump() if hasattr(state, "model_dump") else state
                
                # Extract only necessary data for chat display
                chat_data = {
                    "node": node,
                }
                
                # For cleaner_node, send last message and tool calls
                if node == "cleaner_node":
                    cleaner_responses = state_dict.get("cleaner", {}).get("cleaner_response", [])
                    chat_data["last_message"] = cleaner_responses[-1] if cleaner_responses else None
                    chat_data["tool_call"] = state_dict.get("tool_call")
                    
                    # Get current dataframe from data config
                    current_df = data.get_df()
                    data_preview = None
                    if current_df is not None:
                        # Convert first 20 rows to list of dicts
                        preview_df = current_df.head(20)
                        data_preview = preview_df.to_dict('records')
                    
                    # Also include summary data for results panel
                    chat_data["summary"] = {
                        "count": state_dict.get("cleaner", {}).get("count", 0),
                        "success_tools": state_dict.get("success_tools", []),
                        "failed_tools": state_dict.get("failed_tools", []),
                        "tool_result": state_dict.get("tool_result", []),
                        "data_preview": data_preview  # Add first 20 rows
                    }
                else:
                    # For other nodes (like tool_executor), just send basic info
                    chat_data["info"] = f"Processing {node}"

                # Yield the optimized event
                yield {
                    "event": "message",
                    "data": json.dumps(chat_data, cls=CustomJSONEncoder)
                }
                
                # Yield control to event loop to flush the response
                await asyncio.sleep(0.01)  # Small delay to ensure flushing
                print(f"Event sent - Node: {node}")

        return EventSourceResponse(event_generator())
    
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
