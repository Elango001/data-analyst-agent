from backend.workflow.state_management import State, state_update
from typing import Optional, Any

class VisualizerAgent:
    llm: Optional[Any] = None
    prompt: Optional[Any] = None
    
    def __init__(self, llm: Any, prompt: Optional[Any] = None) -> None:
        self.llm = llm
        self.prompt = prompt
    
    def run(self, state: State) -> State:
        if state["visualizer"]["count"] == 0:
            state = state_update(state)

        response = self.llm.invoke(self.prompt.get_visualizer_prompt(state))
        try:
            reason, tool_args, code = self.llm.split_agent_output(response)
        except ValueError:
            reason, tool_args = self.llm.split_agent_output(response)
            code = None

        tool_state = state.get("tool") if isinstance(state.get("tool"), dict) else {}
        tool_state["tool_call"] = []
        state["tool"] = tool_state

        code_state = state.get("code") if isinstance(state.get("code"), dict) else {}
        code_state["code"] = code or ""
        code_state["code_id"] = f"visualizer-{state['visualizer'].get('count', 0) + 1}"
        state["code"] = code_state

        if not code:
            state["cur_agent"] = "END"

        state["visualizer"]["count"] = state["visualizer"].get("count", 0) + 1
        state["visualizer"]["visualizer_response"].append(reason)

        from backend.Configuration.config import Config

        logger = getattr(Config, "logger", None)
        if logger:
            logger.log_agent_interaction(
                agent_name="visualizer",
                response_data=reason,
                tool_payload=tool_args or [],
                code_payload=code,
            )
        return state

    
