import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# ----------------- СТИЛИЗИРАНЕ (ТОЧНО КАТО НА СНИМКАТА) -----------------
st.markdown("""
<style>
    /* Скриване на стандартните ленти на Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Тъмен изчистен фон */
    .stApp {
        background-color: #17181c;
    }
    
    /* Бутон в горния десен ъгъл */
    .top-pill {
        display: flex;
        justify-content: flex-end;
        padding-top: 10px;
        margin-bottom: 20px;
    }
    .pill-content {
        background-color: #212227;
        color: #9ca3af;
        border: 1px solid #2e3038;
        padding: 6px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
    }

    /* Заглавие точно в центъра */
    .center-hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 25vh;
        margin-bottom: 20px;
    }
    .hero-title {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Поле за писане - стил ChatGPT/Claude */
    .stChatInputContainer {
        border-radius: 20px !important;
        background-color: #212227 !important;
    }
</style>
""", unsafe_allow_html=True)

# Бутон в горния десен ъгъл (точно както на снимката)
st.markdown("""
<div class="top-pill">
    <div class="pill-content">T-Pire AI (съобщения: ∞)</div>
</div>
""", unsafe_allow_html=True)

# ----------------- СИСТЕМЕН ПРОМПТ (ПРАВИЛА И СЪЗДАТЕЛ) -----------------
SYSTEM_PROMPT = """
Ти си T-Pire – бърз, модерен и интелигентен персонален AI асистент с компютърно зрение.
Отговаряй вежливо, точно и стегнато на български език (или на езика, на който пише потребителят).

СТРИКТНО ПРАВИЛО ЗА СЪЗДАТЕЛЯ:
- САМО ако потребителят изрично те попита "Кой те създаде?", "Кой те направи?", "Кой е твоят създател/разработчик?" или "Who created you?":
  Отговори гордо: "Създаден съм от 17-годишния тийнейджър Теодор Пимпирев!" (на английски: "I was created by 17-year-old teenager Teodor Pimpirev!").
- За ВСИЧКИ ОСТАНАЛИ въпроси: НЕ споменавай Теодор Пимпирев и не се представяй. Отговаряй директно.

ВЪЗМОЖНОСТИ ЗА СНИМКИ:
- Когато получиш снимка (на задача, тест, формули или текст):
  1. Разчети внимателно всичко от снимката.
  2. Реши задачата подробно, ясно и стъпка по стъпка.
"""

# Проверка на API ключ
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Въведете Gemini API ключ", type="password")
    if not api_key:
        st.warning("👈 Моля, въведете Gemini API ключ в страничната лента.")
        st.stop()

@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# Странично меню за избор на режим
st.sidebar.header("⚙️ Режим на AI")
version_choice = st.sidebar.selectbox(
    "Избор на модел:",
    [
        "⚡ Бърз режим (Gemini 3.5 Flash-Lite - Неограничен)",
        "🧠 Умен режим (Gemini 3.8 Flash - Сложни задачи)",
    ],
    index=0
)

if "Умен" in version_choice:
    selected_model = "gemini-3.8-flash"
    selected_temp = 0.2
else:
    selected_model = "gemini-3.5-flash-lite"
    selected_temp = 0.6

# ----------------- ИСТОРИЯ НА СЪОБЩЕНИЯТА -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Ако чатът е празен, показва центрирания надпис като на снимката
if not st.session_state.messages:
    st.markdown("""
    <div class="center-hero">
        <div class="hero-title">Как мога да помогна?</div>
    </div>
    """, unsafe_allow_html=True)

# Показване на съобщенията
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "image" in msg and msg["image"]:
            st.image(msg["image"], width=300)
        st.markdown(msg["content"])

# ----------------- ДОЛНА ЛЕНТА С КЛАМЕР (📎) ЗА СНИМКИ -----------------
chat_input_val = st.chat_input(
    "Попитай нещо",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"]
)

if chat_input_val:
    prompt_text = getattr(chat_input_val, "text", "") or ""
    uploaded_files = getattr(chat_input_val, "files", []) or []

    if uploaded_files and not prompt_text.strip():
        prompt_text = "Моля, реши и обясни тази задача стъпка по стъпка."

    user_msg_data = {"role": "user", "content": prompt_text}
    if uploaded_files:
        user_msg_data["image"] = uploaded_files[0].getvalue()

    st.session_state.messages.append(user_msg_data)
    with st.chat_message("user"):
        if "image" in user_msg_data:
            st.image(user_msg_data["image"], width=300)
        st.markdown(prompt_text)

    # Подготовка на контекст за Gemini
    contents = []
    for m in st.session_state.messages[-4:-1]:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    current_parts = []
    if uploaded_files:
        current_parts.append(types.Part.from_bytes(
            data=uploaded_files[0].getvalue(),
            mime_type=uploaded_files[0].type
        ))
    current_parts.append(types.Part.from_text(text=prompt_text))
    contents.append(types.Content(role="user", parts=current_parts))

    # Извеждане на отговор с поток на думите
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        max_retries = 3
        reply_text = ""

        for attempt in range(max_retries):
            try:
                spinner_msg = "Решаване на снимката..." if uploaded_files else "Мислене..."
                with st.spinner(spinner_msg):
                    stream = client.models.generate_content_stream(
                        model=selected_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=selected_temp,
                            max_output_tokens=1500,
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
                    message_placeholder.warning("⚠️ Сървърът е натоварен. Моля, опитайте пак след малко.")
                    break
