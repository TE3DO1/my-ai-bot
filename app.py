import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="Ask T-Pire", page_icon="⚡", layout="centered")

st.title("⚡ Ask T-Pire (Vision & Solver)")

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

# ----------------- SIDEBAR: IMAGE UPLOADER -----------------
st.sidebar.header("📸 Picture Solver")
uploaded_file = st.sidebar.file_uploader(
    "Upload a picture (math, text, notes, forms)", 
    type=["jpg", "jpeg", "png", "webp"]
)

# Preview and prepare image if provided
image_part = None
if uploaded_file is not None:
    st.sidebar.image(uploaded_file, caption="Uploaded Picture", use_container_width=True)
    image_part = types.Part.from_bytes(
        data=uploaded_file.getvalue(),
        mime_type=uploaded_file.type
    )
    st.sidebar.info("💡 Type your question below, or type 'solve this' to solve the image.")

# ----------------- CONVERSATION MEMORY -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------- CHAT INPUT -----------------
if prompt := st.chat_input("Ask T-Pire anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build history context
    recent_messages = st.session_state.messages[-4:-1]
    contents = []
    
    # Add previous chat history
    for m in recent_messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    # Build current turn with image (if uploaded) and question
    current_parts = []
    if image_part:
        current_parts.append(image_part)
    current_parts.append(types.Part.from_text(text=prompt))
    contents.append(types.Content(role="user", parts=current_parts))

    # ----------------- STREAMING & AUTO-RETRY -----------------
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        max_retries = 3
        reply_text = ""

     SYSTEM_PROMPT = """
        You are T-Pire, a smart, fast, and helpful AI assistant and tutor with computer vision.

        CREATOR RULE:
        If anyone asks who created you, who made you, or who your developer is, you must proudly state that you were created by 17-year-old teenager Teodor Pimpirev! Never say you were made by Google.

        CAPABILITIES:
        - When an image is provided:
          1. Extract all text, equations, and questions accurately.
          2. Solve the problem step-by-step with clear explanations.
        - When chatting normally, be fast, witty, polite, and helpful.
        """

        for attempt in range(max_retries):
            try:
                with st.spinner("Analyzing image and solving..." if image_part else "Thinking..."):
                    stream = client.models.generate_content_stream(
                        model="gemini-3.5-flash-lite",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.4,  # Lower temperature for higher accuracy in problem solving
                            max_output_tokens=1500,
                        ),
                    )
                    
                    # Stream response word-by-word
                    for chunk in stream:
                        if chunk.text:
                            reply_text += chunk.text
                            message_placeholder.markdown(reply_text + "▌")
                    
                    message_placeholder.markdown(reply_text)
                    st.session_state.messages.append({"role": "assistant", "content": reply_text})
                    break

            except Exception as e:
                err_str = str(e)
                # Handle 503 traffic spikes automatically
                if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                else:
                    message_placeholder.warning("⚠️ Server busy right now. Please press Enter to ask again.")
                    break
