import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Ask T-Pire", page_icon="⚡", layout="centered")

st.title("⚡ Ask T-Pire")

# Check for API key in Secrets or sidebar
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("👈 Please enter your Gemini API Key in the left sidebar to start chatting.")
        st.stop()

# 1. Reuse client connection
@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User chat input
if prompt := st.chat_input("Ask T-Pire anything..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Only send the last 6 messages to keep latency minimal
    recent_messages = st.session_state.messages[-6:]
    contents = []
    for m in recent_messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    # 3. Stream output with Thinking Mode turned OFF
    with st.chat_message("assistant"):
        def response_generator():
            stream = client.models.generate_content_stream(
                model="gemini-3.8-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction="You are T-Pire. Be brief, direct, and conversational.",
                    temperature=0.6,
                    # Disables internal reasoning pause for near-instant first token
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                )
            )
            for chunk in stream:
                if chunk.text:
                    yield chunk.text

        full_reply = st.write_stream(response_generator)
        st.session_state.messages.append({"role": "assistant", "content": full_reply})
