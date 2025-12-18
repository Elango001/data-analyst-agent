from backend.workflow.state_management import State, state_update
from typing import Optional, Any

class VisualizerAgent:
    llm: Optional[Any] = None
    prompt: Optional[Any] = None
    
    def __init__(self, llm: Any, prompt: Optional[Any] = None) -> None:
        self.llm = llm
        self.prompt = prompt
    
    def run(self, state: State) -> State:
        if state["visualizer"]['count'] == 0:
            state = state_update(state)
        response = self.llm.invoke(self.prompt.get_visualizer_prompt(state))
        reason, tool_args = self.llm.split_agent_output(response)
        if tool_args and tool_args != []:
            state["tool_call"] = tool_args
        else:
            state["tool_call"] = None
            state["cur_agent"] = "END"
        state["visualizer"]["count"] = state["visualizer"].get("count", 0) + 1
        state["visualizer"]["visualizer_response"].append(reason)
        return state

    
