"""
Visualization Workflow API Endpoints
Handles data visualization workflow
"""
from fastapi import APIRouter, HTTPException
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime
from sse_starlette.sse import EventSourceResponse
from backend.workflow.visualizer_workflow import VisualizerWorkflow
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


@router.get("/visualization")
async def visualize_data():
    """Start data visualization process"""
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
