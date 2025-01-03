from typing import Any, Dict, List, Tuple

import uuid

from packets import RAGDocument, PacketType, RAGPayload, Response, ChatSession, Conversation


from agents.rag import RAGAgent


class RAGPipeline(RAGAgent):
    def __init__(self, chat_session: ChatSession, conversation: Conversation):
        super().__init__()
        self.chat_session   = chat_session
        self.conversation   = conversation

    async def run(self) -> Tuple[str, RAGPayload]:
        self.SAQ = self.conversation.SAQ
        self.intent = self.conversation.intent
        self.base_response = self.conversation.base_response

        # rag_query = f"Query: {self.conversation.SAQ}\n User-Intent: {self.conversation.intent}\n Base-Response: {response['response']}"
        rag_query = f"Query: {self.SAQ}\n User-Intent: {self.intent}"
        if self.base_response:
            rag_query += f"\n Base-Response: {self.base_response}"

        rag_response, rag_documents = await self.call_rag_agent(query=rag_query)

        rag_payload = RAGPayload(bot_response=Response(text=rag_response), documents=rag_documents)

        return (PacketType.RAG_RESPONSE, rag_payload)
        # return ("rag", rag_response[0], rag_response[1])
    