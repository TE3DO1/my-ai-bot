import streamlit as st
import time
from google import genai
from google.genai import types

st.set_page_config(page_title="T-Pire", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# ----------------- МОБИЛЕН И ДЕСКТОП CSS (ТОЧНО КАТО НА СНИМКАТА) -----------------
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #17181c;
    }

    /* Модел селектор горе вляво (стил ChatGPT) */
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

    /* ЕДИННАТА ТЪМНА КУТИЯ */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #212227 !important;
        border: 1px solid #2e3038 !important;
        border-radius: 18px !important;
        padding: 10px 14px 6px 14px !important;
    }

    /* Прозрачно текстово поле вътре в кутията */
    div[data-testid="stTextInput"] input {
        background-color: transparent !important;
        border: none !important;
