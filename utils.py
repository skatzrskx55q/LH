"""Парсинг, безопасная загрузка и гибридный поиск. Python 3.10+."""
import functools
import re
import threading
from collections import Counter, defaultdict
from itertools import islice, product
from urllib.parse import urljoin, urlsplit, urlunsplit

import numpy as np
import pandas as pd
import streamlit as st

MODEL_ID = "skatzR/USER-BGE-M3-MiniLM-L12-v2-Distilled"
REQUEST_TIMEOUT_SECONDS = 30
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_VARIANTS = 256
CASE_MARKER_RE = re.compile(r"==\s*(?P<title>.*?)\s*==", re.DOTALL)
SERVICE_FIELD_RE = re.compile(r"^\s*(?P<label>[^:\n]{1,80})\s*:\s*(?P<value>.*)$")
TOKEN_RE = re.compile(r"\w+", re.UNICODE)


@st.cache_resource(show_spinner=False)
def get_model(model_id=MODEL_ID):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_id, trust_remote_code=False)


@st.cache_resource(show_spinner=False)
def model_lock():
    # Модель и токенизатор используются несколькими сессиями Streamlit.
    return threading.RLock()


@st.cache_resource(show_spinner=False)
def get_morph():
    import pymorphy3
    return pymorphy3.MorphAnalyzer()


def normalize_spaces(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def preprocess(text):
    return normalize_spaces(text).casefold().replace("ё", "е")


def normalize_line_endings(text):
    return str(text or "").replace("\r\n", "\n").replace("\r", "\n")


def tokenize(text):
    return tuple(TOKEN_RE.findall(preprocess(text)))


@functools.lru_cache(maxsize=50000)
def lemmatize_cached(word):
    return get_morph().parse(word)[0].normal_form if word.isalpha() else word


def lemmatize(word):
    return lemmatize_cached(word)


def decode_text_bytes(content):
    if len(content) > MAX_DOCUMENT_BYTES:
        raise ValueError("Размер документа превышает 5 МБ.")
    for encoding in ("utf-8-sig", "cp1251", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Не удалось определить кодировку документа.")


def safe_http_url(value):
    """Проверяет адрес для отображения ссылки; ничего не скачивает."""
    value = str(value or "").strip(" ")
    if not value or re.search(r"""[\s\x00-\x1f\x7f<>"'\\]""", value):
        return None
    try:
        parts = urlsplit(value)
        if (parts.scheme.lower() not in {"http", "https"} or not parts.hostname
                or parts.username is not None or parts.password is not None):
            return None
        _ = parts.port  # отклоняет некорректный порт
        return value
    except ValueError:
        return None


def validate_source_url(url):
    url = str(url).strip()
    if not safe_http_url(url):
        raise ValueError("Некорректный URL источника.")
    parts = urlsplit(url)
