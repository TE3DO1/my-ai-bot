import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Ask T-Pire", page_icon="🤖")

st.title("🤖 Ask T-Pire")

# Check for API key
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("👈 Please enter your Gemini API Key in the left sidebar to start chatting.")
        st.stop()

# 1. SPEED BOOST: Cache the client so it reuses the connection
@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# Store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt input
if prompt := st.chat_input("Ask me anything..."):
    # Display user question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. SPEED BOOST: Only send the last 8 messages so prompt processing is instant
    recent_messages = st.session_state.messages[-8:]
    contents = []
    for m in recent_messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    # 3. SPEED BOOST: Stream text live word-by-word
    with st.chat_message("assistant"):
        def response_generator():
            stream = client.models.generate_content_stream(
                model="gemini-3.8-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction="You are T-Pire, a fast, sharp, and helpful AI assistant. Give concise and clear answers.",
                    temperature=0.7,
                )
            )
            for chunk in stream:
                if chunk.text:
                    yield chunk.text

        # st.write_stream renders words as they arrive in real time
        full_reply = st.write_stream(response_generator)
        st.session_state.messages.append({"role": "assistant", "content": full_reply})
