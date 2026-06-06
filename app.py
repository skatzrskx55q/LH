import html
import pandas as pd
import streamlit as st
from utils import keyword_search, semantic_search, decode_text_bytes, fetch_url_text, parse_txt_cases, get_model

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
    white-space: nowrap; /* Не даем лейблам переноситься на новую строку */
}

/* КОНТЕЙНЕР ПРИЛОЖЕНИЯ */
.app-container { color: #f4f4f5; margin-bottom: 2rem; }

.stats-panel {
    display: flex; justify-content: space-between; align-items: center;
    padding: 16px 20px; margin: 2rem 0 1.5rem;
    background: rgba(24, 24, 27, 0.4); border: 1px solid rgba(63, 63, 70, 0.4);
    border-radius: 16px; backdrop-filter: blur(12px);
}
.stats-title { font-size: 18px; font-weight: 700; color: #ffffff; display: flex; align-items: center; gap: 8px; }
.stats-badge { background: rgba(39, 39, 42, 0.6); padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; color: #d4d4d8; border: 1px solid rgba(82, 82, 91, 0.5); }

/* КАРТОЧКИ (GLASSMORPHISM) */
.modern-card {
    background: rgba(24, 24, 27, 0.45); border: 1px solid rgba(63, 63, 70, 0.4);
    border-radius: 16px; padding: 20px; margin-bottom: 16px;
    transition: all 0.3s ease; position: relative; overflow: hidden; backdrop-filter: blur(10px);
}
.modern-card:hover { transform: translateY(-3px); border-color: rgba(139, 92, 246, 0.4); box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5); background: rgba(24, 24, 27, 0.65); }
.modern-card.is-best { border-color: rgba(139, 92, 246, 0.6); background: linear-gradient(180deg, rgba(139, 92, 246, 0.08) 0%, rgba(24, 24, 27, 0.5) 100%); }
.modern-card.is-best::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #8b5cf6, #3b82f6); }

.card-header { display: flex; gap: 16px; margin-bottom: 16px; }
.card-rank { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: rgba(9, 9, 11, 0.6); border: 1px solid rgba(63, 63, 70, 0.5); border-radius: 10px; font-weight: 800; font-size: 15px; color: #f4f4f5; }
.is-best .card-rank { background: #8b5cf6; color: white; border: none; box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
.card-title { font-size: 17px; font-weight: 600; line-height: 1.4; color: #ffffff; flex: 1; }

.data-grid { display: flex; flex-direction: column; gap: 12px; background: rgba(9, 9, 11, 0.3); border: 1px solid rgba(63, 63, 70, 0.3); border-radius: 12px; padding: 16px; }
.data-row { display: flex; flex-direction: row; gap: 8px; align-items: baseline; flex-wrap: wrap; }
.data-row.stacked { flex-direction: column; align-items: flex-start; gap: 6px; }
.data-label { font-size: 12px; font-weight: 600; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }
.data-row:not(.stacked) .data-label::after { content: ":"; }

.data-value { font-size: 14px; color: #e4e4e7; line-height: 1.6; word-break: break-word; width: 100%; }

.intent-container { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 2px; }
.intent-badge { background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.3); color: #d8b4fe; padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: 500; line-height: 1.4; }
.intent-arrow { color: #71717a; font-size: 14px; }
.score-pill { display: inline-flex; align-items: center; padding: 4px 10px; background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 99px; font-size: 12px; font-weight: 700; margin-top: 12px; }
</style>
"""

def escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def field_row(label, value, stacked: bool = False) -> str:
    lbl = escape(label)
    val = str(value or "-")
    
    val_html = escape(val).replace("\n", "<br>")
    
    if not lbl:
        return f'<div class="data-row stacked"><div class="data-value">{val_html}</div></div>'

    if "→" in val:
        parts = [p.strip() for p in val.split("→")]
        badges_html = "".join(
            f'<div class="intent-badge">{escape(part)}</div><div class="intent-arrow">→</div>' 
            if i < len(parts) - 1 else f'<div class="intent-badge">{escape(part)}</div>' 
            for i, part in enumerate(parts)
        )
        return f'<div class="data-row stacked"><div class="data-label">{lbl}</div><div class="intent-container">{badges_html}</div></div>'
        
    stacked_cls = " stacked" if stacked else ""
    return f'<div class="data-row{stacked_cls}"><div class="data-label">{lbl}</div><div class="data-value">{val_html}</div></div>'


def render_card(item, rank: int, show_score: bool, is_best: bool) -> str:
    fields = list(item.get("fields") or [])
    best_cls = " is-best" if is_best else ""
    title = escape(item.get("title", ""))
    
    html_parts = [
        f'<div class="modern-card{best_cls}">',
        '<div class="card-header">',
        f'<div class="card-rank">{rank}</div>',
        f'<div class="card-title">{title}</div>',
        '</div>',
        '<div class="data-grid">'
    ]

    for field in fields:
        val = field.get("value") or "-"
        lbl = field.get("label", "")
        is_stacked = not lbl or (len(str(val)) > 80 and "→" not in str(val)) or "\n" in str(val)
        html_parts.append(field_row(lbl, val, stacked=is_stacked))

    html_parts.append('</div>')

    if show_score and item.get("score") is not None:
        html_parts.append(f'<div class="score-pill">Score: {item["score"]:.3f}</div>')

    html_parts.append('</div>')
    return "".join(html_parts)


def render_results(title: str, items, total: int, show_scores: bool = False, icon: str = "🔍") -> None:
    html_parts = [
        '<div class="app-container">',
        f'<div class="stats-panel"><div class="stats-title">{icon} {escape(title)}</div><div class="stats-badge">{len(items)} / {total} совпадений</div></div>'
    ]

    if not items:
        html_parts.append('<div class="modern-card" style="text-align:center; color:#a1a1aa; padding: 40px;">Ничего не найдено. Попробуйте другой запрос.</div>')
    else:
        for idx, item in enumerate(items):
            is_best = (show_scores and idx == 0)
            html_parts.append(render_card(item, rank=idx + 1, show_score=show_scores, is_best=is_best))

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


st.markdown(DARK_SaaS_CSS, unsafe_allow_html=True)

# Заголовок
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem; padding-top: 1rem;">
    <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; background: linear-gradient(to right, #ffffff, #a1a1aa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Помощник Разметчика
    </h1>
    <p style="color: #a1a1aa; font-size: 1.1rem;">Интеллектуальный поиск по базе знаний</p>
</div>
""", unsafe_allow_html=True)


# --- ЛОГИКА ЗАГРУЗКИ ДАННЫХ ---
@st.cache_data(show_spinner=False, ttl=3600)
def cached_fetch_url(url: str):
    return fetch_url_text(url)

@st.cache_data(show_spinner=False)
def compile_database(doc_configs: list) -> pd.DataFrame:
    dfs = []
    for cfg in doc_configs:
        records = parse_txt_cases(cfg["text"], cfg["name"], cfg["mode"], cfg["prefixes"])
        if records:
            dfs.append(pd.DataFrame(records))
            
    if not dfs:
        return pd.DataFrame()
        
    df = pd.concat(dfs, ignore_index=True)
    model = get_model()
    df.attrs["phrase_embs"] = model.encode(df["search_proc"].tolist(), convert_to_tensor=True)
    return df


MODE_MAP = {"Авто": "auto", "Ручной": "custom", "Сплошной": "none"}

# --- НАСТРОЙКИ (UX БЛОК) ---
with st.expander("⚙️ Источники данных и настройки парсинга", expanded=True):
    col_upload, col_urls = st.columns([1, 1])
    
    with col_upload:
        uploaded_files = st.file_uploader("📂 Локальные файлы (.txt)", type="txt", accept_multiple_files=True)
    with col_urls:
        default_github = "https://raw.githubusercontent.com/skatzrskx55q/LH/main/Документ 3.txt"
        github_urls_text = st.text_area("🌐 Ссылки на GitHub (.txt)", value=default_github, height=100)

    available_docs = {}
    urls = [u.strip() for u in github_urls_text.split("\n") if u.strip()]
    for url in urls:
        doc_name = url.split("/")[-1] or url
        content = cached_fetch_url(url)
        if content:
            available_docs[doc_name] = content
            
    if uploaded_files:
        for f in uploaded_files:
            available_docs[f.name] = decode_text_bytes(f.getvalue())

    st.markdown("<hr style='border-color: rgba(63, 63, 70, 0.4); margin: 1.5rem 0 1rem;'>", unsafe_allow_html=True)
    
    if not available_docs:
        st.info("Нет доступных документов. Загрузите файл или укажите рабочую ссылку.")
        st.stop()

    all_doc_names = list(available_docs.keys())
    active_docs = st.multiselect("📑 Выберите документы для работы:", options=all_doc_names, default=all_doc_names)

    doc_configs = []
    if active_docs:
        st.markdown("<p style='font-size: 13px; color: #a1a1aa; margin-top: 1rem; margin-bottom: 0.5rem;'>ТОНКАЯ НАСТРОЙКА ПАРСИНГА</p>", unsafe_allow_html=True)
        
        for doc in active_docs:
            c1, c2, c3 = st.columns([1.5, 1, 1.5])
            
            with c1:
                st.markdown(f"<div style='margin-top: 30px; color: #e4e4e7; font-weight: 500; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{escape(doc)}'>📄 {escape(doc)}</div>", unsafe_allow_html=True)
            
            with c2:
                mode_choice = st.selectbox(
                    "Режим", 
                    options=["Авто", "Ручной", "Сплошной"], 
                    key=f"mode_{doc}",
                    index=0
                )
            
            with c3:
                prefs_str = ""
                if mode_choice == "Ручной":
                    prefs_str = st.text_input("Укажите префиксы", "Интенты, Дата, Статья", key=f"pref_{doc}")
                else:
                    st.markdown("<div style='height: 68px;'></div>", unsafe_allow_html=True)
            
            doc_configs.append({
                "name": doc,
                "text": available_docs[doc],
                "mode": MODE_MAP[mode_choice],
                "prefixes": [p.strip() for p in prefs_str.split(",")] if prefs_str else []
            })


# --- СБОРКА БАЗЫ И ПОИСК ---
try:
    with st.spinner("Сборка базы знаний..."):
        df = compile_database(doc_configs)
except Exception as exc:
    st.error(f"Ошибка обработки: {exc}")
    st.stop()

# КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Пропорция [8, 1.1, 1.1] делает строку поиска максимально широкой, 
# а поля ввода чисел узкими и компактными. Подсказки-вопросики (help) вернулись!
query_col, top_k_sem_col, top_k_ex_col = st.columns([8, 1.1, 1.1])

with query_col:
    query = st.text_input("Поисковый запрос", placeholder="Например: ошибка подключения...")
with top_k_sem_col:
    top_k_semantic = st.number_input("Топ (Умный)", min_value=1, max_value=20, value=5, step=1")
with top_k_ex_col:
    top_k_exact = st.number_input("Топ (Точный)", min_value=1, max_value=20, value=5, step=1, help="Выдача для точного поиска")

if df.empty:
    st.warning("⚠️ База пуста или выбранные документы не содержат корректных данных для поиска (например, нет меток ==заголовок==).")
    st.stop()

if not query.strip():
    st.stop()

case_count = df["case_uid"].nunique()

with st.spinner("Анализ данных..."):
    semantic_results = semantic_search(query, df, top_k=top_k_semantic)
    exact_results = keyword_search(query, df, top_k=top_k_exact)

render_results("Умный поиск (Семантика)", semantic_results, total=case_count, show_scores=True, icon="✨")
render_results("Точный поиск (Ключи)", exact_results, total=case_count, show_scores=False, icon="🎯")
