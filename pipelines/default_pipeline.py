from typing import Tuple

from packets import  PacketType,  Response, ChatSession, Conversation, BotResponsePayload


from agents.base import Chat


class DefaultPipeline(Chat):
    def __init__(self, chat_session: ChatSession, conversation: Conversation):
        super().__init__()
        self.chat_session   = chat_session
        self.conversation   = conversation

    async def run(self) -> Tuple[str, BotResponsePayload]:
        return (PacketType.ERROR, BotResponsePayload( bot_response=Response(text="Unable to process your request" )))
    