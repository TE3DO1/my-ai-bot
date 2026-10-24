import streamlit as st
import io
import time
import sqlite3
from gtts import gTTS
from google import genai
from google.genai import types

st.set_page_config(page_title="Call T-Pire", page_icon="📞", layout="centered")

# ----------------- DATABASE (PER-USER MEMORY) -----------------
conn = sqlite3.connect("t_pire_memory.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS chat_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        role TEXT,
        content TEXT
    )
""")
conn.commit()

def load_user_memory(user_name):
    clean_user = user_name.lower().strip()
    c.execute("SELECT role, content FROM chat_memory WHERE username = ? ORDER BY id ASC", (clean_user,))
    return [{"role": row[0], "content": row[1]} for row in c.fetchall()]

def save_user_message(user_name, role, content):
    clean_user = user_name.lower().strip()
    c.execute("INSERT INTO chat_memory (username, role, content) VALUES (?, ?, ?)", (clean_user, role, content))
    conn.commit()

def clear_user_memory(user_name):
    clean_user = user_name.lower().strip()
    c.execute("DELETE FROM chat_memory WHERE username = ?", (clean_user,))
    conn.commit()

# ----------------- SIDEBAR: USER PROFILES -----------------
st.sidebar.header("👤 Your Profile")
user_name = st.sidebar.text_input("Enter your name:", value="Teodor")
if not user_name.strip():
    user_name = "Friend"

if st.sidebar.button("🗑️ Reset My Memory"):
    clear_user_memory(user_name)
    st.session_state.messages = []
    st.sidebar.success(f"Memory cleared for {user_name}!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Audio & Settings")
voice_reply = st.sidebar.checkbox("🔊 Auto-Speak Responses", value=True)

# ----------------- CHECK KEYS & INITIALIZE -----------------
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("👈 Please enter your Gemini API Key in the sidebar.")
        st.stop()

@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# Sync database memory with current active user
if ("current_user" not in st.session_state) or (st.session_state.current_user != user_name):
    st.session_state.current_user = user_name
    st.session_state.messages = load_user_memory(user_name)

st.title(f"📞 Call T-Pire")
st.caption(f"Currently chatting with: **{user_name}**")

# ----------------- DISPLAY CHAT HISTORY -----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------- CREATOR PROMPT -----------------
SYSTEM_PROMPT = f"""
You are T-Pire, an AI assistant having a conversation with {user_name}.
Keep your answers brief (1 to 3 sentences) and conversational like a real phone call.

STRICT CREATOR RULE:
- ONLY state your creator if {user_name} explicitly asks "Who created/made you?".
- If asked, say: "I was created by 17-year-old teenager Teodor Pimpirev!"
- For all other questions: Answer directly and never mention Teodor Pimpirev unprompted.
"""

# ----------------- CORE RESPONSE HANDLER -----------------
def process_interaction(content_parts, display_text):
    # Save user message to database and session state
    save_user_message(user_name, "user", display_text)
    st.session_state.messages.append({"role": "user", "content": display_text})
    
    with st.chat_message("user"):
        st.markdown(display_text)

    # Gather recent context from this specific user's memory
    recent_turns = st.session_state.messages[-4:-1]
    history_contents = []
    for m in recent_turns:
        role = "user" if m["role"] == "user" else "model"
        history_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
    
    history_contents.append(types.Content(role="user", parts=content_parts))

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            with st.spinner(f"T-Pire is talking to {user_name}..."):
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=history_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3,
                        max_output_tokens=600,
                    ),
                )
                reply = response.text
                message_placeholder.markdown(reply)

                # Save AI response to this user's database
                save_user_message(user_name, "assistant", reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Speak out loud
                if voice_reply and reply.strip():
                    clean_speech = reply.replace("*", "").replace("#", "")
                    tts = gTTS(text=clean_speech, lang="en")
                    sound_buffer = io.BytesIO()
                    tts.write_to_fp(sound_buffer)
                    sound_buffer.seek(0)
                    st.audio(sound_buffer.getvalue(), format="audio/mp3", autoplay=True)

        except Exception as e:
            message_placeholder.error(f"Error: {e}")

# ----------------- VOICE INPUT (PHONE CALL) -----------------
st.subheader("🎙️ Tap to Speak")
audio_input = st.audio_input("Speak to T-Pire:")

if audio_input is not None:
    audio_bytes = audio_input.getvalue()
    if ("last_audio" not in st.session_state) or (st.session_state.last_audio != audio_bytes):
        st.session_state.last_audio = audio_bytes
        voice_part = types.Part.from_bytes(data=audio_bytes, mime_type=audio_input.type)
        instruction_part = types.Part.from_text(text=f"Respond conversationally to {user_name}.")
        process_interaction([voice_part, instruction_part], "🎤 *(Sent a Voice Message)*")

# ----------------- TEXT INPUT -----------------
if text_prompt := st.chat_input(f"Type a message as {user_name}..."):
    process_interaction([types.Part.from_text(text=text_prompt)], text_prompt)
