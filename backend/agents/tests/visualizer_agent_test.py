from agents.visualizer_agent import VisualizerAgent
from agents.agent_utils import ChatGemini
from prompts.prompts import Prompts
from tools.visualizer_tools import v_tools
import os
from dotenv import load_dotenv
load_dotenv() 
provider="google"
model="gemini-2.5-flash"
api_key=os.getenv("API_KEY")
chat_gemini = ChatGemini().bind_tools(v_tools)
chat_gemini.set_agent(model=model, api_key=api_key)
prompt=Prompts()
visualizer=VisualizerAgent(chat_gemini,prompt)
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
visualizer.run(initial_state)
