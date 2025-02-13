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
    Message,
    PipelineSchema,
    ChatResponsePayload
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
EXEC_APIS = yaml.safe_load(open("files\\api_info.yaml", "r"))
EXEC_API_STR: str = "\n".join([f"{key} : {value['use']}" for key, value in EXEC_APIS.items() if value['use']])

# print("--------------------------")
# print(DATAPipeline.mro())
# print(APIPipeline.mro())
# print(RAGPipeline.mro())
# print(HybridPipeline.mro())
# print(ChatBotBackend.mro())
# print("--------------------------")


class PipelineHandler(LLMAgent):
    
    def __init__(self):
        self.pipeline: Any = None
        
    async def detect_pipeline(self, chat_session: ChatSession, conversation : Conversation) :

        llm_query =    f"Query: {conversation.SAQ} \n" + f"Intent: {conversation.intent} \n" +\
                            f"Executable APIs: {EXEC_API_STR}" #+\
                            # f"DB Data: {self.output_vars} \n" +\
    
        response = await self.llm_call(query=llm_query, use="pipeline_api_rag")
        if response['pipeline'] ==  "EXEC_API":
            self.pipeline = APIPipeline(chat_session=chat_session, conversation=conversation)
        elif response['pipeline'] == "RAG":
            self.pipeline = RAGPipeline(chat_session=chat_session, conversation=conversation)
        # elif response['pipeline'] == "DB_DATA":
            # self.pipeline = DATAPipeline(chat_session=chat_session, conversation=conversation)
        # elif response['pipeline'] == "HYBRID":
            # self.pipeline = HybridPipeline(chat_session=chat_session, conversation=conversation)
        # else:
            # self.pipeline = ChatBotBackend(vector_db=MarkdownVectorDB(), chat_session=chat_session, conversation=conversation)
        
        return self.pipeline
    
    async def get_orchestrator_flow(self, chat_session: ChatSession, conversation: Conversation) -> Tuple[str, Any]:

        llm_query =    f"Query: {conversation.SAQ} \n" + f"Intent: {conversation.intent} \n" +\
                            f"Executable APIs: {EXEC_API_STR}" #+\
                            # f"DB Data: {self.output_vars} \n" +\
    
        response = await self.llm_call(query=llm_query, use="get_orchestrator_flow")
        return response['pipeline'], response['response']
        
        
class ENGINE(Chat, PipelineHandler):
    def __init__(self, session_id: str) -> None:
        # Initialize the base Chat class once
        print("ENGINE __init__")
        self.chat_session = ChatSession(session_id=session_id, chat_history=[])
        # self.chat_session.chat_history = []
        self.pipeline: PipelineSchema
    

    async def set_user_data(self, payload: UserDataPayload) -> None:
        print("Setting user data...")
        self.chat_session.user_data = payload.user_data.model_copy()
        print("User data updated : ", self.chat_session.user_data)


    async def chit_chat_detector(self, query: str, history: str) -> Tuple[bool, Any]:
        llm_query = f"Query: {query}\nChat history: {history}"
        response = await self.llm_call(llm_query, use="chitchat")
        if response["response_type"] == "1" or response["response_type"] == 1:
            return True, response["response"]
        return False, None
    

    async def SAQ_and_intent_generator(self, chat_history: str)-> tuple[str, str]:

        llm_query = (
                ("User query: " + self.conversation.query_data.query.text  + "\n") +
                ("Query-Category: " + self.conversation.query_data.query_domain + " \n" if self.conversation.query_data.query_domain else "") +
                ("Chat history: " + chat_history)
            )
        
        response = await self.llm_call(llm_query, use="saq_and_intent")

        return response["intent"], response["saq"]


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
                
        intent,  saq = await self.SAQ_and_intent_generator(chat_history)
        
        self.conversation.intent = intent
        self.conversation.SAQ = saq
    
        self.pipeline: PipelineSchema = await self.detect_pipeline(chat_session=self.chat_session, conversation=self.conversation)
        print("Pipeline detected: ", self.pipeline.__class__.__name__)
        payload_type, payload = await self.pipeline.run()  
        
        return await self.process_packet(payload_type, payload)


    async def gather_and_generate_response(self, subquery: str, keyword: str, user_response: str) -> WebSocketPacket:
        input_vars = "\n".join([f"`{key} : {value}`" for key, value in self.missing_vars.items()])
        llm_query = f"Query: {subquery} \nkeyword: {keyword} \nValue: {user_response}\nList of Variables: {input_vars}"
        response: Dict[str, str] = await self.llm_call(llm_query, use="extract_vars")
    
        self.chat_session.user_data.api.input_data.update(response) # type: ignore
        self.chat_session.chat_history.append(Message(content=user_response, sender="user", metadata={"type": "counter_response"})) # type: ignore

        payload_type, payload = await self.pipeline.continue_run()  
        return await self.process_packet(payload_type, payload)
    

    async def process_packet(self, payload_type:str, payload: ChatResponsePayload) -> WebSocketPacket:
        response: str = ""
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

        if payload_type != PacketType.ERROR:
            self.chat_session.chat_history.append(Message(content=response, sender="bot", metadata={"type": payload_type})) # type: ignore

        return WebSocketPacket(
            packet_type=payload_type,
            session_id=self.chat_session.session_id,
            conversation_id=None,
            payload=payload
        )

