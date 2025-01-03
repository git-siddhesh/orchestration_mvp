from typing import List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from packets import (
    WebSocketPacket, 
    PacketType,
    UserQueryPayload,
    CounterQueryPayload,
    ResponseFeedbackPayload,
    UserDataPayload,
    ErrorPayload
)


from backend import ChatBOT

import uuid

session_id = str(uuid.uuid4())  # Unique ID for each WebSocket connection
bot = ChatBOT(session_id=session_id)

async def endpoint(packet: WebSocketPacket) -> WebSocketPacket | None:
    

    response = None

    print("****************************** Message received (Server-side) ******************************")
    print("Packet", packet.model_dump())
    # if isinstance(packet.payload, UserDataPayload):
    if packet.packet_type == PacketType.USER_DATA:
        print("User Data Payload")
        await bot.set_user_data(packet.payload) 

    # elif isinstance(packet.payload, UserQueryPayload):
    elif packet.packet_type == PacketType.USER_QUERY:

        await bot.initiate_conversation(packet.payload)
    
        response: WebSocketPacket = await bot.get_response()

    # elif isinstance(packet.payload, CounterQueryPayload):
    elif packet.packet_type == PacketType.COUNTER_QUERY:

        bot.conversation.counter_queries.append(packet.payload)

        await bot.update_memory(
            subquery=packet.payload.counter_query.text,
            keyword=packet.payload.query_variable,
            user_response=packet.payload.user_response.text
        )

        response: WebSocketPacket = await bot.gather_and_generate_response()

    # elif isinstance(packet.payload, ResponseFeedbackPayload):
    elif packet.packet_type == PacketType.RESPONSE_FEEDBACK:

        bot.conversation.response_feedback.append(packet.payload)

        response = WebSocketPacket(
            packet_type=PacketType.RESPONSE_FEEDBACK,
            session_id=session_id,
            payload=packet.payload
        )

    else:
        print("Error: Invalid payload type received.")

        # print the instance of the payload
        

        response = WebSocketPacket(
            packet_type=PacketType.ERROR,
            session_id=session_id,
            payload=ErrorPayload(
                error_code=400,
                error_message="Invalid payload type received.",
                error_stack=None
            )
        )

    # except Exception as e:
    #     print(e)
    #     response = WebSocketPacket(
    #             packet_type=PacketType.ERROR,
    #             session_id=session_id,
    #             payload=ErrorPayload(
    #                 error_code=400,
    #                 error_message="Invalid payload type received.",
    #                 error_stack=None
    #             )
    #         )
    # finally:
    if response:
        return response
