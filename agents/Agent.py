from abc import ABC, abstractmethod
from typing import List, Any

class BaseAgent(ABC):
    @abstractmethod
    def set_agent(self, model: str, api_key: str) -> None:
        pass
    
    @abstractmethod
    def bind_tools(self, tools: List[Any]) -> None:
        pass

    @abstractmethod
    def invoke(self, msg: str, max_retries: int = 5) -> str:
        pass


