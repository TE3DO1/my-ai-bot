import streamlit as st
import time
from google import genai
from google.genai import types
from huggingface_hub import InferenceClient

st.set_page_config(page_title="Ask T-Pire", page_icon="⚡", layout="centered")

st.title("⚡ Ask T-Pire (Fast Chat, Vision & FLUX Image Gen)")

# ----------------- KEYS & CLIENTS -----------------
gemini_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Enter Gemini API Key", type="password")
hf_token = st.secrets.get("HF_TOKEN") or st.sidebar.text_input("Enter Hugging Face Token (Optional for Images)", type="password")

if not gemini_key:
    st.warning("👈 Please add your Gemini API Key to continue.")
    st.stop()

@st.cache_resource
def get_gemini_client(key):
    return genai.Client(api_key=key)

@st.cache_resource
def get_hf_client(token):
    return InferenceClient(api_key=token) if token else None

gemini_client = get_gemini_client(gemini_key)
hf_client = get_hf_client(hf_token)

# ----------------- SIDEBAR: PICTURE SOLVER -----------------
st.sidebar.header("📸 Picture Solver (Vision)")
uploaded_file = st.sidebar.file_uploader("Upload a photo to solve or read", type=["jpg", "jpeg", "png", "webp"])

image_part = None
if uploaded_file is not None:
    st.sidebar.image(uploaded_file, caption="Uploaded Picture", use_container_width=True)
    image_part = types.Part.from_bytes(data=uploaded_file.getvalue(), mime_type=uploaded_file.type)

st.sidebar.markdown("---")
st.sidebar.header("⚡ Instant FLUX Images")
st.sidebar.caption("Type `/image <prompt>` to generate an image in 2 seconds with no cooldown!")

# ----------------- CHAT HISTORY -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], caption=msg.get("caption", "Generated Image"))
        else:
            st.markdown(msg["content"])

# ----------------- PROMPT HELPERS -----------------
def is_image_request(text: str) -> bool:
    t = text.strip().lower()
    return t.startswith(("/image", "/draw", "generate an image", "create an image", "draw a ", "draw me"))

def extract_prompt(text: str) -> str:
    prefixes = ["/image", "/draw", "generate an image of", "generate an image", "create an image of", "create an image", "draw an image of", "draw a", "draw me", "draw"]
    t_lower = text.strip().lower()
    for p in prefixes:
        if t_lower.startswith(p):
            return text.strip()[len(p):].strip(" :,-")
    return text.strip()

# ----------------- CHAT INPUT -----------------
if prompt := st.chat_input("Ask a question, upload a photo, or type '/image a supercar'..."):
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # CASE 1: INSTANT IMAGE GENERATION VIA FLUX.1-SCHNELL (NO 45s WAIT)
    if is_image_request(prompt):
        img_prompt = extract_prompt(prompt)
        with st.chat_message("assistant"):
            if not hf_client:
                st.warning("⚠️ Please add your free `HF_TOKEN` in Streamlit Secrets or the sidebar to generate images.")
            else:
                with st.spinner(f"⚡ Generating '{img_prompt}' in ~3 seconds..."):
                    try:
                        # Calls FLUX.1-schnell directly
                        img = hf_client.text_to_image(img_prompt, model="black-forest-labs/FLUX.1-schnell")
                        st.image(img, caption=f"🎨 '{img_prompt}'")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "type": "image",
                            "content": img,
                            "caption": f"🎨 '{img_prompt}'"
                        })
                    except Exception as e:
                        st.error(f"Generation error: {e}")

    # CASE 2: FAST CHAT & VISION PROBLEM SOLVER
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

            for attempt in range(max_retries):
                try:
                    with st.spinner("Analyzing and solving..." if image_part else "Thinking..."):
                        stream = gemini_client.models.generate_content_stream(
                            model="gemini-3.5-flash-lite",
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction="You are T-Pire, an expert tutor and assistant with vision. Solve problems step-by-step and keep chat answers fast and helpful.",
                                temperature=0.5,
                                max_output_tokens=1200,
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
