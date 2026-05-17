from backend.workflow.state_management import State
from backend.Configuration.config import Config
from typing import Any, Optional, Dict
import contextlib
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class Workflow:
    llm: Optional[Any] = None
    prompt: Optional[Any] = None
    agent: Optional[Any] = None
    tools: Optional[Any] = None
    dataconfig: Optional[Any] = None
    
    def __init__(self, agent: Any) -> None:
        self.prompt = agent.get_prompt()
        self.agent = agent.get_agent()
        self.tools = agent.get_tools()
        self.dataconfig = Config.data_config
    def bind_tools(self):
        if self.tools:
            self.llm=self.agent.llm.bind_tools(self.tools.get_tools().values())
        return self
    def run(self, state: State) -> State:
        return self.agent.run(state)
    
    def tool_executor(self, state: State) -> State:
        tool_state = state.get("tool") if isinstance(state.get("tool"), dict) else {}
        tool_state["tool_result"] = []
        ops = tool_state.get("tool_call", [])
        if not ops:
            state["tool"] = tool_state
            return state
        logger = getattr(Config, "logger", None)
        for call in ops:
            result = self.tools.invoke_tools(call)
            tool_state["tool_result"].append(result)
            if result.get("success") is True:
                tool_state["success_tools"].append(call)
            else:
                tool_state["failed_tools"].append(call)
            if logger:
                logger.log_tool_execution(
                    agent_name=state.get("cur_agent") or "unknown",
                    tool_name=call.get("tool", "unknown"),
                    tool_payload={"params": call.get("params", {}), "result": result},
                )

        tool_state["tool_call"] = []
        state["tool"] = tool_state
        state["df_info"] = self.dataconfig.profile_data()
        return state

    def code_executor(self, state: State) -> State:
        code_state = state.get("code") if isinstance(state.get("code"), dict) else {}
        code_payload = code_state.get("code") or ""
        if not code_payload:
            state["code"] = code_state
            return state

        stdout = io.StringIO()
        result_payload: Optional[Any] = None
        error_payload: Optional[Dict[str, Any]] = None
        exec_env: Dict[str, Any] = {
            "df": Config.data_config.get_df(),
            "pd": pd,
            "np": np,
            "plt": plt,
            "sns": sns,
        }

        try:
            with contextlib.redirect_stdout(stdout):
                exec(code_payload, exec_env)
            if "result" in exec_env:
                result_payload = exec_env.get("result")
            output_text = stdout.getvalue().strip()
            if output_text:
                result_payload = {"stdout": output_text, "result": result_payload}
            code_state.setdefault("code_result", []).append(result_payload)
        except Exception as exc:
            error_payload = {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
            code_state.setdefault("code_error", []).append(error_payload)
        finally:
            logger = getattr(Config, "logger", None)
            if logger:
                logger.log_code_execution(
                    agent_name=state.get("cur_agent") or "unknown",
                    code_id=code_state.get("code_id"),
                    code_payload=code_payload,
                    result_payload=result_payload,
                    error_payload=error_payload,
                )

        state["code"] = code_state
        return state

