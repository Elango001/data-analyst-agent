from typing import Optional, Any
from backend.workflow.state_management import State

DEFAULT_CLEANER_PROMPT = """
You are a data cleaning agent.
Goal: Recommend the next best cleaning step based on the dataset summary.

DATA STATE:
{data}
SUCCEEDED TOOLS:
{success_tools}
FAILED TOOLS:
{failed_tools}

Instructions:
- Keep the response short (2-4 lines).
- Use tool calls for cleaning steps. You may call multiple tools.
- If a tool is in `failed_tools`, adjust params or pick a different tool instead of repeating.
- Do not repeat tools in `success_tools` unless required for new columns.
- If nothing is needed, return no tool calls and explain why.
- Do not return code.
"""

DEFAULT_ANALYSER_PROMPT = """
You are a data analysis agent.
Your goal is to recommend the next analysis step based on:
- current data state
- the previous analysis report

DATA STATE:
{data}
PREVIOUS ANALYSIS REPORT:
{previous_report}
LAST CODE RESULT:
{last_code_result}
LAST CODE ERROR:
{last_code_error}

Instructions:
- Keep the response short (2-4 lines).
- Return analysis code only.
- If analysis is complete, return no code and explain why.
- If returning code, use a single fenced Python block.
"""

DEFAULT_VISUALIZER_PROMPT = """
You are a data visualization agent.
Goal: Recommend the next visualization step based on data state and the analysis report.

DATA STATE:
{data}
ANALYSIS REPORT:
{previous_report}
LAST CODE RESULT:
{last_code_result}
LAST CODE ERROR:
{last_code_error}

Instructions:
- Keep the response short (1-3 lines).
- Return visualization code only.
- Use only matplotlib and seaborn for plots.
- If no action is needed, return no code and explain.
- If returning code, use a single fenced Python block.
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
        tool_state = state.get("tool") if isinstance(state.get("tool"), dict) else {}
        return msg.format(
            data=state["df_info"],
            success_tools=tool_state.get("success_tools", []),
            failed_tools=tool_state.get("failed_tools", [])
        )
    
    def get_cleaner_prompt(self, state: State) -> str:
        return self.cleaner_prompt_formater(state, self.Cleaner_prompt)
    
    def analyser_prompt_formater(self, state: State, msg: str) -> str:
        analyser_state = state.get("analyser") if isinstance(state.get("analyser"), dict) else {}
        prev_reports = analyser_state.get("analyser_response", [])
        previous_report = prev_reports[-1] if prev_reports else ""
        code_state = state.get("code") if isinstance(state.get("code"), dict) else {}
        code_results = code_state.get("code_result", [])
        code_errors = code_state.get("code_error", [])
        last_code_result = code_results[-1] if code_results else ""
        last_code_error = code_errors[-1] if code_errors else ""
        return msg.format(
            data=state["df_info"],
            previous_report=previous_report,
            last_code_result=last_code_result,
            last_code_error=last_code_error,
        )
    
    def get_analyser_prompt(self, state: State) -> str:
        return self.analyser_prompt_formater(state, self.Analyser_prompt)
    
    def visualizer_prompt_formater(self, state: State, msg: str) -> str:
        analyser_state = state.get("analyser") if isinstance(state.get("analyser"), dict) else {}
        prev_reports = analyser_state.get("analyser_response", [])
        previous_report = prev_reports[-1] if prev_reports else ""
        code_state = state.get("code") if isinstance(state.get("code"), dict) else {}
        code_results = code_state.get("code_result", [])
        code_errors = code_state.get("code_error", [])
        last_code_result = code_results[-1] if code_results else ""
        last_code_error = code_errors[-1] if code_errors else ""
        return msg.format(
            data=state["df_info"],
            previous_report=previous_report,
            last_code_result=last_code_result,
            last_code_error=last_code_error,
        )
    
    def get_visualizer_prompt(self, state: State) -> str:
        return self.visualizer_prompt_formater(state, self.Visualizer_prompt)
    