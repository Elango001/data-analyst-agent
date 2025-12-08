from typing import List, Any, Dict

class AllTools:
    def __init__(self) -> None:
        self.tools: Dict[str, Any] = {}

    def add_tools(self, tools: List[Any]) -> None:
        for tool in tools:
            self.tools[tool.name] = tool

    def get_tools(self) -> Dict[str, Any]:
        return self.tools

    def invoke_tools(self, ops: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = ops.get("tool")
        params = ops.get("params", {})

        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}

        tool = self.tools[tool_name]
        return tool.invoke(params) if params else tool.invoke({})
    