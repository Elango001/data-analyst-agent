from typing import TypedDict, List, Any, Optional
from langgraph.graph import MessagesState
class CleanerLog(TypedDict):
    count: int
    cleaner_response: List[Any]
class AnalyserLog(TypedDict):
    count: int
    analyser_response: List[Any]
class VisualizerLog(TypedDict):
    count: int
    visualizer_response: List[Any]
class CodeManager(TypedDict):
    code_id: str
    code: str
    code_result: List[Any]
    code_error: List[Any]
class ToolManager(TypedDict):
    tool_id: str
    tool_call: List[Any]
    success_tools: List[Any]
    failed_tools: List[Any]
    tool_result: List[Any]
class State(MessagesState):
    cleaner: CleanerLog
    analyser: AnalyserLog
    visualizer: VisualizerLog
    cur_agent: Optional[str]
    code: Optional[CodeManager]
    tool: Optional[ToolManager]
    df_info: Optional[str]
    count: int
    max_limit: Optional[int]
    needs_user_confirm: Optional[bool]
    needs_user_confirm_reason: Optional[str]
class AgentSwitcher(TypedDict):
    cur_agent: str
    next_agent: str
    reason: str
    timestamp: float
    done: bool

def init_state() -> State:
    """Initialize a fresh state for pipeline execution.
    
    Returns a State dict with all required fields pre-populated with
    default values for the three-agent pipeline.
    """
    return {
        "messages": [],
        "cur_agent": "cleaner",
        "tool" : ToolManager(
        tool_id="",
        tool_call=[],
        success_tools=[],
        failed_tools=[],
        tool_result=[]
        ),
        "code":CodeManager(
        code_id="",
        code="",
        code_result=[],
        code_error=[],
        ),
        "df_info": "",
        "count": 0,
        "max_limit": 100,
        "needs_user_confirm": False,
        "needs_user_confirm_reason": "",
        "cleaner": {
            "count": 0,
            "cleaner_response": [],
        },
        "analyser": {
            "count": 0,
            "analyser_response": [],
        },
        "visualizer": {
            "count": 0,
            "visualizer_response": [],
        },
    }

def state_update(state: State) -> State:
    """Initialize or reset `code` and `tool` entries in `state` and return it.

    This function mutates the provided `state` mapping by setting fresh
    `ToolManager` and `CodeManager` structures so callers have a known
    initial state for tool and code execution tracking.
    """
    state["tool"] = ToolManager(
        tool_id="",
        tool_call=[],
        success_tools=[],
        failed_tools=[],
        tool_result=[]
    )
    state["code"] = CodeManager(
        code_id="",
        code="",
        code_result=[],
        code_error=[],
    )
    return state