from agents.cleaner_agent import CleanerAgent
from agents.analyser_agent import AnalyserAgent
from agents.visualizer_agent import VisualizerAgent
from agents.Agent import BaseAgent
from agents.agent_utils import ChatGemini
import numpy as np
import pandas as pd
from tools.tool_main import AllTools
from typing import Optional, List, Any, Dict

class Cleaner_config:
    tools: Optional[AllTools] = None
    agent: Optional[CleanerAgent] = None
    prompt: Optional[Any] = None
    
    def set_agent(self, LLM: BaseAgent) -> None:
        self.agent = CleanerAgent(LLM, self.prompt)

    def set_tools(self, tools: AllTools) -> None:
        self.tools = tools
    
    def set_prompt(self, prompt: Any) -> None:
        self.prompt = prompt
    
    def get_agent(self) -> Optional[CleanerAgent]:
        return self.agent

    def get_tools(self) -> Optional[AllTools]:
        return self.tools
    
    def get_prompt(self) -> Optional[Any]:
        return self.prompt

class Analyser_config:
    tools: Optional[AllTools] = None
    agent: Optional[AnalyserAgent] = None
    prompt: Optional[Any] = None
    
    def set_agent(self, LLM: BaseAgent) -> None:
        self.agent = AnalyserAgent(LLM, self.prompt)

    def set_tools(self, tools: AllTools) -> None:
        self.tools = tools
    
    def set_prompt(self, prompt: Any) -> None:
        self.prompt = prompt
    
    def get_agent(self) -> Optional[AnalyserAgent]:
        return self.agent
    
    def get_tools(self) -> Optional[AllTools]:
        return self.tools
    
    def get_prompt(self) -> Optional[Any]:
        return self.prompt

class Visualizer_config:
    tools: Optional[AllTools] = None
    agent: Optional[VisualizerAgent] = None
    prompt: Optional[Any] = None
    
    def set_agent(self, LLM: BaseAgent) -> None:
        self.agent = VisualizerAgent(LLM, self.prompt)

    def set_tools(self, tools: AllTools) -> None:
        self.tools = tools
    
    def set_prompt(self, prompt: Any) -> None:
        self.prompt = prompt
    
    def get_agent(self) -> Optional[VisualizerAgent]:
        return self.agent
    
    def get_tools(self) -> Optional[AllTools]:
        return self.tools
    
    def get_prompt(self) -> Optional[Any]:
        return self.prompt

class LLMConfig:
    llm: Optional[BaseAgent] = None
    provider: Optional[str] = None
    name: Optional[str] = None
    api_key: Optional[str] = None
    
    def __init__(self) -> None:
        self.llm = None
        self.provider = None
        self.name = None
        self.api_key = None

    def set_llm(self, provider: str, name: str, api_key: str) -> None:
        """Set the LLM configuration and validate it"""
        self.provider = provider
        self.name = name
        self.api_key = api_key
        # LLMFinder will raise an exception if there's an error
        # Exception will propagate up to the caller (main.py)
        # If successful, llm will be a valid BaseAgent instance
        self.llm = self.LLMFinder()
    
    def LLMFinder(self) -> BaseAgent:
        """Find and initialize the appropriate LLM based on provider"""
        if self.provider == "google":
            agent = ChatGemini().set_agent(self.name, self.api_key)
            return agent
    
    def get_llm(self) -> Optional[BaseAgent]:
        """Get the configured LLM instance"""
        return self.llm

class Promptconfig:
    prompt: Optional[Any] = None
    
    def __init__(self) -> None:
        self.prompt = None
    
    def set_prompt(self, prompt: Any) -> None:
        self.prompt = prompt
    
    def get_prompt(self) -> Optional[Any]:
        return self.prompt

class ToolConfig:
    cleaner_tools: AllTools= None
    analyser_tools:AllTools = None
    visualizer_tools:AllTools= None
    def __init__(self) -> None:
        self.cleaner_tools = None
        self.analyser_tools = None
        self.visualizer_tools = None

    def set_cleaner_tools(self, tools: List[Any]) -> None:
        self.cleaner_tools = AllTools()
        self.cleaner_tools.add_tools(tools)

    def get_cleaner_tools(self) -> Optional[List[Any]]:
        return self.cleaner_tools
    
    def set_analyser_tools(self, tools: List[Any]) -> None:
        self.analyser_tools = AllTools().add_tools(tools)

    def get_analyser_tools(self) -> Optional[List[Any]]:
        return self.analyser_tools
    
    def set_visualizer_tools(self,tools:List[Any])->None:
        self.visualizer_tools=AllTools().add_tools(tools)

    def get_visualizer_tools(self)->Optional[List[Any]]:
        return self.visualizer_tools
    
class DataConfig:
    df: Optional[pd.DataFrame] = None
    
    def __init__(self) -> None:
        self.df = None
    
    def set_df(self, dataframe: Optional[pd.DataFrame] = None) -> None:
        if dataframe is not None:
            self.df = dataframe
        else:
            self.df = pd.read_csv("/home/elango/Documents/projects/statathon/uploads/df.csv")
    
    def get_df(self) -> Optional[pd.DataFrame]:
        return self.df
    
    def profile_data(self) -> Dict[str, Any]:
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=["object", "category"]).columns.tolist()
        datetime_cols = self.df.select_dtypes(include=["datetime"]).columns.tolist()
        boolean_cols = self.df.select_dtypes(include=["bool"]).columns.tolist()
        profile = {
            "columns": list(self.df.columns),
            "missing value count": (self.df.isna().sum()).to_dict(),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols,
            "boolean_columns": boolean_cols,
            "outlier_columns": [
                col for col in numeric_cols
                if self.df[col].nunique() > 1 and (np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std()) > 3).sum() > 0
            ],
            "skewness": self.df[numeric_cols].skew().round(3).to_dict() if numeric_cols else {},
            "sample": self.df.head(3).to_dict(orient="list")
        }
        return profile

class Config:
    cleaner_config: Cleaner_config = Cleaner_config()
    analyst_config: Analyser_config = Analyser_config()
    visualization_config: Visualizer_config = Visualizer_config()
    llm_config: LLMConfig = LLMConfig()
    tool_config: ToolConfig = ToolConfig()
    prompt_config: Promptconfig = Promptconfig()
    data_config: DataConfig = DataConfig()