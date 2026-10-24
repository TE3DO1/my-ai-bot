import streamlit as st
import time
import sqlite3
import hashlib
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# ----------------- БАЗА ДАННИ (ПОТРЕБИТЕЛИ И ИСТОРИЯ) -----------------
conn = sqlite3.connect("tpire_data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    role TEXT,
    content TEXT,
    file_name TEXT,
    file_type TEXT,
    file_bytes BLOB
)
""")
conn.commit()

def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------- СТИЛИЗИРАНЕ -----------------
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
        max-width: 190px;
    }
    div[data-testid="stSelectbox"] > div {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    .center-hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 20vh;
        margin-bottom: 25px;
    }
    .hero-title {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
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
        padding: 2px 4px !important;
        border-radius: 8px !important;
    }
    div[data-testid="stPopover"] button:hover {
        background-color: #2c2d35 !important;
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

    div[data-testid="stButton"] button {
        background-color: transparent !important;
        border: none !important;
        color: #8e8f99 !important;
        border-radius: 8px !important;
        padding: 2px 4px !important;
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

# ----------------- СЕСИЯ И АВТЕНТИКАЦИЯ -----------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "attached_file" not in st.session_state:
    st.session_state.attached_file = None
if "pending_submit" not in st.session_state:
    st.session_state.pending_submit = None

# Диалогов прозорец за Вход / Регистрация
@st.dialog("Вход в T-Pire")
def auth_modal():
    tab_login, tab_reg = st.tabs(["Вход", "Регистрация"])
    with tab_login:
        email = st.text_input("Имейл", key="auth_login_email")
        password = st.text_input("Парола", type="password", key="auth_login_pass")
        if st.button("Влез в профила", use_container_width=True):
            if email and password:
                c.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", (email.strip().lower(), hash_pass(password)))
                user = c.fetchone()
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.user_email = user[1]
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                    st.success("Успешен вход!")
                    st.rerun()
                else:
                    st.error("Грешен имейл или парола!")
            else:
                st.warning("Моля, попълнете всички полета.")

    with tab_reg:
        reg_email = st.text_input("Имейл за регистрация", key="auth_reg_email")
        reg_pass = st.text_input("Парола", type="password", key="auth_reg_pass")
        if st.button("Създай нов профил", use_container_width=True):
            if reg_email and reg_pass:
                try:
                    c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (reg_email.strip().lower(), hash_pass(reg_pass)))
                    conn.commit()
                    st.session_state.user_id = c.lastrowid
                    st.session_state.user_email = reg_email.strip().lower()
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                    st.success("Профилът е създаден успешно!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Този имейл вече е регистриран!")
            else:
                st.warning("Моля, попълнете всички полета.")

# Зареждане на съобщения за избран чат
def load_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    c.execute("SELECT role, content, file_name, file_type, file_bytes FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    rows = c.fetchall()
    st.session_state.messages = []
    for r in rows:
        st.session_state.messages.append({
            "role": r[0],
            "content": r[1],
            "file_name": r[2],
            "file_type": r[3],
            "file_bytes": r[4]
        })
    st.rerun()

# ----------------- ГОРНА ЛЕНТА: МОДЕЛ, ИСТОРИЯ И ПРОФИЛ -----------------
col_model, col_chats, col_spacer, col_auth = st.columns([2.5, 2.2, 2.3, 3])

with col_model:
    model_choice = st.selectbox(
        "Модел",
        ["⚡ T-Pire 3.5", "🧠 T-Pire 3.8"],
        label_visibility="collapsed"
    )

with col_chats:
    if st.session_state.user_id:
        with st.popover("📁 История"):
            if st.button("➕ Нов чат", use_container_width=True):
                st.session_state.current_chat_id = None
                st.session_state.messages = []
                st.rerun()
            st.divider()
            c.execute("SELECT id, title FROM chats WHERE user_id = ? ORDER BY id DESC", (st.session_state.user_id,))
            user_chats = c.fetchall()
            if user_chats:
                for ch in user_chats:
                    if st.button(f"💬 {ch[1]}", key=f"chat_{ch[0]}", use_container_width=True):
                        load_chat(ch[0])
            else:
                st.caption("Нямате запазени чатове.")
    else:
        st.caption("🔒 *Влез за история*")

with col_auth:
    if st.session_state.user_id:
        u_name = st.session_state.user_email.split('@')[0]
        with st.popover(f"👤 {u_name}"):
            st.write(f"Влезли сте като:\n**{st.session_state.user_email}**")
            if st.button("🚪 Изход", use_container_width=True):
                st.session_state.user_id = None
                st.session_state.user_email = None
                st.session_state.current_chat_id = None
                st.session_state.messages = []
                st.rerun()
    else:
        if st.button("Влез (профил)"):
            auth_modal()

selected_model = "gemini-3.8-flash" if "3.8" in model_choice else "gemini-3.5-flash-lite"
selected_temp = 0.2 if "3.8" in model_choice else 0.6

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

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Моля, добавете GEMINI_API_KEY в Streamlit Secrets.")
    st.stop()

@st.cache_resource
def get_client(key):
    return genai.Client(api_key=key)

client = get_client(api_key)

# Слизане на бара надолу при съобщения
if st.session_state.messages:
    st.markdown("""
    <style>
        .main .block-container {
            padding-bottom: 160px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(input[aria-label="Chat"]) {
            position: fixed !important;
            bottom: 20px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 94% !important;
            max-width: 768px !important;
            z-index: 9999 !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6) !important;
        }
    </style>
    """, unsafe_allow_html=True)

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

# ----------------- КУТИЯ ЗА ПИСАНЕ -----------------
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

    col_doc, col_img, col_dots, col_tools, col_spacer, col_send = st.columns([0.5, 0.5, 0.5, 3.8, 1.2, 0.5])

    with col_doc:
        with st.popover("", icon=":material/note_add:", help="Качи PDF / Текст"):
            pdf_upload = st.file_uploader("Качи PDF / Текст", type=["pdf", "txt"], key="up_pdf")
            if pdf_upload:
                st.session_state.attached_file = pdf_upload
                st.success("Прикачен!")

    with col_img:
        with st.popover("", icon=":material/add_photo_alternate:", help="Качи снимка"):
            img_upload = st.file_uploader("Качи снимка", type=["jpg", "jpeg", "png", "webp"], key="up_img")
            if img_upload:
                st.session_state.attached_file = img_upload
                st.success("Прикачена!")

    with col_dots:
        with st.popover("", icon=":material/more_horiz:", help="Опции"):
            if st.button("🗑️ Изчисти този чат"):
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
        st.button("", icon=":material/arrow_upward:", on_click=submit_action, help="Изпрати")

# ----------------- ИЗПРАЩАНЕ И ЗАПАЗВАНЕ В ПРОФИЛА -----------------
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

    # Ако потребителят е влязъл в профил, създаваме/свързваме чат в базата данни
    if st.session_state.user_id:
        if not st.session_state.current_chat_id:
            chat_title = prompt_text[:28] + "..." if len(prompt_text) > 28 else (prompt_text or "Нов разговор")
            c.execute("INSERT INTO chats (user_id, title) VALUES (?, ?)", (st.session_state.user_id, chat_title))
            conn.commit()
            st.session_state.current_chat_id = c.lastrowid
        
        c.execute("""
            INSERT INTO messages (chat_id, role, content, file_name, file_type, file_bytes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (st.session_state.current_chat_id, "user", prompt_text, user_msg_data["file_name"], user_msg_data["file_type"], user_msg_data["file_bytes"]))
        conn.commit()

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
                spinner_text = "Търсене в интернет..." if (active_tools and "🌐 Търсене" in active_tools) else ("Анализиране..." if user_msg_data["file_bytes"] else "Мислене...")
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

                    # Запазване на отговора в базата данни за този потребител
                    if st.session_state.user_id and st.session_state.current_chat_id:
                        c.execute("""
                            INSERT INTO messages (chat_id, role, content, file_name, file_type, file_bytes)
                            VALUES (?, ?, ?, NULL, NULL, NULL)
                        """, (st.session_state.current_chat_id, "assistant", reply_text))
                        conn.commit()

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
