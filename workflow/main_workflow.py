from workflow.state_management import State
from Configuration.config import Config
from typing import Any, Optional

class Workflow:
    llm: Optional[Any] = None
    prompt: Optional[Any] = None
    agent: Optional[Any] = None
    tools: Optional[Any] = None
    dataconfig: Optional[Any] = None
    
    def __init__(self,agent) -> None:
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
        state["tool_result"] = []
        if not state["tool_call"]:
            return state
        ops = state["tool_call"]
        print(ops)
        for call in ops:
            state["tool_result"].append(self.tools.invoke_tools(call))
            if state["tool_result"][-1]["success"] == True:
                state['success_tools'].append(call)
            else:
                state['failed_tools'].append(call)
        state["tool_call"] = None
        state["df_info"] = self.dataconfig.profile_data()
        return state

