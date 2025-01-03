from agents.base import Agent, Chat
from packets import *
from typing import List, Dict, Any, Tuple, Union, Optional
from utils.call_api_hr import *

import yaml

from packets import CounterQueryPayload
VARS = yaml.safe_load(open("utils\\api_info.yaml", "r"))
VARS = VARS['DATA_EXTRACT']


class DATAAgent(Chat):#, Agent):
    def __init__(self):
        print("DATABackend __init__")
        self.counter_queries: List[CounterQueryPayload] = []
        self.missing_vars: Dict[str, str] = {}
        self.apis: Dict[str, Dict[str, Any]] = {}  # {api_name: {"input_vars": [], "output_vars": []}}



    async def detect_relevant_vars(self) -> Dict[str, Any]:
        # TODO: Get the relevant variables from the LLM model
        output_vars: str = "\n".join([f"{key} : {value['use']}" for key, value in VARS.items() if value['use']])
        llm_query: str = f"Query : {self.conversation.SAQ} \n Query Intent: {self.conversation.intent} \n Variables: {output_vars}"
        relevant_vars = await self.llm_call(llm_query, use="detect_relevant_vars")
        return relevant_vars


    async def resolve_api_dependencies(self, relevant_vars: Dict[str, Any])-> None: # type: ignore
        # TODO: Find the missing variables and update the memory
        
        for slave_query in relevant_vars:
            for output_var in relevant_vars[slave_query]:
                api_name: str = VARS[output_var]["api_to_be_called"]
                # if a new api is found
                if api_name not in self.apis:
                    self.apis[api_name] = {
                        "input_vars": VARS['bonus_amount']["input_vars"],
                        "output_vars": [output_var],
                    }
                    # check if the input_vars are already in the memory, if not add to the missing_vars
                    for var, use in self.apis[api_name]["input_vars"].items():
                        if self.chat_session.user_data and (not self.chat_session.user_data.has_data(var)):
                            self.missing_vars[var] = use

                # if the api is already in the list, append the output_vars
                elif output_var not in self.apis[api_name]["output_vars"]:
                    self.apis[api_name]["output_vars"].append(output_var)

        for slave_query in relevant_vars:
            for output_var in relevant_vars[slave_query]:
                api_name: str = VARS[output_var]["api_to_be_called"]
                # if a new api is found
                if api_name not in self.apis:
                    self.apis[api_name] = {
                        "input_vars": VARS['bonus_amount']["input_vars"],
                        "output_vars": [output_var],
                    }
                    # check if the input_vars are already in the memory, if not add to the missing_vars
                    for var, use in self.apis[api_name]["input_vars"].items():
                        if self.chat_session.user_data and (not self.chat_session.user_data.has_data(var)):
                            self.missing_vars[var] = use

                # if the api is already in the list, append the output_vars
                elif output_var not in self.apis[api_name]["output_vars"]:
                    self.apis[api_name]["output_vars"].append(output_var)


        print("+++++++++++++++ DATA +++++++++++++++")
        print(self.chat_session.user_data.to_str()) # type: ignore
        print("++++++++++++++++++++++++++++++++++++")
            

    async def generate_counter_queries(self):

        if self.missing_vars:

            print("Missing variables:", self.missing_vars.keys())
            input_vars = "\n".join([f"{key} : {value}" for key, value in self.missing_vars.items()])
            llm_query = f"User query: {self.conversation.SAQ} \n Query Intent: {self.conversation.intent} \n Missing variables: \n{input_vars}"
            response = await self.llm_call(llm_query, use="get_missing_vars")
            

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
        response: Dict[str, Any] = await self.llm_call(llm_query, use="api_response_generation")

        payload = BotResponsePayload(bot_response=Response(text=response["response"]))

        return payload
