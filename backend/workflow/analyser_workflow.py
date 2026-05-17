from backend.workflow.main_workflow import Workflow
from backend.workflow.state_management import State
from langgraph.graph import StateGraph, END
from typing import Optional, Any, Dict

class AnalyserWorkflow:
    workflow: Optional[Workflow] = None
    flow: Optional[StateGraph] = None
    graph: Optional[Any] = None
    
    def __init__(self, agent) -> None:
        self.workflow = Workflow(agent)
    
    def analyser_node(self, state: State) -> State:
        return self.workflow.run(state)
    
    def code_executor_node(self, state: State) -> State:
        return self.workflow.code_executor(state)
    
    def route_after_analyser(self, state: State) -> str:
        code_state = state.get("code") if isinstance(state.get("code"), dict) else {}
        if code_state.get("code"):
            return "code_executor"
        return "END"
    
    def nodes_generator(self) -> None:
        self.flow = StateGraph(State)
        self.flow.add_node("analyser", self.analyser_node)
        self.flow.add_node("code_executor", self.code_executor_node)
        self.flow.set_entry_point("analyser")
        self.flow.add_conditional_edges(
            "analyser",
            self.route_after_analyser,
            {
                "code_executor": "code_executor",
                "END": END,
            },
        )
        self.flow.add_edge("code_executor", "analyser")
        self.graph = self.flow.compile()
    
    def invoke(self, initial_state: State, config: Dict[Any, Any] = {'recursion_limit': 500}) -> Any:
        return self.graph.invoke(initial_state, config)