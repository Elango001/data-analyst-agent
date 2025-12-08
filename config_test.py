from Configuration.config import Config
from prompts.prompts import Prompts
from tools.cleaner_tools import c_tools
from workflow.cleaner_workflow import CleanerWorkflow
from dotenv import load_dotenv
load_dotenv()
import os
llm=Config.llm_config
llm.set_llm('google','gemini-2.5-flash',os.getenv("GOOGLE_API_KEY"))
prompt=Config.prompt_config
prompt.set_prompt(Prompts())
tools=Config.tool_config
tools.set_cleaner_tools(c_tools)
data=Config.data_config
data.set_df()
cleaner=Config.cleaner_config
cleaner.set_prompt(prompt.get_prompt())
print(tools.get_cleaner_tools() is not None)

cleaner.set_tools(tools.get_cleaner_tools())
cleaner.set_agent(llm.get_llm())
# print(cleaner.get_agent() is not None)
Config.cleaner_config=cleaner
print(Config.cleaner_config.get_agent() is not None)
print(Config.cleaner_config.get_tools() is not None)
print(Config.cleaner_config.get_prompt() is not None)
print(Config.cleaner_config.agent.prompt is not None)
cleaner_workflow=CleanerWorkflow(Config.cleaner_config)
cleaner_workflow.nodes_generator()
# cleaner_workflow.workflow.tool_executor({
#     "cleaner": {"count": 0, "cleaner_response": []},
#     "analyser": {"count": 0, "analyzer_response": []},
#     "visualizer": {"count": 0, "visualizer_response": []},
#     "cur_agent": "cleaner",
#     "tool_call": [{'tool':'fillna','params':{'columns':['FWI']}}],
#     "success_tools": [],
#     "failed_tools": [],
#     "tool_result": [],
#     "df_info": data.profile_data(),
# })
initial_state={
    "cleaner": {"count": 0, "cleaner_response": []},
    "analyser": {"count": 0, "analyzer_response": []},
    "visualizer": {"count": 0, "visualizer_response": []},
    "cur_agent": "cleaner",
    "tool_call": [{'tool':'fillna','params':{'columns':['FWI']}}],
    "success_tools": [],
    "failed_tools": [],
    "tool_result": [],
    "df_info": data.profile_data(),
}
cleaner_workflow.invoke(initial_state)
