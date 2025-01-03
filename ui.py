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


import streamlit as st




# Initialize session state for maintaining state across interactions
if "selected_path" not in st.session_state:
    st.session_state.selected_path = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "query_type" not in st.session_state:
    st.session_state.query_type = "main"
if "docs" not in st.session_state:
    st.session_state.docs = []
if "send_user_data" not in st.session_state:
    st.session_state.send_user_data = False
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None

# HR tree structure
hr_tree = json.load(open("utils\\ui_tree_data.json"))


def display_menu():
    # Start at the top of the menu tree
    # current_menu may be list or dict

    current_menu: Union[Dict, List] = hr_tree["Main Menu"]
    for path in st.session_state.selected_path:
        current_menu: Any | Any = (
            current_menu[path] if isinstance(current_menu, dict) else current_menu
        )

    # Display the full path of the current selection as a flow of buttons in a single line
    st.markdown("### Current Selection Path:")

    # Display buttons on a single line using columns
    if st.session_state.selected_path:
        cols = st.columns(
            len(st.session_state.selected_path) * 2 - 1
        )  # We need 2 columns for each button + 1 for the arrow
        for i, path in enumerate(st.session_state.selected_path):
            with cols[i * 2]:  # Use every other column for buttons
                # Display each path as a disabled button in the corresponding column
                st.button(f"**{path}**", disabled=True)
            if i != len(st.session_state.selected_path) - 1:
                with cols[i * 2 + 1]:  # Use the columns between buttons for the arrows
                    st.markdown(
                        "<p style='font-size: 30px;'>→</p>", unsafe_allow_html=True
                    )  # Arrow

    else:
        st.button(
            "Main Menu", disabled=True
        )  # Show "Main Menu" if there's no selection

    # Display options for the current menu
    st.markdown("---")  # Separator
    if isinstance(current_menu, dict):
        st.markdown("### Select a Category:")
        for key in current_menu.keys():
            if st.button(key):
                st.session_state.selected_path.append(key)
                st.rerun()
    elif isinstance(current_menu, list):
        st.markdown("### Select an Option:")
        for item in current_menu:
            if item in st.session_state.selected_path:
                st.button(
                    item, disabled=True
                )  # Disable button if it has already been selected
            else:
                if st.button(item):
                    st.session_state.selected_path.append(
                        item
                    )  # Add the list item to the path
                    st.session_state.chat_history.append(
                        {
                            "role": "system",
                            "content": f"User selected: {' > '.join(st.session_state.selected_path)}",
                        }
                    )
                    st.rerun()

    else:
        st.error("Invalid menu structure")
    # Provide a "Back" button to go to the previous level
    if len(st.session_state.selected_path) > 0:
        if st.button("Back"):
            st.session_state.selected_path.pop()
            st.rerun()


def page_content():

    st.set_page_config(page_title="HR ChatBot", layout="wide")

    # Sidebar for settings and document rendering
    with st.sidebar:
        st.header("Settings")
        st.text("Customize chatbot behavior")
        st.header("Document Renderer")
        st.text("Display selected documents here.")
    # Main Chat UI
    st.title("HR ChatBot")
    st.subheader("Navigate HR options or ask anything.")

    # Display current menu
    display_menu()

    for message in st.session_state.chat_history:
        role, content = message["role"], message["content"]
        with st.chat_message(role):
            st.markdown(content)

    for i, doc in enumerate(st.session_state.docs):
        with st.sidebar:
            with st.expander(f"Document {i+1}"):
                st.write(doc['page_content'])
            with st.expander(f"Metadata {i+1}"):
                st.write(doc['metadata'])



async def initiate_connection():
    if st.session_state.send_user_data == False:
        st.session_state.send_user_data = True
        print("Creating new client")
        packet = WebSocketPacket(
                    packet_type='user_data',
                    session_id="123",
                    payload = UserDataPayload(
                                user_data=UserData(
                                    user_id="1234",
                                    user_name="siddhesh dosi",
                                    user_email= "dosisiddhesh@alumni.iitgn.ac.in",
                                    api = APIData(
                                        input_data={},
                                        output_data={},
                                        dynamic_data={}),
                                    user_metadata={}
                            )
                )
        )

        await endpoint(packet)


# Main Streamlit App
async def main():
    page_content()
    await initiate_connection()

    # Chat input using `st.chat_input`
    if user_input := st.chat_input("Ask me anything..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        if st.session_state.query_type == "main":
            payload = {
                "packet_type": "user_query",
                "session_id": "123",
                "conversation_id": "456",
                "payload": {
                    "query": {"text": user_input},
                    "query_domain": " > ".join(st.session_state.selected_path)
                }
            }
            payload = WebSocketPacket.model_validate(payload)
            response = await endpoint(payload)
            st.session_state.last_payload = response
            
        elif st.session_state.query_type == "counter":
            last_payload = st.session_state.last_payload
            last_payload.payload.user_response = Response(text=user_input)
            response = await endpoint(last_payload)
            st.session_state.last_payload = response



        print("****************************** Message received (client side) ******************************")
        print("Response", response.model_dump())

        text = ""
        if response.packet_type == PacketType.COUNTER_QUERY:
            text = response.payload.counter_query.text
            st.session_state.chat_history.append({"role": "assistant", "content": text})
            st.session_state.query_type = "counter"
        elif response.packet_type == PacketType.BOT_RESPONSE:
            text = response.payload.bot_response.text
            st.session_state.chat_history.append({"role": "assistant", "content": text})
            st.session_state.query_type = "main"
        elif response.packet_type == PacketType.RAG_DOCUMENTS:
            text = response.payload.bot_response.text
            st.session_state.chat_history.append({"role": "assistant", "content": text})
            st.session_state.docs = [{'page_content': doc.content, 'metadata': doc.metadata} for doc in response.payload.documents]
            st.session_state.query_type = "main"

        with st.chat_message("assistant"):
            st.markdown(text)
        

        st.rerun()


if __name__ == "__main__":
    asyncio.run(main())



