from typing import List, Tuple, Dict, Any
import uuid


from utils.llm import LLMAgent

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

from pydantic import BaseModel
from openai import OpenAI
client = OpenAI()

import yaml
VARS = yaml.safe_load(open("utils\\api_info.yaml", "r"))


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: List[str] = []


class APIAgent(Agent):
    input_vars: Dict[str, str] = {}
    output_vars: List[str] = []
    api_use_case: str = ""
    api_url: str = ""

    missing_vars: Dict[str, str] = {}

class Chat(LLMAgent):
    def __init__(self, chat_session: ChatSession):
        print("Chat __init__")
        self.chat_session: ChatSession = chat_session
        self.conversation: Any = None

    async def get_chat_session(self) -> ChatSession:
        return self.chat_session
    
class APIBackend(Chat):
    def __init__(self):  # type: ignore
        print("APIBackend __init__")
        self.counter_queries: List[CounterQueryPayload] = []
        self.missing_vars: Dict[str, str] = {}
        self.apis: Dict[str, Dict[str, Any]] = {}  # {api_name: {"input_vars": [], "output_vars": []}}

    async def detect_relevant_vars(self) -> Dict[str, Any]:
        # TODO: Get the relevant variables from the LLM model
        output_vars: str = "\n".join([f"{key} : {value['use']}" for key, value in VARS.items() if value['use']])
        llm_query: str = f"Query : {self.conversation.SAQ} \n Query Intent: {self.conversation.intent} \n Variables: {output_vars}"
        relevant_vars = await self.llm_call(llm_query, use="detect_relevant_vars")
        return relevant_vars


    async def resolve_api_dependencies(self): # type: ignore
        # TODO: Find the missing variables and update the memory

        relevant_vars: Dict[str, Any] = await self.detect_relevant_vars() 
        for slave_query in relevant_vars:
            for output_var in relevant_vars[slave_query]:
                api_name: str = VARS[output_var]["api_to_be_called"]
                # if a new api is found
                if api_name not in self.apis:
                    self.apis[api_name] = {
                        "input_vars": VARS['bonus_amount']["input_vars"],
                        "output_vars": [output_var],
                    }
                    # check if the input_vars are already in the memory, if not add to the missing_vars
                    for var, use in self.apis[api_name]["input_vars"].items():
                        if self.chat_session.user_data and (not self.chat_session.user_data.has_data(var)):
                            self.missing_vars[var] = use

                # if the api is already in the list, append the output_vars
                elif output_var not in self.apis[api_name]["output_vars"]:
                    self.apis[api_name]["output_vars"].append(output_var)


        print("+++++++++++++++ DATA +++++++++++++++")
        print(self.chat_session.user_data.to_str()) # type: ignore
        print("++++++++++++++++++++++++++++++++++++")
            

    async def generate_counter_queries(self):

        if self.missing_vars:

            print("Missing variables:", self.missing_vars.keys())
            input_vars = "\n".join([f"{key} : {value}" for key, value in self.missing_vars.items()])
            llm_query = f"User query: {self.conversation.SAQ} \n Query Intent: {self.conversation.intent} \n Missing variables: \n{input_vars}"
            response = await self.llm_call(llm_query, use="get_missing_vars")
            

            self.counter_queries = [CounterQueryPayload(
                counter_query_id=i,
                counter_query=Query(text=subquery[1]),
                user_response=Response(text=""),
                query_variable=subquery[0],
            ) for i, subquery in enumerate(response.items())]


    async def update_memory(self, subquery: str, keyword: str, user_response: str):
        input_vars = "\n".join([f"`{key} : {value}`" for key, value in self.missing_vars.items()])
        llm_query = f"Query: {subquery} \nkeyword: {keyword} \nValue: {user_response}\nList of Variables: {input_vars}"
        response: Dict[str, str] = await self.llm_call(llm_query, use="extract_vars")
    
        self.chat_session.user_data.api.input_data.update(response) # type: ignore
        self.chat_session.chat_history.append(Message(content=user_response, sender="user", metadata={"type": "counter_response"})) # type: ignore

    async def execute_apis(self):
        # TODO: Execute the APIs and update the memory with the output vars
        for api_name in self.apis:
            api_response: Dict[str, Any] = tools[api_name](**self.chat_session.user_data.get_all_data()) # type: ignore
            self.chat_session.user_data.api.output_data.update(api_response) # type: ignore


class ChatBotBackend(Chat):
    def __init__(self, vector_db: MarkdownVectorDB):
        print("ChatBotBackend __init__")
        self.vector_db: MarkdownVectorDB = vector_db

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


class ENGINE(ChatBotBackend, APIBackend):
    def __init__(self, session_id: str) -> None:
        # Initialize the base Chat class once
        print("ENGINE __init__")
        Chat.__init__(self, chat_session=ChatSession(session_id=session_id))
        
        APIBackend.__init__(self)
        ChatBotBackend.__init__(self, vector_db=MarkdownVectorDB())
        # super().__init__(vector_db=MarkdownVectorDB(), chat_session=ChatSession(session_id=session_id))

    async def set_user_data(self, payload: UserDataPayload) -> None:
        print("Setting user data...")
        self.chat_session.user_data = payload.user_data.model_copy()
        print("User data updated : ", self.chat_session.user_data)

        
    async def initiate_conversation(self, payload: UserQueryPayload) -> None:
        print("Initiating conversation...")
        self.conversation: Conversation = Conversation(
            query_data = payload,
            SAQ = "",
            intent = "",
            counter_queries=[],
            bot_responses=[],
            rag_responses=None,
            related_questions=[],
            response_feedback=[],
        )
        self.missing_vars = {}
        print("Conversation initiated...")
        print("Conversation data: ", self.conversation.model_dump())
        print("Chat session data: ", self.chat_session.model_dump())


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
        
        await self.SAQ_and_intent_generator()

        await self.resolve_api_dependencies()

        await self.generate_counter_queries()

        return await self.gather_and_generate_response()


    async def gather_and_generate_response(self) -> WebSocketPacket:

        payload_type = None
        payload = None
        
        if len(self.counter_queries) > 0:
            counter_query_payload: CounterQueryPayload = self.counter_queries.pop(0)
            # update chat session with the current counter query in self.chat_session
            self.chat_session.chat_history.append(Message(content=counter_query_payload.counter_query.text, sender="bot", metadata={"type": "counter_query"})) # type: ignore

            payload_type = PacketType.COUNTER_QUERY
            payload = counter_query_payload

        else:
            print("+++++++++++++++++++++ DATA ++++++++++++++++++++++++")
            print(f"{self.chat_session.user_data.to_str()}") # type: ignore
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++")

            await self.execute_apis()
            response_type, response, rag_documents = await self.api_evaluator()

            if response_type == "direct":
                bot_response = BotResponsePayload(bot_response=Response(text=response))
                self.chat_session.chat_history.append(Message(content=response, sender="bot", metadata={"type": "bot_response"})) # type: ignore

                payload_type = PacketType.BOT_RESPONSE
                payload = bot_response

            elif response_type == "rag":
                rag_documents_payload = RAGPayload(bot_response=Response(text=response), documents=rag_documents)
                self.conversation.rag_responses = rag_documents_payload 
                self.chat_session.chat_history.append(Message(content=response, sender="bot", metadata={"type": "rag_response"})) # type: ignore

                payload_type = PacketType.RAG_DOCUMENTS
                payload = rag_documents_payload

            else:
                bot_response = BotResponsePayload(bot_response=Response(text="No valid response type found"))
                self.chat_session.chat_history.append(Message(content="No valid response type found", sender="bot", metadata={"type": "bot_response"})) # type: ignore
                payload_type = PacketType.BOT_RESPONSE
                payload = bot_response

        return WebSocketPacket(
            packet_type=payload_type,
            session_id=self.chat_session.session_id,
            conversation_id=None,
            payload=payload
        )

