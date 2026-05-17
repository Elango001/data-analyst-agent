from backend.agents.Agent import BaseAgent
from typing import List, Any, Dict, Tuple, Optional, Callable
import json
from langchain.chat_models import ChatOpenAI
import time
import random
import re


def _split_text_and_code(text: str) -> Tuple[str, Optional[str]]:
    code: Optional[str] = None
    code_match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if code_match:
        code = code_match.group(1).strip()
        text = re.sub(r"```(?:python)?\s*.*?```", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    return text.strip(), code


class ChatOpenAI_(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self._llm: Optional[Any] = None

    def set_agent(self, model: str, api_key: str) -> "ChatOpenAI_":
        try:
            self._llm = ChatOpenAI(model=model, openai_api_key=api_key, temperature=0)
            return self
        except Exception as e:
            raise Exception(f"Invalid API key or model: {e}")

    def bind_tools(self, tools: List[Callable]) -> "ChatOpenAI_":
        if not self._llm:
            raise ValueError("LLM not initialized. Call set_agent() first.")
        self._llm = self._llm.bind_tools(tools)
        return self

    def _call_model(self, msg: str) -> Any:
        if not self._llm:
            raise ValueError("LLM not initialized. Call set_agent() first.")
        return self._llm.invoke(msg)

    def invoke(self, msg: str, max_retries: int = 5) -> Any:
        for attempt in range(1, max_retries + 1):
            try:
                return self._call_model(msg)
            except Exception:
                if attempt == max_retries:
                    raise
                time.sleep(0.4 * attempt + random.random())

    def _parse_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        tool_calls: List[Dict[str, Any]] = []
        raw_calls = getattr(response, "tool_calls", None)
        if raw_calls is None:
            raw_calls = getattr(getattr(response, "additional_kwargs", {}), "get", lambda _k, _d=None: _d)("tool_calls", None)

        if not raw_calls:
            return tool_calls

        for call in raw_calls:
            name = None
            args = None
            if isinstance(call, dict):
                name = call.get("name") or call.get("tool")
                args = call.get("args") or call.get("params")
            else:
                name = getattr(call, "name", None)
                args = getattr(call, "args", None)

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw": args}

            tool_calls.append({"tool": name, "params": args or {}})

        return tool_calls

    def split_agent_output(self, response: Any) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
        text = getattr(response, "content", "") or getattr(response, "text", "") or ""
        tool_calls = self._parse_tool_calls(response)
        text, code = _split_text_and_code(text)
        return text, tool_calls, code
