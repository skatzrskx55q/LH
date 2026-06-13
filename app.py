import html
import pandas as pd
import streamlit as st
from utils import keyword_search, semantic_search, decode_text_bytes, fetch_url_text, parse_txt_cases, get_model

st.set_page_config(
    page_title="Помощник разметчика",
    layout="centered",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

PREMIUM_CSS = """
<style>
@import url('https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,600,700,800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ─── DESIGN TOKENS ─────────────────────────────────────────── */
:root {
    --font-body:    'Satoshi', 'Inter', system-ui, sans-serif;
    --font-mono:    'JetBrains Mono', 'Fira Code', monospace;

    --bg:           #0a0a0c;
    --surface-0:    #0d0d10;
    --surface-1:    #111116;
    --surface-2:    #16161c;
    --surface-3:    #1c1c24;
    --border:       rgba(255,255,255,0.06);
    --border-hover: rgba(255,255,255,0.12);
    --divider:      rgba(255,255,255,0.04);

    --text-primary:   #f0f0f2;
    --text-secondary: #8b8b9e;
    --text-muted:     #52526a;

    --accent:         #7c6ff7;
    --accent-dim:     rgba(124, 111, 247, 0.12);
    --accent-glow:    rgba(124, 111, 247, 0.20);
    --accent-border:  rgba(124, 111, 247, 0.30);

    --green:          #34d399;
    --green-dim:      rgba(52, 211, 153, 0.10);
    --green-border:   rgba(52, 211, 153, 0.20);

    --r-sm:  6px;  --r-md:  10px; --r-lg:  14px;
    --r-xl:  18px; --r-2xl: 24px;
    --ease: cubic-bezier(0.16, 1, 0.3, 1);
    --dur:  220ms;
}

html, body, [class*="css"] {
    font-family: var(--font-body) !important;
    -webkit-font-smoothing: antialiased;
}

header[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
footer { display: none !important; }

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 10% 5%,  rgba(124,111,247,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 95%, rgba(99,102,241,0.05)  0%, transparent 55%),
        var(--bg) !important;
    min-height: 100dvh;
}

.block-container {
    padding-top: 3.5rem !important;
    padding-bottom: 5rem !important;
    max-width: 880px !important;
}

[data-testid="stExpander"] {
    background: var(--surface-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-2xl) !important;
    backdrop-filter: blur(16px) !important;
    margin-bottom: 2rem !important;
    overflow: hidden;
    transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}
[data-testid="stExpander"]:focus-within {
    border-color: var(--accent-border) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}
[data-testid="stExpander"] summary {
    background: transparent !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.01em;
    padding: 18px 22px !important;
    transition: color var(--dur) var(--ease);
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }
[data-testid="stExpander"] > div > div[role="group"] { padding: 0 22px 22px !important; }
[data-testid="stExpander"] svg { fill: currentColor !important; }

span[data-baseweb="tag"] {
    background: var(--accent-dim) !important;
    color: #b4aeff !important;
    border: 1px solid var(--accent-border) !important;
    border-radius: var(--r-md) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 3px 10px !important;
    letter-spacing: 0.01em;
}
span[data-baseweb="tag"] svg { fill: #b4aeff !important; }

div[data-baseweb="input"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-lg) !important;
    color: var(--text-primary) !important;
    font-size: 14px !important;
    transition: border-color var(--dur) var(--ease),
                box-shadow var(--dur) var(--ease),
                background var(--dur) var(--ease);
}
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within {
    border-color: var(--accent-border) !important;
    box-shadow: 0 0 0 3px var(--accent-glow), inset 0 1px 0 rgba(255,255,255,0.04) !important;
    background: var(--surface-3) !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="base-input"] input {
    color: var(--text-primary) !important;
    font-size: 14px !important;
}
input::placeholder { color: var(--text-muted) !important; }

div[data-testid="stTextInput"] label p,
div[data-testid="stNumberInput"] label p,
div[data-testid="stTextArea"] label p,
div[data-testid="stFileUploader"] label p,
div[data-testid="stSelectbox"] label p,
div[data-testid="stMultiSelect"] label p {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 6px !important;
    white-space: nowrap;
}

[data-testid="stFileUploader"] section {
    background: var(--surface-2) !important;
    border: 1px dashed var(--border) !important;
    border-radius: var(--r-lg) !important;
    transition: border-color var(--dur) var(--ease), background var(--dur) var(--ease);
}
[data-testid="stFileUploader"] section:hover {
    border-color: var(--accent-border) !important;
    background: var(--surface-3) !important;
}
[data-testid="stFileUploader"] section p { color: var(--text-secondary) !important; font-size: 13px !important; }

[data-testid="stAlert"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-lg) !important;
    color: var(--text-secondary) !important;
    font-size: 13px !important;
}

hr { border: none !important; border-top: 1px solid var(--divider) !important; margin: 1.5rem 0 !important; }

.app-root { color: var(--text-primary); font-family: var(--font-body); }

.page-header {
    display: flex; flex-direction: column; align-items: center;
    text-align: center; margin-bottom: 2.5rem; padding-top: 0.5rem; gap: 10px;
}
.header-eyebrow {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--accent-dim); border: 1px solid var(--accent-border);
    border-radius: 99px; padding: 4px 14px;
    font-size: 11px; font-weight: 700; color: #b4aeff;
    letter-spacing: 0.06em; text-transform: uppercase;
}
.header-eyebrow .dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 6px var(--accent);
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.7); }
}
.header-title {
    font-size: clamp(2rem, 5vw, 2.75rem);
    font-weight: 800; line-height: 1.1; letter-spacing: -0.03em;
    color: transparent;
    background: linear-gradient(135deg, #ffffff 0%, #c4bfff 50%, #8b7ff5 100%);
    -webkit-background-clip: text; background-clip: text; margin: 0;
}
.header-sub {
    font-size: 15px; color: var(--text-secondary);
    font-weight: 400; margin: 0; max-width: 42ch;
}

.results-header {
    display: flex; align-items: center; justify-content: space-between;
    margin: 2rem 0 1rem; padding-bottom: 12px;
    border-bottom: 1px solid var(--divider);
}
.results-title {
    display: flex; align-items: center; gap: 10px;
    font-size: 15px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em;
}
.results-icon {
    width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
    background: var(--accent-dim); border: 1px solid var(--accent-border);
    border-radius: var(--r-md); font-size: 14px; flex-shrink: 0;
}
.results-meta {
    font-size: 12px; font-weight: 500; color: var(--text-muted);
    background: var(--surface-2); border: 1px solid var(--border);
    padding: 4px 12px; border-radius: 99px; letter-spacing: 0.02em;
}

.empty-state {
    text-align: center; padding: 48px 24px; color: var(--text-muted);
    font-size: 14px; background: var(--surface-1);
    border: 1px solid var(--border); border-radius: var(--r-xl);
}
.empty-icon { font-size: 28px; margin-bottom: 12px; opacity: 0.5; }
.empty-label { font-size: 15px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }

.r-card {
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: var(--r-xl); padding: 20px; margin-bottom: 10px;
    position: relative; overflow: hidden;
    transition: border-color var(--dur) var(--ease),
                box-shadow var(--dur) var(--ease),
                background var(--dur) var(--ease),
                transform var(--dur) var(--ease);
}
.r-card:hover {
    border-color: var(--border-hover);
    box-shadow: 0 8px 24px -8px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
    background: var(--surface-2); transform: translateY(-2px);
}
.r-card.top-result {
    border-color: rgba(124,111,247,0.25);
    background: linear-gradient(160deg, rgba(124,111,247,0.06) 0%, var(--surface-1) 60%);
}
.r-card.top-result::after {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent); opacity: 0.6;
}

.c-header { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 16px; }
.c-rank {
    width: 32px; height: 32px; min-width: 32px;
    display: flex; align-items: center; justify-content: center;
    border-radius: var(--r-md); font-family: var(--font-mono);
    font-weight: 600; font-size: 13px; line-height: 1;
    background: var(--surface-3); border: 1px solid var(--border);
    color: var(--text-secondary); flex-shrink: 0;
}
.top-result .c-rank {
    background: var(--accent-dim); border-color: var(--accent-border); color: var(--accent);
}
.c-title { font-size: 15px; font-weight: 600; color: var(--text-primary); line-height: 1.45; flex: 1; letter-spacing: -0.01em; }

.c-data {
    background: rgba(0,0,0,0.2); border: 1px solid var(--divider);
    border-radius: var(--r-lg); padding: 14px 16px;
    display: flex; flex-direction: column; gap: 10px;
}
.d-row { display: flex; gap: 10px; align-items: baseline; }
.d-row.stacked { flex-direction: column; gap: 5px; }
.d-label {
    font-size: 11px; font-weight: 700; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.07em;
    white-space: nowrap; flex-shrink: 0; padding-top: 1px;
}
.d-row:not(.stacked) .d-label::after { content: ":"; }
.d-value { font-size: 13px; color: #b8b8cc; line-height: 1.6; word-break: break-word; width: 100%; }

.intent-wrap { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 2px; }
.i-badge {
    background: var(--accent-dim); border: 1px solid var(--accent-border);
    color: #b4aeff; padding: 3px 10px; border-radius: var(--r-md);
    font-size: 12px; font-weight: 500; line-height: 1.5;
}
.i-arrow { color: var(--text-muted); font-size: 13px; font-weight: 700; }

.score-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: var(--green-dim); border: 1px solid var(--green-border);
    color: var(--green); padding: 3px 10px; border-radius: 99px;
    font-size: 11px; font-weight: 700; font-family: var(--font-mono);
    letter-spacing: 0.02em; margin-top: 14px;
}
.score-badge::before {
    content: ''; width: 5px; height: 5px;
    border-radius: 50%; background: var(--green);
}

.section-gap { margin-top: 2.5rem; }

div[data-testid="stNumberInput"] button {
    background: var(--surface-3) !important; border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important; border-radius: var(--r-sm) !important;
    transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
}
div[data-testid="stNumberInput"] button:hover {
    background: var(--accent-dim) !important; color: var(--accent) !important;
    border-color: var(--accent-border) !important;
}
</style>
"""

def escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def field_row(label: str, value, stacked: bool = False) -> str:
    lbl = escape(label)
    val = str(value or "-")
    val_html = escape(val).replace("\n", "<br>")

    if not lbl:
        return f'<div class="d-row stacked"><div class="d-value">{val_html}</div></div>'

    if "→" in val:
        parts = [p.strip() for p in val.split("→")]
        badges = "".join(
            f'<div class="i-badge">{escape(p)}</div><div class="i-arrow">→</div>'
            if i < len(parts) - 1
            else f'<div class="i-badge">{escape(p)}</div>'
            for i, p in enumerate(parts)
        )
        return (
            f'<div class="d-row stacked">'
            f'<div class="d-label">{lbl}</div>'
            f'<div class="intent-wrap">{badges}</div>'
            f'</div>'
        )

    cls = " stacked" if stacked else ""
    return (
        f'<div class="d-row{cls}">'
        f'<div class="d-label">{lbl}</div>'
        f'<div class="d-value">{val_html}</div>'
        f'</div>'
    )


def render_card(item: dict, rank: int, show_score: bool, is_best: bool) -> str:
    fields = list(item.get("fields") or [])
    top_cls = " top-result" if is_best else ""
    title = escape(item.get("title", ""))

    parts = [
        f'<div class="r-card{top_cls}">',
        '<div class="c-header">',
        f'<div class="c-rank">{rank:02d}</div>',
        f'<div class="c-title">{title}</div>',
        '</div>',
        '<div class="c-data">',
    ]

    for field in fields:
        val = field.get("value") or "-"
        lbl = field.get("label", "")
        is_stacked = (
            not lbl
            or (len(str(val)) > 80 and "→" not in str(val))
            or "\n" in str(val)
        )
        parts.append(field_row(lbl, val, stacked=is_stacked))

    parts.append('</div>')

    if show_score and item.get("score") is not None:
        parts.append(f'<div class="score-badge">score {item["score"]:.3f}</div>')

    parts.append('</div>')
    return "".join(parts)


def render_results(title: str, items, total: int, show_scores: bool = False, icon: str = "🔍") -> None:
    found = len(items)

    empty_html = (
        '<div class="empty-state">'
        '<div class="empty-icon">🔭</div>'
        '<div class="empty-label">Ничего не найдено</div>'
        'Попробуйте изменить запрос или расширить базу знаний.'
        '</div>'
    )

    cards_html = "".join(
        render_card(item, rank=i + 1, show_score=show_scores, is_best=(show_scores and i == 0))
        for i, item in enumerate(items)
    )

    html_out = f"""
<div class="app-root section-gap">
  <div class="results-header">
    <div class="results-title">
      <div class="results-icon">{icon}</div>
      {escape(title)}
    </div>
    <div class="results-meta">{found}&thinsp;/&thinsp;{total} совпадений</div>
  </div>
  {empty_html if not items else cards_html}
</div>
"""
    st.markdown(html_out, unsafe_allow_html=True)


# ── INJECT CSS ──────────────────────────────────────────────────
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

# ── PAGE HEADER ─────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="header-eyebrow"><span class="dot"></span>AI · Semantic Search</div>
  <h1 class="header-title">Помощник Разметчика</h1>
  <p class="header-sub">Семантический и ключевой поиск по базе знаний</p>
</div>
""", unsafe_allow_html=True)


# ── DATA LOADING ────────────────────────────────────────────────
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

# ── SETTINGS EXPANDER ───────────────────────────────────────────
with st.expander("⚙️  Источники данных и настройки парсинга", expanded=True):
    col_upload, col_urls = st.columns([1, 1])

    with col_upload:
        uploaded_files = st.file_uploader(
            "Локальные файлы (.txt)",
            type="txt",
            accept_multiple_files=True,
        )
    with col_urls:
        default_github = "https://raw.githubusercontent.com/skatzrskx55q/LH/main/Документ 3.txt"
        github_urls_text = st.text_area(
            "Ссылки на GitHub (.txt)",
            value=default_github,
            height=98,
        )

    available_docs: dict = {}
    for url in [u.strip() for u in github_urls_text.split("\n") if u.strip()]:
        doc_name = url.split("/")[-1] or url
        content = cached_fetch_url(url)
        if content:
            available_docs[doc_name] = content

    if uploaded_files:
        for f in uploaded_files:
            available_docs[f.name] = decode_text_bytes(f.getvalue())

    st.markdown(
        "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.05);margin:1.25rem 0 1rem;'>",
        unsafe_allow_html=True,
    )

    if not available_docs:
        st.info("Нет доступных документов. Загрузите файл или укажите рабочую ссылку.")
        st.stop()

    all_doc_names = list(available_docs.keys())
    active_docs = st.multiselect(
        "Документы для работы",
        options=all_doc_names,
        default=all_doc_names,
    )

    doc_configs = []
    if active_docs:
        st.markdown(
            "<p style='font-size:11px;font-weight:700;color:var(--text-muted,#52526a);"
            "text-transform:uppercase;letter-spacing:0.07em;margin:1.25rem 0 0.5rem;'>"
            "Настройка парсинга</p>",
            unsafe_allow_html=True,
        )

        for doc in active_docs:
            c1, c2, c3 = st.columns([1.6, 1, 1.5])

            with c1:
                st.markdown(
                    f"<div style='margin-top:30px;color:#b8b8cc;font-weight:500;font-size:13px;"
                    f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;' title='{escape(doc)}'>"
                    f"📄 {escape(doc)}</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                mode_choice = st.selectbox(
                    "Режим",
                    options=["Авто", "Ручной", "Сплошной"],
                    key=f"mode_{doc}",
                    index=0,
                )
            with c3:
                prefs_str = ""
                if mode_choice == "Ручной":
                    prefs_str = st.text_input(
                        "Префиксы",
                        "Интенты, Дата, Статья",
                        key=f"pref_{doc}",
                    )
                else:
                    st.markdown("<div style='height:68px;'></div>", unsafe_allow_html=True)

            doc_configs.append({
                "name": doc,
                "text": available_docs[doc],
                "mode": MODE_MAP[mode_choice],
                "prefixes": [p.strip() for p in prefs_str.split(",")] if prefs_str else [],
            })


# ── BUILD DB ────────────────────────────────────────────────────
try:
    with st.spinner("Сборка базы знаний…"):
        df = compile_database(doc_configs)
except Exception as exc:
    st.error(f"Ошибка обработки: {exc}")
    st.stop()

# ── SEARCH BAR ──────────────────────────────────────────────────
query_col, top_k_sem_col, top_k_ex_col = st.columns([8, 1.1, 1.1])

with query_col:
    query = st.text_input("Поисковый запрос", placeholder="Например: ошибка подключения…")
with top_k_sem_col:
    top_k_semantic = st.number_input("Топ (Умный)", min_value=1, max_value=20, value=5, step=1)
with top_k_ex_col:
    top_k_exact = st.number_input("Топ (Точный)", min_value=1, max_value=20, value=5, step=1)

# ── GUARDS ──────────────────────────────────────────────────────
if df.empty:
    st.warning("⚠️ База пуста или выбранные документы не содержат данных (нет меток ==заголовок==).")
    st.stop()

if not query.strip():
    st.stop()

case_count = df["case_uid"].nunique()

# ── SEARCH + RENDER ─────────────────────────────────────────────
with st.spinner("Анализ…"):
    semantic_results = semantic_search(query, df, top_k=top_k_semantic)
    exact_results    = keyword_search(query, df, top_k=top_k_exact)

render_results("Умный поиск", semantic_results, total=case_count, show_scores=True, icon="✦")
render_results("Точный поиск", exact_results,   total=case_count, show_scores=False, icon="◎")
