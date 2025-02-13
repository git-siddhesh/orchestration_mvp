from typing import Tuple

import uuid


from packets import PacketType, RAGPayload, Response, ChatSession, Conversation, ChatResponsePayload

from agents.rag import RAGAgent


class RAGPipeline(RAGAgent):
    def __init__(self, chat_session: ChatSession, conversation: Conversation):
        super().__init__()
        self.chat_session   = chat_session
        self.conversation   = conversation

    async def run(self) -> Tuple[str, ChatResponsePayload]:
        rag_query = f"Query: {self.conversation.SAQ}\n User-Intent: {self.conversation.intent}"
        if self.conversation.base_response:
            rag_query += f"\n Base-Response: {self.conversation.base_response}"

        rag_response, rag_documents = await self.call_rag_agent(query=rag_query)

        rag_payload = RAGPayload(bot_response=Response(text=rag_response), documents=rag_documents)

        return (PacketType.RAG_RESPONSE, rag_payload)
    