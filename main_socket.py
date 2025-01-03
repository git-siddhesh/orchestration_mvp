from typing import List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from version_3.packets import (
    WebSocketPacket, 
    PacketType,
    UserQueryPayload,
    CounterQueryPayload,
    ResponseFeedbackPayload,
    UserDataPayload,
    ErrorPayload
)


from version_3.backend import ChatBOT
from fastapi import WebSocket


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

    async def send_personal_message(self, message: WebSocketPacket, websocket: WebSocket):
        await websocket.send_json(message.model_dump())

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    session_id = str(id(websocket))  # Unique ID for each WebSocket connection

    bot = ChatBOT(session_id=session_id)

    try:
        while True:
            json_data: Any = await websocket.receive_json()
            packet: WebSocketPacket = WebSocketPacket.model_validate(json_data)

            print(f"Received packet: {json_data}")

            response = None 
            if isinstance(packet.payload, UserDataPayload):

                await bot.set_user_data(packet.payload)


            elif isinstance(packet.payload, UserQueryPayload):

                await bot.initiate_conversation(packet.payload)
            
                response: WebSocketPacket = await bot.get_response()

            elif isinstance(packet.payload, CounterQueryPayload):

                bot.conversation.counter_queries.append(packet.payload)

                response: WebSocketPacket = await bot.gather_and_generate_response()

            elif isinstance(packet.payload, ResponseFeedbackPayload):

                bot.conversation.reponse_feedback.append(packet.payload)

                response = WebSocketPacket(
                    packet_type=PacketType.RESPONSE_FEEDBACK,
                    session_id=session_id,
                    payload=packet.payload
                )

                # response = await bot.update_feedback(packet.payload)

            else:
                print("Error: Invalid payload type received.")
                print(packet.payload.model_dump())
                response = WebSocketPacket(
                    packet_type=PacketType.ERROR,
                    session_id=session_id,
                    payload=ErrorPayload(
                        error_code=400,
                        error_message="Invalid payload type received.",
                        error_stack=None
                    )
                )

            if response:
                await manager.send_personal_message(response, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Session {session_id} ended.")


# RUN UVICORN SERVER
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)