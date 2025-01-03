from typing import List, Tuple, Dict, Any, Union, Annotated
import uuid

from packets import (
    ChatSession,
    Conversation,
    UserQueryPayload,
    CounterQueryPayload,
    BotResponsePayload,
    RAGPayload,
    RAGDocument,
    WebSocketPacket,
    PacketType,
    Response,
    UserDataPayload,
    Query,
    Message
)

from utils.call_api_hr import *
from utils.create_vdb_data import MarkdownVectorDB
from agents.base import Chat
from agents.chat import ChatBotBackend

from pipelines.data_extract_pipeline import DATAPipeline
from pipelines.api_extract_pipeline import APIPipeline
from pipelines.rag_pipeline import RAGPipeline
from pipelines.hybrid_pipeline import HybridPipeline

from utils.llm import LLMAgent


import yaml
VARS = yaml.safe_load(open("utils\\api_info.yaml", "r"))
DATA_VARS = VARS['DATA_EXTRACT']
EXEC_APIS = VARS['EXEC_APIS']

PipelineSchema = Annotated[
    Union[
        DATAPipeline,
        APIPipeline,
        RAGPipeline,
        HybridPipeline,
    ],
    "PipelineSchema"
]

print("--------------------------")
print(DATAPipeline.mro())
print(APIPipeline.mro())
print(RAGPipeline.mro())
print(HybridPipeline.mro())
print(ChatBotBackend.mro())

print("--------------------------")


class PipelineHandler(LLMAgent):

    output_vars: str = "\n".join([f"{key} : {value['use']}" for key, value in DATA_VARS.items() if value['use']])
    exec_apis: str = "\n".join([f"{key} : {value['use']}" for key, value in EXEC_APIS.items() if value['use']])
    
    def __init__(self):
        self.pipeline: Any = None

    async def SAQ_and_intent_generator(self, query: str, chat_history: str, query_category: str|None)-> tuple[str, str]:

        # llm_query:str = ( f"User query: {query}\n" \
        #                   f"{('Query-Category: {query_category} \n' if query_category else '')}" \
        #                   f"Chat history: {chat_history}"
        # )
        llm_query = (
                ("User query: " + query + "\n") +
                ("Query-Category: " + query_category + " \n" if query_category else "") +
                ("Chat history: " + chat_history)
            )
        

        # llm_query = f"User query: {query}\nChat history: {chat_history}"
        response = await self.llm_call(llm_query, use="generate_SAQ_and_intent")

        # self.conversation.intent = response["intent"]
        # self.conversation.SAQ = response["saq"]

        return response["intent"], response["saq"]
        
    async def detect_pipeline(self, chat_session: ChatSession, conversation : Conversation) :

        chat_history: str = chat_session.fetch_history()

        query: str = conversation.query_data.query.text
        query_category: str | None = conversation.query_data.query_domain     

        intent,  saq = await self.SAQ_and_intent_generator(query, chat_history, query_category)
        
        conversation.intent = intent
        conversation.SAQ = saq
        
        llm_query =    f"Query: {saq} \n" +\
                            f"Intent: {intent} \n" +\
                            f"DB Data: {self.output_vars} \n" +\
                            f"Executable APIs: {self.exec_apis}"
    
        response = await self.llm_call(query=llm_query, use="detect_pipeline")
        if response['pipeline'] == "DB_DATA":
            self.pipeline = DATAPipeline(chat_session=chat_session, conversation=conversation)
        elif response['pipeline'] ==  "EXEC_API":
            self.pipeline = APIPipeline(chat_session=chat_session, conversation=conversation)
        elif response['pipeline'] == "RAG":
            self.pipeline = RAGPipeline(chat_session=chat_session, conversation=conversation)
        elif response['pipeline'] == "HYBRID":
            self.pipeline = HybridPipeline(chat_session=chat_session, conversation=conversation)
        else:
            self.pipeline = ChatBotBackend(vector_db=MarkdownVectorDB(), chat_session=chat_session, conversation=conversation)
        
        return self.pipeline
        
        
class ENGINE(Chat, PipelineHandler):
    def __init__(self, session_id: str) -> None:
        # Initialize the base Chat class once
        print("ENGINE __init__")
        self.chat_session = ChatSession(session_id=session_id)
    

    async def set_user_data(self, payload: UserDataPayload) -> None:
        print("Setting user data...")
        self.chat_session.user_data = payload.user_data.model_copy()
        print("User data updated : ", self.chat_session.user_data)


    async def chit_chat_detector(self, query: str, history: str) -> Tuple[bool, Any]:
        llm_query = f"Query: {query}\nChat history: {history}"
        response = await self.llm_call(llm_query, use="detect_chit_chat")
        if response["response_type"] == "1" or response["response_type"] == 1:
            return True, response["response"]
        return False, None
    

    async def get_response(self) -> WebSocketPacket:

        query = self.conversation.query_data.query.text 
        chat_history = self.chat_session.fetch_history()

        status, greeting = await self.chit_chat_detector(query = query, history=chat_history)
        if status:
            playload =  BotResponsePayload(bot_response=Response(text=greeting, response_id=uuid.uuid4().hex))
            return WebSocketPacket(
                packet_type=PacketType.BOT_RESPONSE,
                session_id=self.chat_session.session_id,
                conversation_id=None,
                payload=playload
            )
      
    
        pipeline: PipelineSchema = await self.detect_pipeline(chat_session=self.chat_session, conversation=self.conversation)
        print("Pipeline detected: ", pipeline.__class__.__name__)
        payload_type, payload = await pipeline.run()  
        response = ""
        if payload_type == PacketType.BOT_RESPONSE:
            response = payload.bot_response.text

        elif payload_type == PacketType.COUNTER_QUERY:
            response = payload.counter_query.text

        elif payload_type == PacketType.RAG_RESPONSE:
            response = payload.bot_response.text
            
            self.conversation.rag_responses = payload

        elif payload_type == PacketType.API_RESPONSE:
            response = payload.bot_response.text


        else:
            payload = BotResponsePayload(bot_response=Response(text="No valid response type found"))
            payload_type = PacketType.ERROR

        print("ERROR", payload_type)
        if payload_type != PacketType.ERROR:
            self.chat_session.chat_history.append(Message(content=response, sender="bot", metadata={"type": payload_type})) # type: ignore

        return WebSocketPacket(
            packet_type=payload_type,
            session_id=self.chat_session.session_id,
            conversation_id=None,
            payload=payload
        )
            


        
