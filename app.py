import streamlit as st
import time
import urllib.parse
from google import genai
from google.genai import types

st.set_page_config(page_title="Ask T-Pire", page_icon="⚡", layout="centered")

st.title("⚡ Ask T-Pire (Chat, Vision & Image Generator)")

# Check API Key
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("👈 Please enter your Gemini API Key in the sidebar.")
        st.stop()

# Reuse client connection
@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# ----------------- SIDEBAR: PICTURE SOLVER (VISION) -----------------
st.sidebar.header("📸 Picture Solver (Vision)")
uploaded_file = st.sidebar.file_uploader(
    "Upload a picture to read or solve", 
    type=["jpg", "jpeg", "png", "webp"]
)

image_part = None
if uploaded_file is not None:
    st.sidebar.image(uploaded_file, caption="Uploaded Picture", use_container_width=True)
    image_part = types.Part.from_bytes(
        data=uploaded_file.getvalue(),
        mime_type=uploaded_file.type
    )

st.sidebar.markdown("---")
st.sidebar.header("🎨 Free Image Generator")
st.sidebar.caption("Type `/image <description>` in chat to draw pictures instantly!")

# ----------------- CHAT HISTORY -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], caption=msg.get("caption", "Generated Image"))
        else:
            st.markdown(msg["content"])

# ----------------- HELPER FUNCTIONS -----------------
def is_image_request(text: str) -> bool:
    t = text.strip().lower()
    return (
        t.startswith("/image") or 
        t.startswith("/draw") or 
        t.startswith("generate an image") or 
        t.startswith("draw an image") or
        t.startswith("create an image") or
        t.startswith("draw a") or
        t.startswith("draw me")
    )

def extract_prompt(text: str) -> str:
    prefixes = [
        "/image", "/draw", "generate an image of", "generate an image",
        "create an image of", "create an image", "draw an image of",
        "draw a", "draw me an image of", "draw me", "draw"
    ]
    t_lower = text.strip().lower()
    for p in prefixes:
        if t_lower.startswith(p):
            return text.strip()[len(p):].strip(" :,-")
    return text.strip()

# ----------------- CHAT INPUT -----------------
if prompt := st.chat_input("Ask a question, upload a picture, or type '/image a dog'..."):
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # CASE 1: GENERATE AN IMAGE (FREE VIA FLUX/POLLINATIONS)
    if is_image_request(prompt):
        img_prompt = extract_prompt(prompt)
        with st.chat_message("assistant"):
            with st.spinner(f"🎨 Generating '{img_prompt}'..."):
                try:
                    # Clean encode prompt into free image generator URL
                    encoded = urllib.parse.quote(img_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
                    
                    st.image(image_url, caption=f"🎨 '{img_prompt}'")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "type": "image",
                        "content": image_url,
                        "caption": f"🎨 '{img_prompt}'"
                    })
                except Exception as e:
                    st.error(f"Image error: {e}")

    # CASE 2: NORMAL CHAT OR VISION SOLVER (GEMINI)
    else:
        text_messages = [m for m in st.session_state.messages if m.get("type", "text") == "text"]
        recent_messages = text_messages[-4:-1]
        contents = []

        for m in recent_messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

        current_parts = []
        if image_part:
            current_parts.append(image_part)
        current_parts.append(types.Part.from_text(text=prompt))
        contents.append(types.Content(role="user", parts=current_parts))

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            max_retries = 3
            reply_text = ""

            SYSTEM_PROMPT = """
            You are T-Pire, an expert AI assistant and problem solver with vision capabilities.
            When an image is provided:
            1. Read and extract all text, equations, or problems from the picture.
            2. Solve the problem thoroughly step-by-step.
            If no image is provided, respond helpfully, fast, and conversationally.
            """

            for attempt in range(max_retries):
                try:
                    with st.spinner("Analyzing image and solving..." if image_part else "Thinking..."):
                        stream = client.models.generate_content_stream(
                            model="gemini-3.5-flash-lite",
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PROMPT,
                                temperature=0.5,
                                max_output_tokens=1500,
                            ),
                        )
                        for chunk in stream:
                            if chunk.text:
                                reply_text += chunk.text
                                message_placeholder.markdown(reply_text + "▌")

                        message_placeholder.markdown(reply_text)
                        st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply_text})
                        break

                except Exception as e:
                    err_str = str(e)
                    if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    else:
                        message_placeholder.warning("⚠️ Server busy right now. Please try again.")
                        break
