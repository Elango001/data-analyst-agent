from agents.analyser_agent import AnalyserAgent
from agents.agent_utils import ChatGemini
from prompts.prompts import Prompts
from tools.analyser_tools import a_tools
import os
from dotenv import load_dotenv
load_dotenv() 
provider="google"
model="gemini-2.5-flash"
api_key=os.getenv("API_KEY")
chat_gemini = ChatGemini().bind_tools(a_tools)
chat_gemini.set_agent(model=model, api_key=api_key)
prompt=Prompts()
analyser=AnalyserAgent(chat_gemini,prompt)
initial_state={
            "cleaner": {"count": 0, "cleaner_response": []},
            "analyser": {"count": 0, "analyzer_response": []},
            "visualizer": {"count": 0, "visualizer_response": []},
            "cur_agent": "Cleaner",
            "tool_call": None,
            "success_tools": [],
            "failed_tools": [],
            "tool_result": [],
            "df_info":None
        }
analyser.run(initial_state)
