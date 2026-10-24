import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# ----------------- СТИЛИЗИРАНЕ (ИЗЧИСТЕН CHATGPT СТИЛ) -----------------
st.markdown("""
<style>
    /* Премахване на страничното меню и излишни Streamlit елементи */
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #17181c;
    }

    /* Модел селектор горе вляво (стил ChatGPT) */
    div[data-testid="stSelectbox"] {
        max-width: 220px;
    }
    div[data-testid="stSelectbox"] > div {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Горен десен индикатор */
    .top-pill {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        height: 100%;
    }
    .pill-content {
        background-color: #212227;
        color: #9ca3af;
        border: 1px solid #2e3038;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 13px;
    }

    /* Центрирано заглавие при празен екран */
    .center-hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 24vh;
        margin-bottom: 25px;
    }
    .hero-title {
        color: #ffffff;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Стилизиране на лентата за писане долу */
    div[data-testid="stChatInput"] {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        border-radius: 20px !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
    }

    /* Оправяне на цветовете на бутоните Търсене / Разсъждение (без червени рамки) */
    div[data-testid="stPills"] button {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        color: #9ca3af !important;
        border-radius: 20px !important;
    }
    div[data-testid="stPills"] button[aria-checked="true"] {
        background-color: #2e3038 !important;
        border: 1px solid #4b5563 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- ГОРНА ЛЕНТА: МОДЕЛ ВЛЯВО -----------------
col_model, col_spacer, col_user = st.columns([3, 4, 3])

with col_model:
    model_choice = st.selectbox(
        "Модел",
        ["⚡ T-Pire 3.5 (Бърз)", "🧠 T-Pire 3.8 (Умен)"],
        label_visibility="collapsed"
    )

with col_user:
    st.markdown("""
    <div class="top-pill">
        <div class="pill-content">T-Pire AI (съобщения: ∞)</div>
    </div>
    """, unsafe_allow_html=True)

if "3.8" in model_choice:
    selected_model = "gemini-3.8-flash"
    selected_temp = 0.2
else:
    selected_model = "gemini-3.5-flash-lite"
    selected_temp = 0.6

# ----------------- СИСТЕМЕН ПРОМПТ (СЪЗДАТЕЛ И ПРАВИЛА) -----------------
SYSTEM_PROMPT = """
Ти си T-Pire – бърз, мощен и интелигентен персонален AI асистент с възможности за четене на PDF документи, файлове и компютърно зрение.
Отговаряй точно, структурирано и вежливо на български език (или на езика, на който пише потребителят).

СТРИКТНО ПРАВИЛО ЗА СЪЗДАТЕЛЯ:
- САМО ако потребителят изрично те попита "Кой те създаде?", "Кой те направи?", "Кой е твоят разработчик?" или "Who created you?":
  Отговори гордо: "Създаден съм от 17-годишния тийнейджър Теодор Пимпирев!" (на английски: "I was created by 17-year-old teenager Teodor Pimpirev!").
- За ВСИЧКИ ОСТАНАЛИ въпроси: НЕ споменавай Теодор Пимпирев и не се представяй. Отговаряй директно.

ВЪЗМОЖНОСТИ ЗА PDF И СНИМКИ:
- Когато получиш PDF документ, файл или снимка:
  1. Разчети подробно целия текст, страници, формули и въпроси в него.
  2. Реши задачите или направи ясен анализ стъпка по стъпка.
"""

# Връзка с Gemini API
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Моля, добавете вашия GEMINI_API_KEY в Streamlit Secrets.")
    st.stop()

@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# ----------------- ИСТОРИЯ НА СЪОБЩЕНИЯТА -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Начален екран (само при нов чат)
if not st.session_state.messages:
    st.markdown("""
    <div class="center-hero">
        <div class="hero-title">Как мога да помогна?</div>
    </div>
    """, unsafe_allow_html=True)

# Показване на историята
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("file_bytes"):
            if msg.get("file_type", "").startswith("image/"):
                st.image(msg["file_bytes"], width=300)
            else:
                st.info(f"📄 **Прикачен документ:** `{msg.get('file_name', 'документ')}`")
        st.markdown(msg["content"])

# ----------------- БУТОНИ ЗА ТЪРСЕНЕ И РАЗСЪЖДЕНИЕ -----------------
col_tools, _ = st.columns([3, 1])
with col_tools:
    active_tools = st.pills(
        "Инструменти",
        ["🌐 Търсене", "🗣️ Разсъждение"],
        selection_mode="multi",
        default=["🗣️ Разсъждение"],
        label_visibility="collapsed"
    )

# Динамичен надпис в лентата
bar_placeholder = "Продължи разговора" if st.session_state.messages else "Попитай нещо"

# ----------------- ЧИСТО ВХОДЯЩО ПОЛЕ (БЕЗ МИКРОФОН, С ПОДДРЪЖКА НА СНИМКИ И PDF) -----------------
chat_val = st.chat_input(
    bar_placeholder,
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp", "pdf", "txt"]
)

if chat_val:
    prompt_text = getattr(chat_val, "text", "") or ""
    uploaded_files = getattr(chat_val, "files", []) or []

    # Ако е качен файл без допълнителен текст
    if uploaded_files and not prompt_text.strip():
        f = uploaded_files[0]
        if f.type == "application/pdf":
            prompt_text = f"Моля, анализирай и обясни съдържанието на този PDF документ ({f.name}) подробно."
        else:
            prompt_text = "Моля, разгледай тази снимка и я реши/обясни подробно стъпка по стъпка."

    # Запазване в историята
    user_msg_data = {
        "role": "user",
        "content": prompt_text,
        "file_name": uploaded_files[0].name if uploaded_files else None,
        "file_type": uploaded_files[0].type if uploaded_files else None,
        "file_bytes": uploaded_files[0].getvalue() if uploaded_files else None
    }
    st.session_state.messages.append(user_msg_data)

    with st.chat_message("user"):
        if user_msg_data["file_bytes"]:
            if user_msg_data["file_type"].startswith("image/"):
                st.image(user_msg_data["file_bytes"], width=300)
            else:
                st.info(f"📄 **Прикачен документ:** `{user_msg_data['file_name']}`")
        st.markdown(prompt_text)

    # Подготовка на контекст за Gemini
    contents = []
    for m in st.session_state.messages[-4:-1]:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    current_parts = []
    if uploaded_files:
        uf = uploaded_files[0]
        current_parts.append(types.Part.from_bytes(
            data=uf.getvalue(),
            mime_type=uf.type
        ))
    current_parts.append(types.Part.from_text(text=prompt_text))
    contents.append(types.Content(role="user", parts=current_parts))

    # Инструменти
    tools = []
    if active_tools and "🌐 Търсене" in active_tools:
        tools.append(types.Tool(google_search=types.GoogleSearch()))

    temp = 0.2 if (active_tools and "🗣️ Разсъждение" in active_tools) else selected_temp

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        max_retries = 3
        reply_text = ""

        for attempt in range(max_retries):
            try:
                spinner_text = "Търсене в интернет..." if (active_tools and "🌐 Търсене" in active_tools) else ("Анализиране на файла..." if uploaded_files else "Мислене...")
                with st.spinner(spinner_text):
                    stream = client.models.generate_content_stream(
                        model=selected_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=temp,
                            tools=tools if tools else None,
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
                    message_placeholder.warning("⚠️ Сървърът е зает. Моля, опитайте пак след няколко секунди.")
                    break
