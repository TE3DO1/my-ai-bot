import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="🤖")

st.title("🤖 Ask T-Pire")

# Check for API key in Streamlit Secrets, or let user type it in sidebar
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("👈 Please enter your Gemini API Key in the left sidebar to start chatting.")
        st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=api_key)

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

    # Format history for Gemini
    contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a smart, helpful personal AI assistant.",
                        temperature=0.7,
                    )
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Error: {e}")
