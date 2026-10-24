import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="Ask T-Pire", page_icon="⚡", layout="centered")

st.title("⚡ Ask T-Pire")

# ----------------- CREATOR & BEHAVIOR PROMPT -----------------
SYSTEM_PROMPT = """
You are T-Pire, a smart, fast, and helpful AI assistant with computer vision.

STRICT CREATOR RULE:
- ONLY state your creator if explicitly asked "Who created/made you?".
- If asked, state: "I was created by 17-year-old teenager Teodor Pimpirev!"
- For ALL other prompts: DO NOT mention Teodor Pimpirev or introduce yourself.

CAPABILITIES:
- If an image is provided, extract all text and solve it step-by-step.
- When chatting normally, answer questions directly, fast, and concisely.
""

# Check API Key
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("👈 Please enter your Gemini API Key in the sidebar.")
        st.stop()

# Reuse connection
@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# ----------------- SIDEBAR: VERSION SWITCHER -----------------
st.sidebar.header("⚙️ AI Version Switcher")

version_choice = st.sidebar.selectbox(
    "Choose AI Brain:",
    [
        "🧠 Smart Mode (T-Pire 2.0 tdi - Accurate & Math)",
        "⚡ Fast Mode (T-Pire 1.9 tdi - Ultra Speed)",
    ],
    index=0  # Defaults to Smart Mode for correct answers
)

# Set model and temperature based on user selection
if "Smart" in version_choice:
    selected_model = "gemini-3.8-flash"
    selected_temp = 0.2  # Precise & factual
    st.sidebar.caption("🎯 *Best for homework, math, coding, and precise reasoning.*")
else:
    selected_model = "gemini-3.5-flash-lite"
    selected_temp = 0.6  # Quick & conversational
    st.sidebar.caption("🚀 *Best for rapid chatting, quick ideas, and small talk.*")

st.sidebar.markdown("---")

# ----------------- SIDEBAR: PICTURE SOLVER -----------------
st.sidebar.header("📸 Picture Solver (Vision)")
uploaded_file = st.sidebar.file_uploader(
    "Upload a picture (math, notes, questions, forms)", 
    type=["jpg", "jpeg", "png", "webp"]
)

image_part = None
if uploaded_file is not None:
    st.sidebar.image(uploaded_file, caption="Uploaded Picture", use_container_width=True)
    image_part = types.Part.from_bytes(
        data=uploaded_file.getvalue(),
        mime_type=uploaded_file.type
    )
    st.sidebar.info("💡 Type 'solve this' or ask a question about the picture below.")

# ----------------- CHAT HISTORY -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------- CHAT INPUT -----------------
if prompt := st.chat_input("Ask T-Pire anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Conversation history context
    recent_messages = st.session_state.messages[-4:-1]
    contents = []

    for m in recent_messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    # Add current prompt and image (if attached)
    current_parts = []
    if image_part:
        current_parts.append(image_part)
    current_parts.append(types.Part.from_text(text=prompt))
    contents.append(types.Content(role="user", parts=current_parts))

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        max_retries = 3
        reply_text = ""

        for attempt in range(max_retries):
            try:
                spinner_text = "Solving..." if image_part else ("Thinking deeply..." if "Smart" in version_choice else "Typing fast...")
                with st.spinner(spinner_text):
                    stream = client.models.generate_content_stream(
                        model=selected_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=selected_temp,
                            max_output_tokens=2000,
                        ),
                    )
                    
                    for chunk in stream:
                        if chunk.text:
                            reply_text += chunk.text
                            message_placeholder.markdown(reply_text + "▌")

                    message_placeholder.markdown(reply_text)
                    st.session_state.messages.append({"role": "assistant", "content": reply_text})
                    break

            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                else:
                    message_placeholder.warning("⚠️ Server busy right now. Please press Enter to try again.")
                    break
