from backend.workflow.state_management import State, state_update
from typing import Optional, Any

class CleanerAgent:
    llm: Optional[Any] = None
    prompt: Optional[Any] = None
    
    def __init__(self, llm: Any, prompt: Optional[Any] = None) -> None:
        self.llm = llm
        self.prompt = prompt
    
    def run(self, state: State) -> State:
        if state["cleaner"]['count'] == 0:
            state = state_update(state)
        response = self.llm.invoke(self.prompt.get_cleaner_prompt(state))
        reason, tool_args = self.llm.split_agent_output(response)
        print(reason,tool_args)
        if tool_args and tool_args != []:
            state["tool_call"] = tool_args
        else:
            state["tool_call"] = None
            state["cur_agent"] = "analyser"
        state["cleaner"]["count"] = state["cleaner"].get("count", 0) + 1
        state["cleaner"]["cleaner_response"].append(reason)
        return state