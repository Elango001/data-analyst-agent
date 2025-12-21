"""
Configuration API Endpoints
Handles agent and database configuration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.Configuration.config import Config
from backend.tools.cleaner_tools import c_tools
from backend.tools.visualizer_tools import v_tools
from backend.prompts.prompts import Prompts

router = APIRouter()

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


@router.post("/configure")
async def configure_agent(config_request: ConfigRequest):
    """Configure the agent with model and API key"""
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
        
        Config.visualization_config = visualizer
        
        # Validation checks
        print(f"Agent configured: {Config.cleaner_config.get_agent() is not None}")
        print(f"Tools configured: {Config.cleaner_config.get_tools() is not None}")
        print(f"Prompt configured: {Config.cleaner_config.get_prompt() is not None}")
        print(f"Agent prompt configured: {Config.cleaner_config.agent.prompt is not None}")
        print(f"Visualizer agent configured: {Config.visualization_config.get_agent() is not None}")
        print(f"Visualizer tools configured: {Config.visualization_config.get_tools() is not None}")
        print(f"Visualizer prompt configured: {Config.visualization_config.get_prompt() is not None}")

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


@router.post("/configure-db")
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
