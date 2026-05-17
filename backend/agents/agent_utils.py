from backend.agents.Agent import BaseAgent
from typing import get_type_hints, List, Any, Dict, Tuple, Optional, Callable
import inspect
import re
from google import genai
from google.genai import types
import time
import random


def _split_text_and_code(text: str) -> Tuple[str, Optional[str]]:
    code: Optional[str] = None
    code_match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if code_match:
        code = code_match.group(1).strip()
        text = re.sub(r"```(?:python)?\s*.*?```", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    return text.strip(), code

class ChatGemini(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
    def set_agent(self, model: str, api_key: str)-> 'ChatGemini':
        try:
            self.client: genai.Client = genai.Client(api_key=api_key)
            self.model_name: str = model
            self._config: Optional[types.GenerateContentConfig] = None
            return self
        except Exception as e:
            raise Exception(f"Invalid API key or model: {e}")

    def bind_tools(self, tools: List[Callable]) -> 'ChatGemini':
        self._config = types.GenerateContentConfig(
            tools=[
                types.Tool(
                    function_declarations=[
                        self.create_function_declaration(t.func) for t in tools
                    ]
                )
            ]
        )
        return self

    def create_function_declaration(self, fn: Callable) -> Dict[str, Any]:
        sig = inspect.signature(fn)
        hints = get_type_hints(fn)
        doc = inspect.getdoc(fn) or ""
        desc = doc.split("\n")[0].strip()

        properties: Dict[str, Any] = {}
        required: List[str] = []
        for name, param in sig.parameters.items():
            annotation = hints.get(name, str)
            if annotation == list or "List" in str(annotation):
                field = {"type": "array", "items": {"type": "string"}}
            elif annotation in (int, float):
                field = {"type": "number"}
            elif annotation is bool:
                field = {"type": "boolean"}
            else:
                field = {"type": "string"}
            properties[name] = field
            if param.default is inspect._empty:
                required.append(name)

        return {
            "name": fn.__name__,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def _call_model(self, msg: str) -> Any:
        return self.client.models.generate_content(
            model=self.model_name,
            contents=msg,
            config=self._config,
        )

    def invoke(self, msg: str, max_retries: int = 5) -> Any:
        for attempt in range(1, max_retries + 1):
            try:
                return self._call_model(msg)
            except Exception as e:
                if attempt == max_retries:
                    raise
                time.sleep(0.4 * attempt + random.random())
    
    def split_agent_output(self, response: Any) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
        text = getattr(response, "text", "") or ""
        part = response.candidates[0].content.parts
        tool_calls: List[Dict[str, Any]] = []
        for i, j in enumerate(part):
            if i == 0:
                continue
            if hasattr(j, "function_call") and j.function_call:
                tool_calls.append({"tool": j.function_call.name, "params": j.function_call.args})
        text, code = _split_text_and_code(text)
        return text, tool_calls, code