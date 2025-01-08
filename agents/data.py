from agents.base import Agent, Chat
from packets import *
from typing import List, Dict, Any, Tuple, Union, Optional
from utils.call_api_hr import *

import yaml

from packets import CounterQueryPayload
# VARS = yaml.safe_load(open("files\\api_info.yaml", "r"))
# VARS = VARS['DATA_EXTRACT']

DB = yaml.safe_load(open(".\\files\\salary_data.yaml", "r"))
vars: str = ""
for key, value in DB.items():
    vars = f"{vars} \n {key} : "
    for k, v in value['vars'].items():
        vars = f"{vars} {k} ({v['use']}), "

print("VARS:", vars)

DB2 = yaml.safe_load(open(".\\files\\predefined_queries.yaml", "r"))
PREDEFINED_VARS  = {}
for key, value in DB2.items():
    PREDEFINED_VARS[key] = value['use']





class DATAAgent(Chat):#, Agent):
    def __init__(self):
        print("DATABackend __init__")
        self.counter_queries: List[CounterQueryPayload] = []
        self.missing_vars: Dict[str, str] = {}
        self.sql_tables: List[str] = []  # ["table"]

    async def detect_relevant_predefined_queries(self) -> Tuple[str, Dict[str, Any]]:
        # ALGO: Check if the user query is in the predefined queries list
        llm_query: str = f"Query : {self.conversation.SAQ} \n Query Intent: {self.conversation.intent} \n Variables: {PREDEFINED_VARS}"
        response: Dict[str, Any] = await self.llm_call(llm_query, use="predefined_queries")
        return response


    async def detect_relevant_vars(self) -> Dict[str, Any]:
        # TODO: Get the relevant variables from the LLM model
        llm_query: str = f"Query : {self.conversation.SAQ} \n Query Intent: {self.conversation.intent} \n Variables: {vars}"
        relevant_vars = await self.llm_call(llm_query, use="relevant_db_vars")
        return relevant_vars
    
    
    async def resolve_missing_variables(self, relevant_vars: List[str]) -> None:
        for section in relevant_vars:
            input_params: Dict[str, Any] = DB[section]['input_params']
            
            for param in input_params.keys():
                if self.chat_session.user_data and (not self.chat_session.user_data.has_data(param)):
                    self.missing_vars[param] = input_params[param]

            output_vars = DB2[section]['vars']
            self.chat_session.user_data.api.output_data.update(output_vars)

            self.sql_tables.append(section)
        
        print("+++++++++++++++ DATA +++++++++++++++")
        print(self.chat_session.user_data.to_str()) # type: ignore
        print("++++++++++++++++++++++++++++++++++++")
            
        print("Missing variables:", self.missing_vars.keys())

    async def generate_counter_queries(self):

        if self.missing_vars:

            print("Missing variables:", self.missing_vars.keys())
            input_vars = "\n".join([f"{key} : {value}" for key, value in self.missing_vars.items()])
            llm_query = f"User query: {self.conversation.SAQ} \n Query Intent: {self.conversation.intent} \n Missing variables: \n{input_vars}"
            response = await self.llm_call(llm_query, use="counter_queries")
            

            self.counter_queries = [CounterQueryPayload(
                counter_query_id=i,
                counter_query=Query(text=subquery[1]),
                user_response=Response(text=""),
                query_variable=subquery[0],
            ) for i, subquery in enumerate(response.items())]


    async def update_memory(self, subquery: str, keyword: str, user_response: str):
        input_vars = "\n".join([f"`{key} : {value}`" for key, value in self.missing_vars.items()])
        llm_query = f"Query: {subquery} \nkeyword: {keyword} \nValue: {user_response}\nList of Variables: {input_vars}"
        response: Dict[str, str] = await self.llm_call(llm_query, use="extract_vars")
    
        self.chat_session.user_data.api.input_data.update(response) # type: ignore
        self.chat_session.chat_history.append(Message(content=user_response, sender="user", metadata={"type": "counter_response"})) # type: ignore

    
    async def resolve_counter_queries(self) -> CounterQueryPayload | None:

        if len(self.counter_queries) > 0:
            return self.counter_queries.pop(0)
        
        return None

    async def execute_apis(self):
        # TODO: Execute the APIs and update the memory with the output vars
        for api_name in self.apis:
            api_response: Dict[str, Any] = tools[api_name](**self.chat_session.user_data.get_all_data()) # type: ignore
            self.chat_session.user_data.api.output_data.update(api_response) # type: ignore

    async def api_response_generation(self) -> BotResponsePayload:
        """
        A decision maker that evaluates the API responses and decides the next course of action.
        1. Humanize the response using LLMatic transformation.
        2. Return the final response to the user as it is.
        """
        
        api_data= self.chat_session.user_data.to_str(data_type="output")  # type: ignore
        meta_data = self.chat_session.user_data.to_str(data_type="meta")  # type: ignore
        var_data = f"{api_data} {meta_data}"
        
        llm_query: str = f"query: {self.conversation.SAQ}\n User-Intent: {self.conversation.intent}\n Available data: {var_data}"
        response: Dict[str, Any] = await self.llm_call(llm_query, use="api_response")

        payload = BotResponsePayload(bot_response=Response(text=response["response"]))

        return payload
