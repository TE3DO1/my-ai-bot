import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# ----------------- СТИЛИЗИРАНЕ (МОБИЛЕН И ДЕСКТОП ДИЗАЙН) -----------------
css_styles = """
<style>
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #17181c;
    }

    div[data-testid="stSelectbox"] {
        max-width: 210px;
    }
    div[data-testid="stSelectbox"] > div {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

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

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        border-radius: 18px !important;
        padding: 10px 14px 6px 14px !important;
    }

    div[data-testid="stTextInput"] input {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 15px !important;
        padding: 2px 0 6px 0 !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #8e8f99 !important;
    }

    div[data-testid="stPopover"] button {
        background-color: transparent !important;
        border: none !important;
        color: #8e8f99 !important;
        padding: 2px 6px !important;
        font-size: 16px !important;
    }
    div[data-testid="stPopover"] button:hover {
        color: #ffffff !important;
    }

    div[data-testid="stPills"] button {
        background-color: #26272e !important;
        border: 1px solid #33353e !important;
        color: #9ca3af !important;
        border-radius: 20px !important;
        padding: 3px 10px !important;
        font-size: 12px !important;
    }
    div[data-testid="stPills"] button[aria-checked="true"] {
        background-color: #2f313a !important;
        border: 1px solid #4b5563 !important;
        color: #ffffff !important;
    }

    .send-btn button {
        background-color: transparent !important;
        border: none !important;
        color: #8e8f99 !important;
        font-size: 18px !important;
        padding: 2px 8px !important;
    }
    .send-btn button:hover {
        color: #ffffff !important;
    }

    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            overflow-x: auto !important;
            gap: 4px !important;
        }
        div[data-testid="column"] {
            width: auto !important;
            flex: 0 0 auto !important;
            min-width: 0 !important;
        }
    }
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

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

# Връзка с Gemini
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Моля, добавете GEMINI_API_KEY в Streamlit Secrets.")
    st.stop()

@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# ----------------- ИНИЦИАЛИЗАЦИЯ -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "attached_file" not in st.session_state:
    st.session_state.attached_file = None
if "pending_submit" not in st.session_state:
    st.session_state.pending_submit = None

# Начален екран
if not st.session_state.messages:
    st.markdown("""
    <div class="center-hero">
        <div class="hero-title">Как мога да помогна?</div>
    </div>
    """, unsafe_allow_html=True)

# История на съобщенията
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("file_bytes"):
            if msg.get("file_type", "").startswith("image/"):
                st.image(msg["file_bytes"], width=300)
            else:
                st.info(f"📄 **Прикачен документ:** `{msg.get('file_name', 'документ')}`")
        st.markdown(msg["content"])

# ----------------- ЕДИННАТА КУТИЯ ЗА ПИСАНЕ И БУТОНИ -----------------
bar_placeholder = "Продължи разговора" if st.session_state.messages else "Попитай нещо"

def submit_action():
    text_val = st.session_state.get(f"user_text_input_{st.session_state.input_key}", "").strip()
    if text_val or st.session_state.attached_file:
        st.session_state.pending_submit = {
            "text": text_val,
            "file": st.session_state.attached_file
        }
        st.session_state.attached_file = None
        st.session_state.input_key += 1

with st.container(border=True):
    st.text_input(
        "Chat",
        placeholder=bar_placeholder,
        label_visibility="collapsed",
        key=f"user_text_input_{st.session_state.input_key}",
        on_change=submit_action
    )

    if st.session_state.attached_file:
        st.caption(f"📎 Готов за изпращане: `{st.session_state.attached_file.name}`")

    col_doc, col_img, col_dots, col_tools, col_spacer, col_send = st.columns([0.6, 0.6, 0.6, 3.8, 1.2, 0.6])

    with col_doc:
        with st.popover("📄⁺"):
            pdf_upload = st.file_uploader("Качи PDF / Текст", type=["pdf", "txt"], key="up_pdf")
            if pdf_upload:
                st.session_state.attached_file = pdf_upload
                st.success("Прикачен!")

    with col_img:
        with st.popover("🖼️⁺"):
            img_upload = st.file_uploader("Качи снимка", type=["jpg", "jpeg", "png", "webp"], key="up_img")
            if img_upload:
                st.session_state.attached_file = img_upload
                st.success("Прикачена!")

    with col_dots:
        with st.popover("···"):
            if st.button("🗑️ Изчисти чата"):
                st.session_state.messages = []
                st.session_state.attached_file = None
                st.session_state.pending_submit = None
                st.rerun()

    with col_tools:
        active_tools = st.pills(
            "Инструменти",
            ["🌐 Търсене", "🗣️ Разсъждение"],
            selection_mode="multi",
            default=["🗣️ Разсъждение"],
            label_visibility="collapsed"
        )

    with col_send:
        st.markdown('<div class="send-btn">', unsafe_allow_html=True)
        st.button("➤", on_click=submit_action)
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- ИЗПРАЩАНЕ И ОТГОВОР -----------------
if st.session_state.pending_submit:
    data = st.session_state.pending_submit
    st.session_state.pending_submit = None

    prompt_text = data["text"]
    c_file = data["file"]

    if c_file and not prompt_text:
        if c_file.type == "application/pdf":
            prompt_text = f"Моля, анализирай и реши/обясни подробно този PDF документ ({c_file.name})."
        else:
            prompt_text = "Моля, разгледай тази снимка и я реши/обясни стъпка по стъпка."

    user_msg_data = {
        "role": "user",
        "content": prompt_text,
        "file_name": c_file.name if c_file else None,
        "file_type": c_file.type if c_file else None,
        "file_bytes": c_file.getvalue() if c_file else None
    }
    st.session_state.messages.append(user_msg_data)

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
                spinner_text = "Търсене в интернет..." if (active_tools and "🌐 Търсене" in active_tools) else ("Анализиране на файла..." if user_msg_data["file_bytes"] else "Мислене...")
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
