import hashlib
import html
from urllib.parse import unquote, urlsplit

import pandas as pd
import streamlit as st

from utils import (
    attach_embeddings, build_database, decode_text_bytes, fetch_url_text,
    search_bundle, safe_http_url, MAX_DOCUMENT_BYTES, MODEL_ID,
)

st.set_page_config(page_title="Помощник разметчика", layout="centered", page_icon="⚡", initial_sidebar_state="collapsed")

DARK_SaaS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

header[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 15% 20%, rgba(67, 40, 116, 0.25) 0%, transparent 50%),
                radial-gradient(circle at 85% 80%, rgba(29, 78, 216, 0.15) 0%, transparent 50%),
                #09090b !important;
    background-size: 150% 150% !important;
    animation: bg-shift 20s ease-in-out infinite alternate !important;
}

@keyframes bg-shift {
    0% { background-position: 0% 0%; }
    100% { background-position: 100% 100%; }
}

.block-container {
    padding-top: 3rem !important;
    padding-bottom: 4rem !important;
    max-width: 850px !important;
}

/* EXPANDER НАСТРОЕК */
[data-testid="stExpander"] {
    background: rgba(24, 24, 27, 0.45) !important;
    border: 1px solid rgba(63, 63, 70, 0.4) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(10px) !important;
    margin-bottom: 2rem !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    background: transparent !important;
    color: #f4f4f5 !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 16px 20px !important;
    transition: color 0.2s ease;
}
[data-testid="stExpander"] summary:hover { color: #8b5cf6 !important; }
[data-testid="stExpander"] svg { fill: currentColor !important; }

/* КАСТОМИЗАЦИЯ MULTISELECT TAGS */
span[data-baseweb="tag"] {
    background-color: rgba(139, 92, 246, 0.15) !important;
    color: #d8b4fe !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
span[data-baseweb="tag"] svg { fill: #d8b4fe !important; }

/* ПОЛЯ ВВОДА */
div[data-baseweb="input"] > div, div[data-baseweb="base-input"], div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
    background-color: rgba(9, 9, 11, 0.6) !important;
    border: 1px solid rgba(63, 63, 70, 0.5) !important;
    border-radius: 12px !important;
    color: #f4f4f5 !important;
    backdrop-filter: blur(8px);
}
div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.25) !important;
    background-color: rgba(9, 9, 11, 0.8) !important;
}
div[data-testid="stTextInput"] label p, div[data-testid="stNumberInput"] label p, div[data-testid="stTextArea"] label p, div[data-testid="stFileUploader"] label p, div[data-testid="stSelectbox"] label p {
    color: #a1a1aa !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
