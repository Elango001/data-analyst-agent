from workflow.main_workflow import Workflow
from workflow.state_management import State
from langgraph.graph import StateGraph, END
from typing import Optional, Any, Dict

class AnalyserWorkflow:
    workflow: Optional[Workflow] = None
    flow: Optional[StateGraph] = None
    graph: Optional[Any] = None
    
    def __init__(self) -> None:
        self.workflow = Workflow()
    
    def analyser_node(self, state: State) -> State:
        return self.workflow.run(state)
    
    def tool_executor_node(self, state: State) -> State:
        return self.workflow.tool_executor(state)
    
    def route_after_analyser(self, state: State) -> str:
        if state["tool_call"]:
            return "tool_executor"
        return "END"
    
    def nodes_generator(self) -> None:
        self.flow = StateGraph(State)
        self.flow.add_node("analyser", self.analyser_node)
        self.flow.add_node("tool_executor", self.tool_executor_node)
        self.flow.set_entry_point("analyser")
        self.flow.add_conditional_edges(
            "analyser",
            self.route_after_analyser,
            {
                "tool_executor": "tool_executor",
                "END": END,
            },
        )
        self.graph = self.flow.compile()
    
    def invoke(self, initial_state: State, config: Dict[Any, Any] = {'recursion_limit': 500}) -> Any:
        return self.graph.invoke(initial_state, config)