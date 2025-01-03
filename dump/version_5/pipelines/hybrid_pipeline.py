from agents.api import APIAgent
from agents.data import DATAAgent
from agents.rag import RAGAgent
from packets import (
    ChatSession,
    Conversation,
    CounterQueryPayload,
    BotResponsePayload,
    RAGPayload,
    PacketType,
    Response
)
from typing import List, Tuple, Dict, Any
import uuid

import yaml


class HybridPipeline(APIAgent, DATAAgent, RAGAgent):
    def __init__(self, chat_session: ChatSession, conversation: Conversation):
        self.chat_session   = chat_session
        self.conversation   = conversation

    async def run(self)-> Tuple[str, CounterQueryPayload | BotResponsePayload | RAGPayload]:
        relevant_vars: Dict[str, Any] = await self.detect_relevant_vars() 
        await self.resolve_api_dependencies(relevant_vars)

        await self.generate_counter_queries()

        return await self.continue_run()

    async def continue_run(self)-> Tuple[str, CounterQueryPayload | BotResponsePayload | RAGPayload]:
        count_query_payload: CounterQueryPayload | None= await self.resolve_counter_queries()

        if count_query_payload: # counter queries are pending...
            return (PacketType.COUNTER_QUERY, count_query_payload)
        
        await self.execute_apis()
        # api_response_payload: BotResponsePayload = await self.api_response_generation()
        response = await self.api_evaluator()

        if response["response_type"] == "direct":  
            api_response_payload = BotResponsePayload(bot_response=Response(text=response["response"]))
            return (PacketType.API_RESPONSE, api_response_payload)
        
        elif response["response_type"] == "rag":
            query = f"Query: {self.conversation.SAQ}\n User-Intent: {self.conversation.intent}\n Base-Response: {response['response']}"
            rag_response, rag_documents = await self.call_rag_agent(query=query)

            rag_payload = RAGPayload(bot_response=Response(text=rag_response), documents=rag_documents)
            return (PacketType.RAG_RESPONSE, rag_payload)
        
        else:
            return (PacketType.ERROR, BotResponsePayload(bot_response=Response(text="Error in API evaluation")))

