import streamlit as st
import time
import sqlite3
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="⚡", layout="centered", initial_sidebar_state="auto")

# ----------------- БАЗА ДАННИ -----------------
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

# ----------------- ИЗПРАЩАНЕ НА ИМЕЙЛ С КОД -----------------
def send_email_code(to_email: str, code: str):
    smtp_user = st.secrets.get("SMTP_EMAIL")
    smtp_pass = st.secrets.get("SMTP_PASSWORD")
    
    if not smtp_user or not smtp_pass:
        return False, "Липсват SMTP_EMAIL или SMTP_PASSWORD в Streamlit Secrets!"

    clean_pass = smtp_pass.replace(" ", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"Вашият код за потвърждение: {code}", "utf-8")
    msg["From"] = f"T-Pire AI <{smtp_user}>"
    msg["To"] = to_email

    html_content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #17181c; color: #ffffff; padding: 25px; border-radius: 12px; max-width: 450px; margin: auto;">
        <h2 style="color: #4f8bf9; margin-top: 0; text-align: center;">⚡ T-Pire AI</h2>
        <p style="font-size: 15px; color: #d1d5db; text-align: center;">Вашият 6-цифрен код за потвърждение е:</p>
        <div style="background-color: #212227; border: 1px solid #383a45; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <span style="font-size: 30px; font-weight: bold; letter-spacing: 5px; color: #ffffff;">{code}</span>
        </div>
        <p style="font-size: 12px; color: #8e8f99; text-align: center;">Кодът е валиден 10 минути.</p>
        <hr style="border: 0; border-top: 1px solid #2e3038; margin: 20px 0;">
        <p style="font-size: 11px; color: #6b7280; text-align: center;">T-Pire AI • Създаден от Теодор Пимпирев</p>
    </div>
    """
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=12) as server:
            server.starttls()
            server.login(smtp_user, clean_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        return True, "Писмото е изпратено успешно!"
    except Exception as e:
        return False, f"Грешка при изпращане: {e}"

# ----------------- РЕСПОНСИВЕН ДИЗАЙН -----------------
css_styles = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp {
        background-color: #17181c;
    }

    [data-testid="stSidebar"] {
        background-color: #1b1c22 !important;
        border-right: 1px solid #272832 !important;
    }

    /* Модел селектор горе вляво на главния екран */
    div[data-testid="stSelectbox"] {
        max-width: 200px;
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
        margin-top: 18vh;
        margin-bottom: 25px;
    }
    .hero-title {
        color: #ffffff;
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Кутия за писане */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        border-radius: 18px !important;
        padding: 8px 12px 6px 12px !important;
    }

    div[data-testid="stTextInput"] input {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 15px !important;
        padding: 4px 0 !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #8e8f99 !important;
    }

    div[data-testid="stPopover"] button {
        background-color: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        padding: 2px 4px !important;
        border-radius: 8px !important;
    }

    div[data-testid="stButton"] button {
        background-color: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        border-radius: 8px !important;
        padding: 2px 4px !important;
    }

    /* --- ФИКС ЗА ТЕЛЕФОНИ: ТРИТЕ ИКОНКИ ЗАЛЕПЕНИ ВЛЯВО, СТРЕЛКАТА ВДЯСНО --- */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 6px !important;
        width: 100% !important;
    }

    /* Трите иконки вляво: плътно събрани без раздалечаване */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-child(1),
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-child(2),
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-child(3) {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }

    /* Празното място между трите точки и стрелката */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-child(4) {
        flex-grow: 1 !important;
        width: auto !important;
    }

    /* Стрелката най-вдясно */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-child(5) {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }

    @media (max-width: 768px) {
        .hero-title {
            font-size: 1.6rem !important;
            margin-top: 12vh !important;
        }
    }
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# ----------------- ИНИЦИАЛИЗАЦИЯ -----------------
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

if "tool_search" not in st.session_state:
    st.session_state.tool_search = False
if "tool_reasoning" not in st.session_state:
    st.session_state.tool_reasoning = True

if "reg_step" not in st.session_state:
    st.session_state.reg_step = 1
if "target_email" not in st.session_state:
    st.session_state.target_email = ""
if "gen_code" not in st.session_state:
    st.session_state.gen_code = ""

# ----------------- ДИАЛОГ ЗА ВХОД И РЕГИСТРАЦИЯ -----------------
@st.dialog("Вход в профила")
def auth_modal():
    tab_login, tab_reg = st.tabs(["Вход", "Регистрация с код"])
    
    with tab_login:
        email = st.text_input("Имейл", key="auth_login_email")
        password = st.text_input("Парола", type="password", key="auth_login_pass")
        if st.button("Влез", use_container_width=True):
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
                st.warning("Попълнете всички полета.")

    with tab_reg:
        if st.session_state.reg_step == 1:
            st.markdown("Въведете вашия имейл, за да получите код:")
            r_email = st.text_input("Имейл", key="reg_email_input")
            if st.button("📩 Изпрати код", use_container_width=True):
                if r_email and "@" in r_email:
                    c.execute("SELECT id FROM users WHERE email = ?", (r_email.strip().lower(),))
                    if c.fetchone():
                        st.error("Този имейл вече има регистрация!")
                    else:
                        code = str(random.randint(100000, 999999))
                        st.session_state.gen_code = code
                        st.session_state.target_email = r_email.strip().lower()
                        
                        with st.spinner("Изпращане на имейл..."):
                            sent, info = send_email_code(st.session_state.target_email, code)
                            if sent:
                                st.session_state.reg_step = 2
                                st.success("✅ Кодът е изпратен в пощата ви!")
                                st.rerun()
                            else:
                                st.error(f"❌ {info}")
                else:
                    st.warning("Въведете валиден имейл адрес.")
        
        elif st.session_state.reg_step == 2:
            st.markdown(f"Кодът е изпратен на: **{st.session_state.target_email}**")
            entered_code = st.text_input("6-цифрен код от пощата:", key="reg_code_input")
            new_pass = st.text_input("Изберете парола:", type="password", key="reg_pass_input")
            
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                if st.button("Завърши", use_container_width=True):
                    if entered_code.strip() == st.session_state.gen_code:
                        if len(new_pass) >= 4:
                            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (st.session_state.target_email, hash_pass(new_pass)))
                            conn.commit()
                            st.session_state.user_id = c.lastrowid
                            st.session_state.user_email = st.session_state.target_email
                            st.session_state.current_chat_id = None
                            st.session_state.messages = []
                            st.session_state.reg_step = 1
                            st.success("🎉 Регистрацията е готова!")
                            st.rerun()
                        else:
                            st.error("Паролата трябва да е поне 4 символа.")
                    else:
                        st.error("Грешен код!")
            with col_b2:
                if st.button("Назад", use_container_width=True):
                    st.session_state.reg_step = 1
                    st.rerun()

# ----------------- СТРАНИЧНО МЕНЮ (ПРОФИЛ И ИСТОРИЯ) -----------------
with st.sidebar:
    st.markdown("### ⚡ T-Pire AI")
    
    if st.session_state.user_id:
        st.markdown(f"👤 **{st.session_state.user_email}**")
        if st.button("🚪 Изход от профила", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.current_chat_id = None
            st.session_state.messages = []
            st.rerun()
    else:
        st.caption("Влезте, за да пазите историята си:")
        if st.button("🔑 Вход / Регистрация", use_container_width=True):
            auth_modal()
            
    st.divider()

    st.markdown("#### 📁 История на чатовете")
    if st.button("➕ Нов чат", use_container_width=True):
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.rerun()

    if st.session_state.user_id:
        c.execute("SELECT id, title FROM chats WHERE user_id = ? ORDER BY id DESC", (st.session_state.user_id,))
        user_chats = c.fetchall()
        
        if user_chats:
            for ch in user_chats:
                col_c_title, col_c_del = st.columns([4, 1])
                with col_c_title:
                    if st.button(f"💬 {ch[1]}", key=f"chat_{ch[0]}", use_container_width=True):
                        st.session_state.current_chat_id = ch[0]
                        c.execute("SELECT role, content, file_name, file_type, file_bytes FROM messages WHERE chat_id = ? ORDER BY id ASC", (ch[0],))
                        rows = c.fetchall()
                        st.session_state.messages = [{"role": r[0], "content": r[1], "file_name": r[2], "file_type": r[3], "file_bytes": r[4]} for r in rows]
                        st.rerun()
                with col_c_del:
                    if st.button("🗑️", key=f"del_{ch[0]}", help="Изтрий този чат"):
                        c.execute("DELETE FROM messages WHERE chat_id = ?", (ch[0],))
                        c.execute("DELETE FROM chats WHERE id = ?", (ch[0],))
                        conn.commit()
                        if st.session_state.current_chat_id == ch[0]:
                            st.session_state.current_chat_id = None
                            st.session_state.messages = []
                        st.rerun()
            
            st.markdown("---")
            if st.button("⚠️ Изтрий цялата история", use_container_width=True):
                c.execute("SELECT id FROM chats WHERE user_id = ?", (st.session_state.user_id,))
                c_ids = [r[0] for r in c.fetchall()]
                for cid in c_ids:
                    c.execute("DELETE FROM messages WHERE chat_id = ?", (cid,))
                c.execute("DELETE FROM chats WHERE user_id = ?", (st.session_state.user_id,))
                conn.commit()
                st.session_state.current_chat_id = None
                st.session_state.messages = []
                st.rerun()
        else:
            st.caption("Нямате запазени разговори.")
    else:
        st.caption("🔒 *Влезте в профила си, за да виждате и управлявате историята си.*")

# ----------------- ГЛАВЕН ЕКРАН: МОДЕЛ ГОРЕ ВЛЯВО -----------------
col_m, col_sp = st.columns([3, 7])
with col_m:
    model_choice = st.selectbox(
        "Модел",
        ["⚡ T-Pire 3.5 (Бърз)", "🧠 T-Pire 3.8 (Умен)"],
        label_visibility="collapsed"
    )

selected_model = "gemini-3.8-flash" if "3.8" in model_choice else "gemini-3.5-flash-lite"
selected_temp = 0.2 if "3.8" in model_choice else 0.6

# ----------------- СИСТЕМЕН ПРОМПТ -----------------
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

# Фиксиране на бара най-долу при съобщения
if st.session_state.messages:
    st.markdown("""
    <style>
        .main .block-container {
            padding-bottom: 140px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(input[aria-label="Chat"]) {
            position: fixed !important;
            bottom: 15px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: calc(100% - 28px) !important;
            max-width: 740px !important;
            z-index: 9999 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.6) !important;
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

# ----------------- КОМПАКТЕН БАР (СЪБРАНИ ИКОНКИ ВЛЯВО) -----------------
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

    # Колонките: първите три са плътно вляво с CSS, 4-тата е разделител, 5-тата е стрелката вдясно
    col_doc, col_img, col_dots, col_spacer, col_send = st.columns([1, 1, 1, 12, 1])

    with col_doc:
        with st.popover("", icon=":material/note_add:", help="Качи PDF / Документ"):
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
        with st.popover("", icon=":material/more_horiz:", help="Инструменти и опции"):
            st.markdown("**Инструменти на AI:**")
            st.session_state.tool_search = st.toggle("🌐 Търсене в интернет", value=st.session_state.tool_search)
            st.session_state.tool_reasoning = st.toggle("🗣️ Дълбоко разсъждение", value=st.session_state.tool_reasoning)
            st.divider()
            if st.button("🗑️ Изчисти този екран"):
                st.session_state.messages = []
                st.session_state.attached_file = None
                st.session_state.pending_submit = None
                st.rerun()

    with col_send:
        st.button("", icon=":material/arrow_upward:", on_click=submit_action, help="Изпрати")

# ----------------- ИЗПРАЩАНЕ И ОБРАБОТКА -----------------
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
    if st.session_state.tool_search:
        tools.append(types.Tool(google_search=types.GoogleSearch()))

    temp = 0.2 if st.session_state.tool_reasoning else selected_temp

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        max_retries = 3
        reply_text = ""

        for attempt in range(max_retries):
            try:
                spinner_text = "Търсене в Google..." if st.session_state.tool_search else ("Анализиране..." if user_msg_data["file_bytes"] else "Мислене...")
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
