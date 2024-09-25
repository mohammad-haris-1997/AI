import streamlit as st 
from langchain_core.messages import AIMessage, HumanMessage
from testt1 import main
import hydralit_components as hc

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="Streaming Bot")

st.title("Streaming Bot")

for message in st.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)
    else: 
        with st.chat_message("AI"):
            st.markdown(message.content)


user_query = st.chat_input("Your Message")

if user_query is not None and user_query.strip() != "":
    user_query = user_query.strip().lower()
    existing_response = None
    for i in range(len(st.session_state.chat_history) - 1, -1, -1):
        if isinstance(st.session_state.chat_history[i], HumanMessage) and st.session_state.chat_history[i].content.strip().lower() == user_query:
            if i + 1 < len(st.session_state.chat_history) and isinstance(st.session_state.chat_history[i + 1], AIMessage):
                existing_response = st.session_state.chat_history[i + 1].content
                break

    st.session_state.chat_history.append(HumanMessage(user_query))

    with st.chat_message("Human"):
        st.markdown(user_query)

    if existing_response: 

        with st.chat_message("AI"):
            st.markdown(existing_response)  
        
    else:
        with st.chat_message("AI"):
            with hc.HyLoader('<div class="custom-loader-message"><div style="font-size: 20px;">Please wait while the answer is being fetched...</div>', hc.Loaders.standard_loaders):   
                response_generator = main(user_query) 

                full_response = ""

                if hasattr(response_generator, '__iter__') and not isinstance(response_generator, str):
                    response_placeholder = st.empty()

                    for response in response_generator:  
                        full_response += response  
                        response_placeholder.markdown(full_response)  
                else:
                    st.markdown(response_generator)
                    full_response = response_generator

        # After receiving the full response, update the chat history
            st.session_state.chat_history.append(AIMessage(full_response))


