"""
Cleaning Workflow API Endpoints
Handles data cleaning workflow
"""
from fastapi import APIRouter, HTTPException
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime
from sse_starlette.sse import EventSourceResponse
from backend.workflow.cleaner_workflow import CleanerWorkflow
from backend.Configuration.config import Config


router = APIRouter()

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


# Global state for cleaning workflow
cleaning_workflow_state = {
    "is_active": False,
    "waiting_for_user": False,
    "workflow": None,
    "current_state": None,
    "generator": None
}


@router.get("/clean")
async def clean_data():
    """Start data cleaning process"""
    global cleaning_workflow_state
    
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


@router.post("/continue-cleaning")
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
