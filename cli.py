import sys

from packets import (
    PacketType,
    WebSocketPacket,
    CounterQueryPayload,
    UserQueryPayload,
    BotResponsePayload,
    RAGPayload,
    ResponseFeedbackPayload,

    UserDataPayload,
    UserData, 
    Query,
    Message,
    Response,
    APIData
)

from main_cli import endpoint

from typing import Union, Any, Dict, List
import json
import asyncio



# Initialize session state for maintaining state across interactions
selected_path: List[Any] = []
chat_history: List[Any]= []
query_type = "main"

docs: List[Any] = []

send_user_data = False

last_payload = None

# HR tree structure
hr_tree: Dict[str, Any] = json.load(open("files\\ui_tree_data.json"))


# CLI Functions
def display_menu():
    global selected_path

    # Start at the top of the menu tree
    current_menu: Union[Dict, List] = hr_tree["Main Menu"]
    for path in selected_path:
        current_menu = current_menu[path] if isinstance(current_menu, dict) else current_menu

    # Display the full path of the current selection
    print("\nCurrent Selection Path: > " + " > ".join(selected_path) if selected_path else "Main Menu")

    # Display options for the current menu
    print("\nOptions:")
    if isinstance(current_menu, dict):
        for key in current_menu.keys():
            print(f"- {key}")
    elif isinstance(current_menu, list):
        for item in current_menu:
            print(f"- {item}")
    else:
        print("Invalid menu structure")

    # Provide a "Back" option to go to the previous level
    if selected_path:
        print("- Back")


def navigate_menu():
    global selected_path

    while True:
        display_menu()
        user_input = input("Enter your choice: ").strip()

        if user_input.lower() == "back" and selected_path:
            selected_path.pop()
        elif user_input in hr_tree["Main Menu"] or (selected_path and user_input in hr_tree["Main Menu"].get(selected_path[-1], {})):
            selected_path.append(user_input)
        else:
            print("Invalid option. Please try again.")
        
        if selected_path and isinstance(hr_tree["Main Menu"][selected_path[-1]], list):
            break

async def initiate_connection():
    global send_user_data
    if not send_user_data:
        send_user_data = True
        print("Creating new client...")
        packet = WebSocketPacket(
            packet_type=PacketType.USER_DATA,
            session_id="123",
            payload=UserDataPayload(
                user_data=UserData(
                    user_id="1234",
                    user_name="Siddhesh Dosi",
                    user_email="dosisiddhesh@alumni.iitgn.ac.in",
                    api= APIData(
                        input_data={}, output_data={}, dynamic_data={}
                    ),
                    user_metadata={}
                )
            )
        )
        await endpoint(packet)


async def main():
    global query_type, last_payload

    await initiate_connection()

    while True:
        # print("\nWelcome to the HR ChatBot CLI")
        # print("1. Navigate HR options")
        # print("2. Ask a question")
        # print("3. Exit")

        # choice = input("Enter your choice: ").strip()
        choice = "2"

        if choice == "1":
            navigate_menu()
        elif choice == "2":
            user_input = input("Ask me anything: ").strip()
            chat_history.append({"role": "user", "content": user_input})

            if query_type == "main":
                payload = {
                    "packet_type": "user_query",
                    "session_id": "123",
                    "conversation_id": "456",
                    "payload": {
                        "query": {"text": user_input},
                        "query_domain": " > ".join(selected_path)
                    }
                }
                payload = WebSocketPacket(**payload)
                response = await endpoint(payload)
                last_payload = response
            elif query_type == "counter":
                last_payload.payload["user_response"] = {"text": user_input}
                response = await endpoint(last_payload)
                last_payload = response

            if response.packet_type == "BOT_RESPONSE":
                print("Bot Response:", response.payload["bot_response"]["text"])
                query_type = "main"
            elif response.packet_type == "COUNTER_QUERY":
                print("Counter Query:", response.payload["counter_query"]["text"])
                query_type = "counter"
            elif response.packet_type == "RAG_DOCUMENTS":
                print("Bot Response:", response.payload["bot_response"]["text"])
                docs.clear()
                docs.extend([
                    {"page_content": doc.content, "metadata": doc.metadata}
                    for doc in response.payload["documents"]
                ])
                query_type = "main"

        elif choice == "3":
            print("Exiting HR ChatBot. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    asyncio.run(main())
