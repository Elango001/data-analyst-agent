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
from backend.workflow.visualizer_workflow import VisualizerWorkflow
from backend.Configuration.config import Config
from backend.tools.cleaner_tools import c_tools
from backend.tools.visualizer_tools import v_tools
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
            # Handle NaN and inf values
            if np.isnan(obj) or np.isinf(obj):
                return None
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

class SaveVersionRequest(BaseModel):
    tool_details: str = Field(..., description="Description of the version/tool that created it")

class RevertVersionRequest(BaseModel):
    timestamp: str = Field(..., description="Timestamp of the version to revert to (ISO format)")


# Global state
is_configured = False
cleaning_workflow_state = {
    "is_active": False,
    "waiting_for_user": False,
    "workflow": None,
    "current_state": None,
    "generator": None
}

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
        "configured": is_configured,
        "has_data": has_data,
        "data_info": data_info,
        "db_configured": db_handler is not None,
        "version_handler_configured": version_handler is not None,
        "db_handler_type": str(type(db_handler).__name__) if db_handler else None,
        "version_handler_type": str(type(version_handler).__name__) if version_handler else None
    }

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
        tools.set_visualizer_tools(v_tools)
        print(f"Cleaner tools set: {tools.get_cleaner_tools() is not None}")
        print(f"Visualizer tools set: {tools.get_visualizer_tools() is not None}")
    
        
        # Configure cleaner with proper initialization order
        cleaner = Config.cleaner_config
        cleaner.set_prompt(prompt.get_prompt())
        print(f"Tools to be set: {tools.get_cleaner_tools() is not None}")
        cleaner.set_tools(tools.get_cleaner_tools())
        cleaner.set_agent(llm.get_llm())
        
        # Update Config with configured cleaner
        Config.cleaner_config = cleaner
        
        # Configure visualizer with proper initialization order
        visualizer = Config.visualization_config
        visualizer.set_prompt(prompt.get_prompt())
        visualizer.set_tools(tools.get_visualizer_tools())
        visualizer.set_agent(llm.get_llm())
        
        # Update Config with configured visualizer
        Config.visualization_config = visualizer
        
        # Validation checks
        print(f"Agent configured: {Config.cleaner_config.get_agent() is not None}")
        print(f"Tools configured: {Config.cleaner_config.get_tools() is not None}")
        print(f"Prompt configured: {Config.cleaner_config.get_prompt() is not None}")
        print(f"Agent prompt configured: {Config.cleaner_config.agent.prompt is not None}")
        print(f"Visualizer agent configured: {Config.visualization_config.get_agent() is not None}")
        print(f"Visualizer tools configured: {Config.visualization_config.get_tools() is not None}")
        print(f"Visualizer prompt configured: {Config.visualization_config.get_prompt() is not None}")

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
            csv_path=db_config.csv_path,
            version_dir="data_versions"  # Add version directory
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

@app.get("/deleted-data/{tool_id}")
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
        
@app.get("/clean")
async def clean_data():
    """Start data cleaning process"""
    global cleaning_workflow_state
    
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
        
        # Store workflow in global state
        cleaning_workflow_state["workflow"] = cleaner_workflow
        cleaning_workflow_state["generator"] = cleaner_workflow.invoke(initial_state)
        cleaning_workflow_state["is_active"] = True
        cleaning_workflow_state["waiting_for_user"] = False
        
        async def event_generator():
            # Run the synchronous generator in an executor to allow interleaving
            loop = asyncio.get_event_loop()
            
            for event in cleaning_workflow_state["generator"]:
                node = list(event.keys())[0]
                state = event[node]
                
                # Log each event being sent
                print(f"Streaming event - Node: {node}")
                
                # Convert state to dict if it has model_dump method
                state_dict = state.model_dump() if hasattr(state, "model_dump") else state
                
                # Store current state
                cleaning_workflow_state["current_state"] = state_dict
                
                # Extract only necessary data for chat display
                chat_data = {
                    "node": node,
                }
                
                # For cleaner_node, send last message and tool calls
                if node == "cleaner_node":
                    cleaner_responses = state_dict.get("cleaner", {}).get("cleaner_response", [])
                    chat_data["last_message"] = cleaner_responses[-1] if cleaner_responses else None
                    chat_data["tool_call"] = state_dict.get("tool_call")
                    
                    # Save cleaner response to database if we have tool results
                    tool_results = state_dict.get("tool_result", [])
                    if tool_results and cleaner_responses:
                        # Get the last cleaner response and the corresponding tool_id
                        last_response = cleaner_responses[-1]
                        # Each tool result should have a tool_id
                        for result in tool_results:
                            if result.get("success") and "tool_id" in result:
                                handler = Config.db_config.get_deleted_data_handler()
                                if handler:
                                    handler.save_cleaner_response(result["tool_id"], last_response)
                    
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
                    
                    # PAUSE HERE - Wait for user action
                    if cleaner_responses:  # If agent has responded
                        chat_data["waiting_for_user"] = True
                        cleaning_workflow_state["waiting_for_user"] = True
                        
                        # Send the response with waiting flag
                        yield {
                            "event": "message",
                            "data": json.dumps(chat_data, cls=CustomJSONEncoder)
                        }
                        
                        # Send a special "waiting" event
                        yield {
                            "event": "waiting",
                            "data": json.dumps({
                                "message": "Waiting for user action (Save Version or Continue)",
                                "can_save": True,
                                "can_continue": True
                            }, cls=CustomJSONEncoder)
                        }
                        
                        # Exit the generator - user must call /continue-cleaning
                        break
                else:
                    # For other nodes (like tool_executor), just send basic info
                    chat_data["info"] = f"Processing {node}"

                # Yield the optimized event (only if not waiting)
                if not chat_data.get("waiting_for_user"):
                    yield {
                        "event": "message",
                        "data": json.dumps(chat_data, cls=CustomJSONEncoder)
                    }
                
                # Yield control to event loop to flush the response
                await asyncio.sleep(0.01)  # Small delay to ensure flushing
                print(f"Event sent - Node: {node}")
            
            # Workflow completed
            if not cleaning_workflow_state["waiting_for_user"]:
                cleaning_workflow_state["is_active"] = False
                yield {
                    "event": "complete",
                    "data": json.dumps({"message": "Cleaning workflow completed"}, cls=CustomJSONEncoder)
                }

        return EventSourceResponse(event_generator())
    
    except Exception as e:
        cleaning_workflow_state["is_active"] = False
        raise HTTPException(status_code=500, detail=f"Cleaning failed: {str(e)}")

@app.post("/continue-cleaning")
async def continue_cleaning():
    """Continue the paused cleaning workflow"""
    global cleaning_workflow_state
    
    if not cleaning_workflow_state["is_active"]:
        raise HTTPException(status_code=400, detail="No active cleaning workflow")
    
    if not cleaning_workflow_state["waiting_for_user"]:
        raise HTTPException(status_code=400, detail="Workflow is not waiting for user action")
    
    try:
        # Reset waiting flag
        cleaning_workflow_state["waiting_for_user"] = False
        
        # Get data configuration
        data = Config.data_config
        
        async def event_generator():
            # Continue from where we left off
            for event in cleaning_workflow_state["generator"]:
                node = list(event.keys())[0]
                state = event[node]
                
                print(f"Streaming event - Node: {node}")
                
                # Convert state to dict if it has model_dump method
                state_dict = state.model_dump() if hasattr(state, "model_dump") else state
                
                # Store current state
                cleaning_workflow_state["current_state"] = state_dict
                
                # Extract only necessary data for chat display
                chat_data = {
                    "node": node,
                }
                
                # For cleaner_node, send last message and tool calls
                if node == "cleaner_node":
                    cleaner_responses = state_dict.get("cleaner", {}).get("cleaner_response", [])
                    chat_data["last_message"] = cleaner_responses[-1] if cleaner_responses else None
                    chat_data["tool_call"] = state_dict.get("tool_call")
                    
                    # Save cleaner response to database if we have tool results
                    tool_results = state_dict.get("tool_result", [])
                    if tool_results and cleaner_responses:
                        # Get the last cleaner response and the corresponding tool_id
                        last_response = cleaner_responses[-1]
                        # Each tool result should have a tool_id
                        for result in tool_results:
                            if result.get("success") and "tool_id" in result:
                                handler = Config.db_config.get_deleted_data_handler()
                                if handler:
                                    handler.save_cleaner_response(result["tool_id"], last_response)
                    
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
                        "data_preview": data_preview
                    }
                    
                    # PAUSE AGAIN - Wait for user action
                    if cleaner_responses:  # If agent has responded
                        chat_data["waiting_for_user"] = True
                        cleaning_workflow_state["waiting_for_user"] = True
                        
                        # Send the response with waiting flag
                        yield {
                            "event": "message",
                            "data": json.dumps(chat_data, cls=CustomJSONEncoder)
                        }
                        
                        # Send a special "waiting" event
                        yield {
                            "event": "waiting",
                            "data": json.dumps({
                                "message": "Waiting for user action (Save Version or Continue)",
                                "can_save": True,
                                "can_continue": True
                            }, cls=CustomJSONEncoder)
                        }
                        
                        # Exit the generator - user must call /continue-cleaning again
                        break
                else:
                    # For other nodes (like tool_executor), just send basic info
                    chat_data["info"] = f"Processing {node}"

                # Yield the optimized event (only if not waiting)
                if not chat_data.get("waiting_for_user"):
                    yield {
                        "event": "message",
                        "data": json.dumps(chat_data, cls=CustomJSONEncoder)
                    }
                
                # Yield control to event loop to flush the response
                await asyncio.sleep(0.01)
                print(f"Event sent - Node: {node}")
            
            # Workflow completed
            if not cleaning_workflow_state["waiting_for_user"]:
                cleaning_workflow_state["is_active"] = False
                yield {
                    "event": "complete",
                    "data": json.dumps({"message": "Cleaning workflow completed"}, cls=CustomJSONEncoder)
                }

        return EventSourceResponse(event_generator())
    
    except Exception as e:
        cleaning_workflow_state["is_active"] = False
        raise HTTPException(status_code=500, detail=f"Continue cleaning failed: {str(e)}")

@app.get("/visualization")
async def visualize_data():
    """Start data visualization process"""
    if not is_configured:
        raise HTTPException(status_code=400, detail="Please configure first")
    
    if Config.data_config.get_df() is None:
        raise HTTPException(status_code=400, detail="Please upload a CSV file first")
    
    try:
        # Initialize visualizer workflow
        print("Config.visualization_config:", Config.visualization_config is not None)
        visualizer_workflow = VisualizerWorkflow(Config.visualization_config)
        visualizer_workflow.nodes_generator()
        
        # Get data configuration
        data = Config.data_config
        
        # Initialize state
        initial_state = {
            "cleaner": {"count": 0, "cleaner_response": []},
            "analyser": {"count": 0, "analyzer_response": []},
            "visualizer": {"count": 0, "visualizer_response": []},
            "cur_agent": "visualizer",
            "tool_call": None,
            "success_tools": [],
            "failed_tools": [],
            "tool_result": [],
            "df_info": data.profile_data(),
        }
        
        async def event_generator():
            for event in visualizer_workflow.invoke(initial_state):
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
                
                # For visualizer_node, send last message and visualizations
                if node == "visualizer_node":
                    visualizer_responses = state_dict.get("visualizer", {}).get("visualizer_response", [])
                    chat_data["last_message"] = visualizer_responses[-1] if visualizer_responses else None
                    chat_data["tool_call"] = state_dict.get("tool_call")
                    
                    # Save visualizer response to database if we have tool results
                    tool_results = state_dict.get("tool_result", [])
                    if tool_results and visualizer_responses:
                        # Get the last visualizer response
                        last_response = visualizer_responses[-1]
                        # Save response for each successful tool result
                        for result in tool_results:
                            if result.get("success") and "tool_id" in result:
                                handler = Config.db_config.get_deleted_data_handler()
                                if handler:
                                    # Save the visualizer response (explanation)
                                    handler.save_cleaner_response(result["tool_id"], last_response)
                    
                    # Extract visualizations from tool results
                    visualizations = []
                    if tool_results:
                        for result in tool_results:
                            if result.get("success") and "visualization" in result:
                                visualizations.append({
                                    "type": result.get("type", "unknown"),
                                    "data": result.get("visualization"),
                                    "title": result.get("title", "Visualization")
                                })
                    
                    # Also include summary data for results panel
                    chat_data["summary"] = {
                        "count": state_dict.get("visualizer", {}).get("count", 0),
                        "success_tools": state_dict.get("success_tools", []),
                        "failed_tools": state_dict.get("failed_tools", []),
                        "tool_result": state_dict.get("tool_result", []),
                        "visualizations": visualizations
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
            
            # Workflow completed
            yield {
                "event": "complete",
                "data": json.dumps({"message": "Visualization workflow completed"}, cls=CustomJSONEncoder)
            }

        return EventSourceResponse(event_generator())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")

@app.get("/data-preview")
async def get_data_preview():
    """Get preview of current data"""
    try:
        df = Config.data_config.get_df()
        if df is None:
            return {
                "status": "warning",
                "message": "No data available",
                "preview": None
            }
        
        preview_df = df.head(20)
        data_preview = preview_df.to_dict('records')
        
        return {
            "status": "success",
            "rows": len(df),
            "columns": len(df.columns),
            "preview": data_preview
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "preview": None
        }

@app.get("/data-preview")
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

@app.post("/save-version")
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

@app.get("/versions")
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

@app.post("/revert-version")
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

@app.delete("/delete-version")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload
        reload_dirs=["."]  # Watch current directory for changes
    )
