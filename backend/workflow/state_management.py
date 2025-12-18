from typing import TypedDict, List, Any, Optional
from langgraph.graph import MessagesState
class CleanerState(TypedDict):
    count: int
    cleaner_response: List[Any]
class AnalyseState(TypedDict):
    count: int
    analyzer_response: List[Any]
class VisualizerState(TypedDict):
    count: int
    visualizer_response: List[Any]
class State(MessagesState):
    cleaner: CleanerState
    analyser: AnalyseState
    visualizer: VisualizerState
    cur_agent: Optional[str]
    tool_call: Optional[str]
    success_tools: List[Any]
    failed_tools: List[Any]
    tool_result: List[Any]
    df_info: Optional[str]
def state_update(state:State)->State:
    state["success_tools"]=[]
    state["failed_tools"]=[]
    state["tool_result"]=[]
    return state