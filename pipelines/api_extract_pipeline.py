from typing import List, Tuple, Dict, Any
import uuid

from packets import PacketType, CounterQueryPayload, BotResponsePayload, ChatResponsePayload

from utils.call_api_hr import *

from agents.api import APIAgent

import yaml
VARS = yaml.safe_load(open("files\\api_info.yaml", "r"))




class APIPipeline(APIAgent):
    def __init__(self,chat_session, conversation):  # type: ignore
        super().__init__()
        self.chat_session   = chat_session
        self.conversation   = conversation


    async def run(self)-> Tuple[str, ChatResponsePayload]:

        relevant_vars: Dict[str, Any] = await self.detect_relevant_vars() 
        await self.resolve_api_dependencies(relevant_vars)

        await self.generate_counter_queries()

        return await self.continue_run()

    async def continue_run(self)-> Tuple[str, ChatResponsePayload]:
        if len(self.counter_queries) > 0: # counter queries are pending...
            count_query_payload: CounterQueryPayload = self.counter_queries.pop(0)
            return (PacketType.COUNTER_QUERY, count_query_payload)
        
        await self.execute_apis()
        api_response_payload: BotResponsePayload = await self.api_response_generation()
        return (PacketType.API_RESPONSE, api_response_payload)
    
  
##############################################
