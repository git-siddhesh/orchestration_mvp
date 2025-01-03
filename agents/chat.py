from typing import List, Tuple, Dict, Any
import uuid

from packets import *

from utils.call_api_hr import *
from utils.create_vdb_data import MarkdownVectorDB



from agents.base import Chat

class ChatBotBackend(Chat):
    def __init__(self, vector_db: MarkdownVectorDB, chat_session, conversation):
        print("ChatBotBackend __init__")
        self.vector_db: MarkdownVectorDB = vector_db
        self.chat_session   = chat_session
        self.conversation   = conversation

    async def chit_chat_detector(self, query: str, history: str) -> Tuple[bool, Any]:
        llm_query = f"Query: {query}\nChat history: {history}"
        response = await self.llm_call(llm_query, use="detect_chit_chat")
        if response["response_type"] == "1" or response["response_type"] == 1:
            return True, response["response"]
        return False, None

    async def SAQ_and_intent_generator(self):

        query = self.conversation.query_data.query.text
        chat_history = self.chat_session.fetch_history()
        query_category = self.conversation.query_data.query_domain
        # llm_query:str = ( f"User query: {query}\n" \
        #                   f"{('Query-Category: {query_category} \n' if query_category else '')}" \
        #                   f"Chat history: {chat_history}"
        # )

        llm_query = f"User query: {query}\nChat history: {chat_history}"
        response = await self.llm_call(llm_query, use="generate_SAQ_and_intent")

        self.conversation.intent = response["intent"]
        self.conversation.SAQ = response["saq"]


    async def api_evaluator(self) -> Tuple[str, str, Any]:
        """
        A decision maker that evaluates the API responses and decides the next course of action.
        1. Return the final response to the user as it is.
        2. Humanize the response using LLMatic transformation.
        3. Use these information and pass to RAG agent to generate more analytical response from the DOCUMETNS.
        """
        
        api_data= self.chat_session.user_data.to_str(data_type="output")  # type: ignore
        meta_data = self.chat_session.user_data.to_str(data_type="meta")  # type: ignore
        var_data = f"{api_data} {meta_data}"
        
        llm_query: str = f"query: {self.conversation.SAQ}\n User-Intent: {self.conversation.intent}\n Available data: {var_data}"
        response: Dict[str, Any] = await self.llm_call(llm_query, use="api_evaluator")

        if response["response_type"] == "direct":
            return ("direct", response["response"], None)
        
        if response["response_type"] == "rag":
            query = f"Query: {self.conversation.SAQ}\n User-Intent: {self.conversation.intent}\n Base-Response: {response['response']}"
            rag_response = await self.call_rag_agent(query=query)
            return ("rag", rag_response[0], rag_response[1])

        return ("UNKNOWN", "No valid response type found", None)
    
    async def call_rag_agent(self, query: str) -> Tuple[str, List[RAGDocument]]:
        self.vector_db.recreate_or_load_vector_db()

        docs = self.vector_db.retrieve_documents(query)
        rag_docs = [RAGDocument(document_id=str(i), content=doc.page_content, metadata=doc.metadata) for i, doc in enumerate(docs)] # type: ignore

        formatted_docs = "\n\n".join([ f"Document {i+1}:\nContent: {doc.page_content}" for i, doc in enumerate(docs)])
        rag_query = f"{query}\n\nRetrieved documents: {formatted_docs}"
        response = await self.llm_call(rag_query, use="rag")

        return response["response"], rag_docs
    
    async def run(self)-> Tuple[str, Any]:
        return "ChatBotBackend", "ChatBotBackend"