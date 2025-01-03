from agents.base import Agent, Chat
from packets import RAGDocument
from typing import List, Dict, Any, Tuple, Union, Optional
from utils.call_api_hr import *

from utils.create_vdb_data import MarkdownVectorDB

import yaml

VARS = yaml.safe_load(open("utils\\api_info.yaml", "r"))
vector_db = MarkdownVectorDB()

class RAGAgent(Chat):#, Agent):
    def __init__(self):

        self.vector_db: MarkdownVectorDB= vector_db    

    async def call_rag_agent(self, query: str ) -> Tuple[str, List[RAGDocument]]:
        self.vector_db.recreate_or_load_vector_db()

        docs = self.vector_db.retrieve_documents(query)
        rag_docs = [RAGDocument(document_id=str(i), content=doc.page_content, metadata=doc.metadata) for i, doc in enumerate(docs)] # type: ignore

        formatted_docs = "\n\n".join([ f"Document {i+1}:\nContent: {doc.page_content}" for i, doc in enumerate(docs)])
        rag_query = f"{query}\n\nRetrieved documents: {formatted_docs}"
        response = await self.llm_call(rag_query, use="rag")

        return response["response"], rag_docs
