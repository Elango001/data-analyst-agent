from workflow.main_workflow import Workflow
from workflow.state_management import State
from langgraph.graph import StateGraph, END
from typing import Optional, Any, Dict

class CleanerWorkflow:
    workflow: Optional[Workflow] = None
    flow: Optional[StateGraph] = None
    graph: Optional[Any] = None
    
    def __init__(self,agent) -> None:
        self.workflow = Workflow(agent)
        self.workflow=self.workflow.bind_tools()
    
    def clean_node(self, state: State) -> State:
        return  self.workflow.run(state)
    
    def tool_executor_node(self, state: State) -> State:
        return self.workflow.tool_executor(state)

    def route_after_cleaner(self, state: State) -> str:
        if state["tool_call"]:
            return "tool_executor"
        return "END"
    
    def nodes_generator(self) -> None:
        self.flow = StateGraph(State)
        self.flow.add_node("cleaner_node", self.clean_node)
        self.flow.add_node("tool_executor", self.tool_executor_node)
        self.flow.set_entry_point("cleaner_node")
        self.flow.add_conditional_edges(
            "cleaner_node",
            self.route_after_cleaner,
            {
                "tool_executor": "tool_executor",
                "END": END,
            },
        )
        self.flow.add_edge("tool_executor", "cleaner_node")
        self.graph = self.flow.compile()
    
    def invoke(self, initial_state: State, config: Dict[Any, Any] = {'recursion_limit': 500}) -> Any:
        return self.graph.invoke(initial_state, config)