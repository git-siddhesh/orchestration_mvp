from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime


class PacketType(str, Enum):
    """
    Enumeration for different types of packets.
    """
    USER_QUERY = "user_query"
    COUNTER_QUERY = "counter_query_response"
    BOT_RESPONSE = "bot_response"
    RAG_DOCUMENTS = "rag_documents"
    RELATED_QUESTIONS = "related_questions"
    RESPONSE_FEEDBACK = "response_feedback"


class Message(BaseModel):
    """
    Represents a single message in the context of a query or response.
    """
    sender: str = Field(..., description="The sender of the message ('user', 'bot', or 'system').")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the message.")
    content: str = Field(..., description="The content of the message.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata related to the message.")

class Query(BaseModel):
    """
    Represents a query from the user/Bot.
    """
    query: str = Field(..., description="The query text.")
    query_id: Optional[str] = Field(default=None, description="Unique identifier for the query.")

class Response(BaseModel):
    """
    Represents a response from the bot.
    """
    response: str = Field(..., description="The response text.")
    response_id: Optional[str] = Field(default=None, description="Unique identifier for the response.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata related to the response.")

class RAGDocument(BaseModel):
    """
    Represents a document in a Retrieval-Augmented Generation (RAG) context.
    """
    document_id: str = Field(..., description="Unique identifier for the document.")
    content: str = Field(..., description="Content of the document.")
    source: Optional[str] = Field(default=None, description="Source of the document.")
    confidence: Optional[float] = Field(default=None, description="Confidence score for the document (if applicable).")

class RelatedQuestions(BaseModel):
    """
    Represents a related question for the user's query.
    """
    question: List[Query] = Field(..., description="The related question.")
    relevance_score: Optional[List[float]] = Field(default=None, description="Relevance score for the question.")

#___________________________________________________________________________________
# PAYLOADS #########################################################################


class UserQueryPayload(BaseModel):
    """
    Payload for a user query with or without history.
    """
    query: Query = Field(..., description="The user's question.")
    query_domain: Optional[str] = Field(..., description="The domain of the user query.")
    chat_history: Optional[List[Message]] = Field(
        default=None, description="Optional conversation history if available."
    )


class CounterQueryPayload(BaseModel):
    """
    Payload for a counter-response query and response.
    Shared by the user and bot since we need to map the user response to the counter-query.
    """
    counter_query: Query = Field(..., description="The counter-response query.")
    user_response: Response = Field(..., description="The user's response to the counter-query.")


class BotResponsePayload(BaseModel):
    """
    Payload for the bot's response.
    """
    bot_response: Response = Field(..., description="The bot's response to the user query.")


class RAGDocumentsPayload(BaseModel):
    """
    Payload for Retrieval-Augmented Generation (RAG) documents.
    """
    documents: List[RAGDocument] = Field(..., description="List of RAG documents relevant to the query.")


class RelatedQuestionsPayload(BaseModel):
    """
    Payload for related questions.
    """
    related_questions: List[Query] = Field(..., description="List of related questions for the user's query.")


class ResponseFeedbackPayload(BaseModel):
    """
    Payload for feedback on bot responses.
    """
    response_id: str = Field(..., description="Unique identifier for the bot response.")
    feedback: int = Field(..., description="Feedback value (e.g., 1 for positive, 0 for negative).")
    query_id: Optional[str] = Field(..., description="Unique identifier for the user query.")

#___________________________________________________________________________________
# WEBSOCKET PACKET ################################################################

class WebSocketPacket(BaseModel):
    """
    Represents a packet sent or received over WebSocket.
    """
    packet_type: PacketType = Field(..., description="The type of the packet (e.g., user_query, bot_response).")
    session_id: str = Field(..., description="Unique identifier for the WebSocket session.")
    conversation_id: Optional[str] = Field(default=None, description="Optional unique identifier for the conversation.")
    payload: Union[
        "UserQueryPayload", # for server
        "CounterQueryPayload", # for server and client
        "BotResponsePayload", # for client
        "RAGDocumentsPayload", # for client
        "RelatedQuestionsPayload", # for client
        "ResponseFeedbackPayload" # for server
    ] = Field(..., description="The payload associated with the packet.")

    # @validator("session_id")
    # def validate_session_id(cls, value):
    #     if not value.strip():
    #         raise ValueError("Session ID must not be empty.")
    #     return value

