from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
from pydantic import ValidationError
from enum import Enum
from datetime import datetime

from packets import (
    WebSocketPacket, 
    PacketType,
    UserQueryPayload,
    CounterQueryPayload,
    ResponseFeedbackPayload
)

from backend import ChatBotBackend, ChatDB, RAGAgent

app = FastAPI()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket(path="/ws")
async def websocket_endpoint(websocket: WebSocket)-> None:
    await manager.connect(websocket=websocket)
    try:
        while True:
            # Wait for incoming message
            raw_data: str = await websocket.receive_text()

            try:
                json_data: Dict[Any, Any] = json.loads(raw_data)
                packet = WebSocketPacket(**json_data)

                # if packet.packet_type == PacketType.USER_QUERY:
                if isinstance(packet.payload, UserQueryPayload):
                    query_payload: UserQueryPayload = packet.payload  # This will be of type UserQueryPayload
                    
                    response = f"Received query: {query_payload.query}"

                # elif packet.packet_type == PacketType.COUNTER_QUERY:
                elif isinstance(packet.payload, CounterQueryPayload):
                    counter_payload: CounterQueryPayload = packet.payload
                    
                    response = f"Received counter-query and response: {counter_payload.counter_query}"
                
                # elif packet.packet_type == PacketType.RESPONSE_FEEDBACK:
                elif isinstance(packet.payload, ResponseFeedbackPayload):
                    feedback_payload: ResponseFeedbackPayload = packet.payload  # This will be of type RAGDocumentsPayload
                    print("Not implemented yet")
                    response = f"Received Feedback: {[feedback_payload.feedback]}"
                else:
                    response = "Unhandled packet type."

                # Send response
                await manager.send_personal_message(response, websocket)

            except ValidationError as e:
                # Handle validation errors from Pydantic
                error_message = f"Invalid packet format: {e.json()}"
                await manager.send_personal_message(error_message, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
