import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# ----------------- СТИЛИЗИРАНЕ (ТОЧНО КАТО НА ДВЕТЕ СНИМКИ) -----------------
st.markdown("""
<style>
    /* Премахване на странично меню и хедъри */
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

    /* Индикатор горе вдясно */
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

    /* Заглавие при празен екран */
    .center-hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 22vh;
        margin-bottom: 25px;
    }
    .hero-title {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Кутията за чат точно както на снимката */
    .chat-card {
        background-color: #212227;
        border: 1px solid #2e3038;
        border-radius: 18px;
        padding: 14px 18px 10px 18px;
        margin-top: 15px;
    }

    /* Прозрачно текстово поле вътре в кутията */
    div[data-testid="stTextInput"] input {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 16px !important;
        padding: 4px 0 10px 0 !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #8e8f99 !important;
    }

    /* Стилизиране на бутоните за прикачване */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #8e8f99 !important;
        padding: 2px 6px !important;
    }
    button[kind="secondary"]:hover {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- ГОРНА ЛЕНТА: МОДЕЛ ВЛЯВО (CHATGPT СТИЛ) -----------------
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

# Връзка с Gemini
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Моля, добавете GEMINI_API_KEY в Streamlit Secrets.")
    st.stop()

@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# Инициализация на сесията
if "messages" not in st.session_state:
    st.session_state.messages = []
if "attached_doc" not in st.session_state:
    st.session_state.attached_doc = None
if "attached_img" not in st.session_state:
    st.session_state.attached_img = None

# Начален екран
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

# ----------------- ЕДИННАТА КУТИЯ ЗА ЧАТ (ТОЧНО КАТО НА СНИМКИТЕ) -----------------
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# Динамичен надпис
bar_placeholder = "Продължи разговора" if st.session_state.messages else "Попитай нещо"

# 1. Текстово поле (горна част на кутията)
user_prompt = st.text_input(
    "Chat",
    placeholder=bar_placeholder,
    label_visibility="collapsed",
    key="chat_text_input"
)

# Индикатор за прикачен файл, ако е избран
if st.session_state.attached_doc:
    st.caption(f"📄 Готов за изпращане: `{st.session_state.attached_doc.name}`")
if st.session_state.attached_img:
    st.caption(f"🖼️ Готова за изпращане: `{st.session_state.attached_img.name}`")

# 2. Долен ред с иконките и капсулата [ 🌐 Търсене | 🗣️ Разсъждение ]
c_doc, c_img, c_dots, c_tools, c_mic, c_send = st.columns([0.6, 0.6, 0.6, 4.5, 0.6, 0.6])

# Иконка 📄⁺ (PDF и документи)
with c_doc:
    with st.popover("📄⁺"):
        uploaded_doc = st.file_uploader("Качи PDF / Документ", type=["pdf", "txt", "docx"], key="doc_up")
        if uploaded_doc:
            st.session_state.attached_doc = uploaded_doc
            st.success("Документът е прикачен!")

# Иконка 🖼️⁺ (Снимки и задачи)
with c_img:
    with st.popover("🖼️⁺"):
        uploaded_img = st.file_uploader("Качи снимка", type=["jpg", "jpeg", "png", "webp"], key="img_up")
        if uploaded_img:
            st.session_state.attached_img = uploaded_img
            st.success("Снимката е прикачена!")

# Иконка ...
with c_dots:
    with st.popover("···"):
        st.caption("Допълнителни опции")
        if st.button("🗑️ Изчисти чата"):
            st.session_state.messages = []
            st.session_state.attached_doc = None
            st.session_state.attached_img = None
            st.rerun()

# Капсула с бутоните Търсене и Разсъждение (точно като на втората снимка)
with c_tools:
    active_tools = st.pills(
        "Tools",
        ["🌐 Търсене", "🗣️ Разсъждение"],
        selection_mode="multi",
        default=["🗣️ Разсъждение"],
        label_visibility="collapsed"
    )

with c_mic:
    st.write("🎙️")

with c_send:
    send_clicked = st.button("➤")

st.markdown('</div>', unsafe_allow_html=True)

# ----------------- ИЗПРАЩАНЕ И ОБРАБОТКА -----------------
chosen_file = st.session_state.attached_doc or st.session_state.attached_img

if send_clicked and (user_prompt.strip() or chosen_file):
    prompt_text = user_prompt.strip()

    if chosen_file and not prompt_text:
        if chosen_file.type == "application/pdf":
            prompt_text = f"Моля, анализирай и реши/обясни подробно този PDF документ ({chosen_file.name})."
        else:
            prompt_text = "Моля, разгледай тази снимка и я реши/обясни стъпка по стъпка."

    # Записване в историята
    user_msg_data = {
        "role": "user",
        "content": prompt_text,
        "file_name": chosen_file.name if chosen_file else None,
        "file_type": chosen_file.type if chosen_file else None,
        "file_bytes": chosen_file.getvalue() if chosen_file else None
    }
    st.session_state.messages.append(user_msg_data)

    # Нулиране на прикачените файлове за следващия въпрос
    st.session_state.attached_doc = None
    st.session_state.attached_img = None

    # Контекст
    contents = []
    for m in st.session_state.messages[-4:-1]:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    current_parts = []
    if user_msg_data["file_bytes"]:
        current_parts.append(types.Part.from_bytes(
            data=user_msg_data["file_bytes"],
            mime_type=user_msg_data["file_type"]
        ))
    current_parts.append(types.Part.from_text(text=prompt_text))
    contents.append(types.Content(role="user", parts=current_parts))

    # Инструменти според капсулата
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
                spinner_text = "Търсене в интернет..." if (active_tools and "🌐 Търсене" in active_tools) else ("Анализиране на документа..." if user_msg_data["file_bytes"] else "Мислене...")
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
    
    st.rerun()
