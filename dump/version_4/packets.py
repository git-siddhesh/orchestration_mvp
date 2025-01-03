from pydantic import BaseModel, Field, validator, root_validator, model_validator
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from datetime import datetime


class PacketType(str, Enum):
    """
    Enumeration for different types of packets.
    """
    USER_DATA = "user_data"
    USER_QUERY = "user_query"
    COUNTER_QUERY = "counter_query_response"
    BOT_RESPONSE = "bot_response"
    RAG_DOCUMENTS = "rag_documents"
    RELATED_QUESTIONS = "related_questions"
    RESPONSE_FEEDBACK = "response_feedback"
    ERROR = "error"


class Message(BaseModel):
    """
    Represents a single message in the context of a query or response.
    """
    sender: str = Field(..., description="The sender of the message ('user', 'bot', or 'system').")
    message_id: Optional[str] = Field(default=None, description="Unique identifier for the message.")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the message.")
    content: str = Field(..., description="The content of the message.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata related to the message. (e.g., type = 'bot' | 'user' | 'system')")

class Query(BaseModel):
    """
    Represents a query from the user/Bot.
    """
    text: str = Field(..., description="The query text.")
    query_id: Optional[str] = Field(default=None, description="Unique identifier for the query.")

class Response(BaseModel):
    """
    Represents a response from the bot.
    """
    text: str = Field(..., description="The response text.")
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
    metadata: Optional[Any] = Field(default=None, description="Additional metadata related to the document.")

class RelatedQuestions(BaseModel):
    """
    Represents a related question for the user's query.
    """
    question: List[Query] = Field(..., description="The related question.")
    relevance_score: Optional[List[float]] = Field(default=None, description="Relevance score for the question.")

class APIData(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    dynamic_data: Dict[str, Any] = Field(default_factory=dict)
    

class UserData(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    api: APIData = Field(default_factory=APIData)
    user_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    def populate_user_metadata(cls, values):
        # Access data from ValidationInfo
        if hasattr(values, 'data'):  # Check if it's a ValidationInfo object
            values = values.data
        
        # Populate user_metadata with default values
        user_metadata = values.get("user_metadata", {})
        user_metadata["user_id"] = values.get("user_id")
        user_metadata["user_name"] = values.get("user_name")
        user_metadata["user_email"] = values.get("user_email")
        values["user_metadata"] = user_metadata
        return values
    
    def to_str(self, data_type:str="") -> str:
        """
        Efficiently convert api_data to a string of key-value pairs.

        Parameters:
        ----------
        data_type : {"input", "output", "dynamic", "meta", ""}, optional
            The data type to convert to a string. If not specified, all data types are converted
            to a string. Default is "".

        Returns:
        -------
        string
            A string representation of the specified data type or all data types.
        """
        input_data = ", ".join(f"{k}: {v}" for k, v in self.api.input_data.items() if k and v)
        output_data = ", ".join(f"{k}: {v}" for k, v in self.api.output_data.items() if k and v)
        dynamic_data = ", ".join(f"{k}: {v}" for k, v in self.api.dynamic_data.items() if k and v)
        meta_data = ", ".join(f"{k}: {v}" for k, v in self.user_metadata.items() if k and v)

        if data_type == "input":
            return input_data
        elif data_type == "output":
            return output_data
        elif data_type == "dynamic":
            return dynamic_data
        elif data_type == "meta":
            return meta_data
        else:
            return f"I/P: {input_data}, \nO/P: {output_data}, \nDYN: {dynamic_data}, \nMETA: {meta_data}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UserData to a dictionary."""
        return {
            "input_data": self.api.input_data,
            "output_data": self.api.output_data,
            "dynamic_data": self.api.dynamic_data,
            "user_metadata": self.user_metadata
        }
    
    # check if some data is present in the api_data, user_metadata
    def has_data(self, key: str) -> bool:
        return key in self.api.input_data or key in self.api.output_data or key in self.api.dynamic_data or key in self.user_metadata

    def get_all_data(self) -> Dict[str, Any]:
        """Get all data from the UserData object."""
        return {
            **self.api.input_data,
            **self.api.output_data,
            **self.api.dynamic_data,
            **self.user_metadata
        }
#___________________________________________________________________________________
# PAYLOADS #########################################################################

class UserDataPayload(BaseModel):
    """
    Payload for user data.
    """
    user_data: UserData = Field(..., description="User data associated with the session.")

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
    counter_query_id: int = Field(..., description="Unique identifier for the counter-query.")
    counter_query: Query = Field(..., description="The counter-response query.")
    user_response: Optional[Response] = Field(None, description="The user's response to the counter-query.")
    query_variable: Optional[str] = Field(..., description="The variable associated with the counter-query.")

class BotResponsePayload(BaseModel):
    """
    Payload for the bot's response.
    """
    bot_response: Response = Field(..., description="The bot's response to the user query.")


class RAGPayload(BaseModel):
    """
    Payload for Retrieval-Augmented Generation (RAG) documents.
    """
    bot_response: Response = Field(..., description="The bot's response to the user query.")
    documents: Optional[List[RAGDocument]] = Field([], description="List of RAG documents relevant to the query.")


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

class ErrorPayload(BaseModel):
    """
    Payload for error messages.
    """
    error_code: int = Field(..., description="Error code associated with the error.")
    error_message: str = Field(..., description="Error message.")
    error_stack: Optional[List[Any]] = Field(default=None, description="Error stack trace (if available).")

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
        "UserDataPayload",
        "UserQueryPayload", # for server
        "CounterQueryPayload", # for server and client
        "BotResponsePayload", # for client
        "RAGPayload", # for client
        "RelatedQuestionsPayload", # for client
        "ResponseFeedbackPayload", # for server
        "ErrorPayload"
    ] = Field(..., description="The payload associated with the packet.")

    # @validator("session_id")
    # def validate_session_id(cls, value):
    #     if not value.strip():
    #         raise ValueError("Session ID must not be empty.")
    #     return value



class Conversation(BaseModel):
    query_data: UserQueryPayload = Field(..., description="The user's query data.")
    SAQ: str = Field(..., description="The user's query data.")
    intent: str = Field(..., description="The user's query data.")
    counter_queries: List[CounterQueryPayload] = Field(default=[], description="List of counter-queries and responses.")
    bot_responses: List[BotResponsePayload] = Field(default=[], description="List of bot responses.")
    rag_responses: Optional[RAGPayload] = Field(default=None, description="List of RAG responses.")
    related_questions: List[RelatedQuestionsPayload] = Field(default=[], description="List of related questions.")
    response_feedback: List[ResponseFeedbackPayload] = Field(default=[], description="List of response feedback.")
    
class ChatSession(BaseModel):
    session_id: str = Field(..., description="Unique identifier for the WebSocket session.")
    user_data: Optional[UserData] = Field(default=None, description="User data associated with the session.")
    chat_history: Optional[List[Message]] = Field(default=[], description="Conversation history for the session.")

    def fetch_history(self, n: int=-1, reverse: bool=True) -> str:
        """
        Fetch the last n messages from the chat history.
        """
        if n == -1:
            n = len(self.chat_history) # type: ignore
            
        chat_history = ""
        if self.chat_history: 
            for chat in self.chat_history[:n:-1 if reverse else 1]:
                chat_history += f'{getattr(chat, "sender", "Unknown")}: {chat.content}\n ' if chat.metadata else ""
        return chat_history
        


# response = WebSocketPacket(
#                     packet_type=PacketType.ERROR,
#                     session_id='123',
#                     payload=ErrorPayload(
#                         error_code=400,
#                         error_message="Invalid payload type received.",
#                         error_stack=None
#                     )
#                 )

# print(response)
# print(response.model_dump())
# k = response.model_dump()
# response3 = WebSocketPacket.model_validate(k)
# print(response3)

# json_packet = {'packet_type': 'user_query', 'session_id': '123', 'conversation_id': '456', 'payload': {'query': {'text': 'hi', 'query_id': None}, 'query_domain': '', 'chat_history': None}}

