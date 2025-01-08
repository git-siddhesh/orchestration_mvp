from typing import List, Tuple, Dict, Any
import uuid

from packets import PacketType, CounterQueryPayload, BotResponsePayload

from utils.call_api_hr import *

from agents.data import DATAAgent

import yaml
VARS = yaml.safe_load(open("files\\api_info.yaml", "r"))




class DATAPipeline(DATAAgent):
    def __init__(self, chat_session, conversation):  # type: ignore
        super().__init__()
        self.chat_session   = chat_session
        self.conversation   = conversation
        # self.state = "predefined_queries"

    async def run(self)-> Tuple[str, CounterQueryPayload | BotResponsePayload]:
        print("DATAPipeline run")

        print("%% checking predefined queries vs generic queries")

        response = await self.detect_relevant_predefined_queries()
        await self.resolve_missing_variables(response['relevant_queries'])

        relevant_vars: Dict[str, Any] = await self.detect_relevant_vars() 
        await self.resolve_missing_variables(list(relevant_vars.keys()))

        await self.generate_counter_queries()

        return await self.continue_run()

    async def continue_run(self)-> Tuple[str, CounterQueryPayload | BotResponsePayload]:
        count_query_payload: CounterQueryPayload | None= await self.resolve_counter_queries()

        if count_query_payload: # counter queries are pending...
            return (PacketType.COUNTER_QUERY, count_query_payload)
        
        # if self.state == "predefined_queries":
        #     self.state = "generic_queries"
        #     return await self.run()

        await self.execute_apis()
        api_response_payload: BotResponsePayload = await self.api_response_generation()
        return (PacketType.BOT_RESPONSE, api_response_payload)
    
  
##############################################
