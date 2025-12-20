from typing import Optional, Any
from backend.workflow.state_management import State

DEFAULT_CLEANER_PROMPT = """
You are a data cleaning agent.
Goal: Suggest the next best data-cleaning step based on the dataset summary.
Data state:
{data}
SUCCEEDED TOOLS:
{success_tools}
FAILED TOOLS:
{failed_tools}
Rules:
1. return a text message explaining why you did that in 2 to 3 lines. 
2. You can return multiple tool calls.
3. If a tool exists in `failed_tools`, attempt to FIX the issue by modifying params rather than repeating the same call.
4. DO NOT repeat tools from `success_tools` unless needed for new columns.
5. If no action is needed, return an empty list and explain why.
"""

DEFAULT_ANALYSER_PROMPT = """
You are a data analysis agent.
Your goal is to suggest the next best data-analysis step based on:
- the current data state,
- the previous analysis report,
- and the results of tool executions.
The data is already clean and ready for analysis
DATA STATE:
{data}
PREVIOUS ANALYSIS REPORT:
{previous_report}
SUCCEEDED TOOLS:
{success_tools}
FAILED TOOLS:
{failed_tools}
RULES:
1. If the previous analysis report contains useful insights, summarize what you understood and propose the next logical analysis step.
2. If the previous report is empty or insufficient, you MUST call a tool to perform analysis or extract more information.
3. You are allowed to return multiple tool calls in one response.
4. If a tool appears in `failed_tools`, DO NOT repeat the same failing call. Instead, FIX the issue by modifying parameters or choosing a more appropriate tool.
5. DO NOT repeat tools from `success_tools` unless they are required for newly found columns or additional insights.
6. If no further action is required, return an empty tool-call list and explain why analysis is complete.
7. Every tool call MUST be relevant, justified, and aimed at improving or understanding the data better.
"""

DEFAULT_VISUALIZER_PROMPT = """
You are a data visualizing agent.
Goal: Suggest the next best data-visualization step based on the data state.
Data state:
{data}
SUCCEEDED TOOLS:
{success_tools}
FAILED TOOLS:
{failed_tools}
Rules:
1. return a text message explaining why you did that in 1 to 3 lines.
2. You can return multiple tool calls.
3. If a tool exists in `failed_tools`, attempt to FIX the issue by modifying params rather than repeating the same call.
4. DO NOT repeat tools from `success_tools` unless needed for new columns.
5. If no action is needed, return an empty list and explain.
"""

class Prompts:
    Cleaner_prompt: Optional[str] = None
    Analyser_prompt: Optional[str] = None
    Visualizer_prompt: Optional[str] = None

    def __init__(self) -> None:
        self.Cleaner_prompt = DEFAULT_CLEANER_PROMPT
        self.Analyser_prompt = DEFAULT_ANALYSER_PROMPT
        self.Visualizer_prompt = DEFAULT_VISUALIZER_PROMPT

    def set_cleaner_prompt(self, prompt: Optional[str] = None) -> None:
        if prompt:
            self.Cleaner_prompt = prompt
    
    def set_analyser_prompt(self, prompt: Optional[str] = None) -> None:
        if prompt:
            self.Analyser_prompt = prompt
    
    def set_visualizer_prompt(self, prompt: Optional[str] = None) -> None:
        if prompt:
            self.Visualizer_prompt = prompt
    
    def cleaner_prompt_formater(self, state: State, msg: str) -> str:
        return msg.format(
            data=state["df_info"],
            success_tools=state["success_tools"],
            failed_tools=state["failed_tools"]
        )
    
    def get_cleaner_prompt(self, state: State) -> str:
        return self.cleaner_prompt_formater(state, self.Cleaner_prompt)
    
    def analyser_prompt_formater(self, state: State, msg: str) -> str:
        return msg.format(
            data=state["df_info"],
            previous_report=state["previous_report"],
            success_tools=state["success_tools"],
            failed_tools=state["failed_tools"]
        )
    
    def get_analyser_prompt(self, state: State) -> str:
        return self.analyser_prompt_formater(state, self.Analyser_prompt)
    
    def visualizer_prompt_formater(self, state: State, msg: str) -> str:
        return msg.format(
            data=state["df_info"],
            success_tools=state["success_tools"],
            failed_tools=state["failed_tools"]
        )
    
    def get_visualizer_prompt(self, state: State) -> str:
        return self.visualizer_prompt_formater(state, self.Visualizer_prompt)
    