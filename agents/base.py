from typing import List, Tuple, Dict, Any

from utils.llm import LLMAgent

from packets import ChatSession, Conversation, UserQueryPayload
from pydantic import BaseModel

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: List[str] = []

class Chat(LLMAgent):
    # define class variables
    chat_session: ChatSession
    conversation: Conversation
    missing_vars: Dict[str, str]


    def __init__(self):
        print("Chat __init__")

    def initiate_conversation(self, payload: UserQueryPayload) -> None:
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

    def get_chat_session(self) -> ChatSession:
        return self.chat_session
    