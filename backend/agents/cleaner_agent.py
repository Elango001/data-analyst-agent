from backend.workflow.state_management import State, state_update
from typing import Optional, Any, List, Dict

class CleanerAgent:
    llm: Optional[Any] = None
    prompt: Optional[Any] = None
    
    def __init__(self, llm: Any, prompt: Optional[Any] = None) -> None:
        self.llm = llm
        self.prompt = prompt
    
    def run(self, state: State) -> State:
        if state["cleaner"]["count"] == 0:
            state = state_update(state)
        response = self.llm.invoke(self.prompt.get_cleaner_prompt(state))
        try:
            reason, tool_args, _code = self.llm.split_agent_output(response)
        except ValueError:
            reason, tool_args = self.llm.split_agent_output(response)
            _code = None

        tool_args = tool_args or []
        tool_state = state.get("tool") if isinstance(state.get("tool"), dict) else {}
        tool_state["tool_call"] = tool_args
        state["tool"] = tool_state
        if not tool_args:
            state["cur_agent"] = "analyser"

        state["cleaner"]["count"] = state["cleaner"].get("count", 0) + 1
        state["cleaner"]["cleaner_response"].append(reason)

        from backend.Configuration.config import Config

        logger = getattr(Config, "logger", None)
        if logger:
            logger.log_agent_interaction(
                agent_name="cleaner",
                response_data=reason,
                tool_payload=tool_args,
                code_payload=None,
            )
        return state