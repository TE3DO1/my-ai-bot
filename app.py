import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

st.set_page_config(page_title="Ask T-Pire", page_icon="⚡", layout="centered")

st.title("⚡ Ask T-Pire")

# Check for API key
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("👈 Please enter your Gemini API Key in the sidebar to start chatting.")
        st.stop()

# Cache client connection
@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask T-Pire anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Keep conversation context fast and short
    recent_messages = st.session_state.messages[-6:]
    contents = []
    for m in recent_messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    # Helper function to stream with thinking disabled
    def stream_model(model_name):
        return client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="You are T-Pire. Be brief, direct, and conversational.",
                temperature=0.6,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
        )

    # Generator with automatic fallback if Google is overloaded
    def safe_response_generator():
        try:
            # Try primary model
            stream = stream_model("gemini-3.8-flash")
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except APIError as e:
            # If 503 overloaded, immediately switch to the backup model
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                try:
                    backup_stream = stream_model("gemini-3.5-flash-lite")
                    for chunk in backup_stream:
                        if chunk.text:
                            yield chunk.text
                except Exception as backup_err:
                    yield f"⚠️ Google's servers are experiencing high traffic right now. Please try again in a few moments."
            else:
                yield f"⚠️ Error: {e}"

    with st.chat_message("assistant"):
        full_reply = st.write_stream(safe_response_generator)
        st.session_state.messages.append({"role": "assistant", "content": full_reply})
