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
    <div class="top-
