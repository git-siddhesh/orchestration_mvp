from typing import List, Tuple, Dict, Any
import uuid

from packets import PacketType, CounterQueryPayload, BotResponsePayload

from utils.call_api_hr import *

from agents.api import APIAgent

import yaml
VARS = yaml.safe_load(open("utils\\api_info.yaml", "r"))




class APIPipeline(APIAgent):
    def __init__(self,chat_session, conversation):  # type: ignore
        super().__init__()
        self.chat_session   = chat_session
        self.conversation   = conversation


    async def run(self)-> Tuple[str, CounterQueryPayload | BotResponsePayload]:

        relevant_vars: Dict[str, Any] = await self.detect_relevant_vars() 
        await self.resolve_api_dependencies(relevant_vars)

        await self.generate_counter_queries()

        return await self.continue_run()

    async def continue_run(self)-> Tuple[str, CounterQueryPayload | BotResponsePayload]:
        count_query_payload: CounterQueryPayload | None= await self.resolve_counter_queries()

        if count_query_payload: # counter queries are pending...
            return (PacketType.COUNTER_QUERY, count_query_payload)
        
        await self.execute_apis()
        api_response_payload: BotResponsePayload = await self.api_response_generation()
        return (PacketType.API_RESPONSE, api_response_payload)
    
  
##############################################
