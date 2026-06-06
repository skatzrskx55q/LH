import html
import streamlit as st
from utils import keyword_search, load_all_txts, semantic_search

st.set_page_config(page_title="Помощник разметчика", layout="centered", page_icon="⚡")

DARK_SaaS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

header {display: none !important;}
footer {display: none !important;}
.stDeployButton {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 850px !important;
}

div[data-baseweb="input"] > div, 
div[data-baseweb="base-input"] {
    background-color: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 12px !important;
    color: #f4f4f5 !important;
    transition: all 0.2s ease;
}

div[data-baseweb="input"] > div:focus-within {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.25) !important;
    background-color: #09090b !important;
}

div[data-testid="stTextInput"] label p, 
div[data-testid="stNumberInput"] label p {
    color: #a1a1aa !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.app-container {
    color: #f4f4f5;
    margin-bottom: 2rem;
}

.stats-panel {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    margin: 2rem 0 1.5rem;
    background: rgba(24, 24, 27, 0.6);
    border: 1px solid #27272a;
    border-radius: 16px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
.stats-title {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
}
.stats-badge {
    background: #27272a;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    color: #a1a1aa;
    border: 1px solid #3f3f46;
}

.modern-card {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    position: relative;
    overflow: hidden;
}
.modern-card:hover {
    transform: translateY(-4px);
    border-color: #3f3f46;
    box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.5);
}

.modern-card.is-best {
    border-color: #8b5cf6;
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.05) 0%, #18181b 100%);
}
.modern-card.is-best::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #8b5cf6, #3b82f6);
}

.card-header {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}
.card-rank {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #09090b;
    border: 1px solid #27272a;
    border-radius: 12px;
    font-weight: 800;
    font-size: 16px;
    color: #f4f4f5;
}
.is-best .card-rank {
    background: #8b5cf6;
    color: white;
    border: none;
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
}
.card-title {
    font-size: 17px;
    font-weight: 600;
    line-height: 1.4;
    color: #ffffff;
    flex: 1;
}

.data-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: #09090b;
    border: 1px solid #27272a;
    border-radius: 12px;
    padding: 16px;
}
.data-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
@media(min-width: 640px) {
    .data-row {
        flex-direction: row;
        align-items: baseline;
        gap: 16px;
    }
    .data-label {
        width: 140px;
        flex-shrink: 0;
    }
}
.data-row.stacked {
    flex-direction: column;
}
.data-label {
    font-size: 12px;
    font-weight: 600;
    color: #71717a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.data-value {
    font-size: 14px;
    color: #e4e4e7;
    line-height: 1.6;
    word-break: break-word;
}
.data-value pre {
    white-space: pre-wrap;
    font-family: inherit;
    margin: 0;
}

.score-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    background: rgba(16, 185, 129, 0.1);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 99px;
    font-size: 12px;
    font-weight: 700;
    margin-top: 12px;
}
</style>
"""


def escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def field_row(label, value, stacked: bool = False) -> str:
    lbl = escape(label)
    val = escape(str(value or "-"))
    stacked_cls = " stacked" if stacked else ""
    # Весь HTML генерируется в одну строку без отступов, чтобы Streamlit не сломал его
    return f'<div class="data-row{stacked_cls}"><div class="data-label">{lbl}</div><div class="data-value"><pre>{val}</pre></div></div>'


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
        is_stacked = len(str(val)) > 80 or "\n" in str(val)
        html_parts.append(field_row(field.get("label", "Поле"), val, stacked=is_stacked))

    html_parts.append('</div>')

    if show_score and item.get("score") is not None:
        html_parts.append(f'<div class="score-pill">Score: {item["score"]:.3f}</div>')

    html_parts.append('</div>')
    # Склеиваем без переносов строк (newline), чтобы избежать конфликта с Markdown
    return "".join(html_parts)


def render_results(title: str, items, total: int, show_scores: bool = False, icon: str = "🔍") -> None:
    html_parts = [
        '<div class="app-container">',
        f'<div class="stats-panel"><div class="stats-title">{icon} {escape(title)}</div><div class="stats-badge">{len(items)} / {total} совпадений</div></div>'
    ]

    if not items:
        html_parts.append('<div class="modern-card" style="text-align:center; color:#a1a1aa; padding: 40px;">Нет данных по вашему запросу.</div>')
    else:
        for idx, item in enumerate(items):
            is_best = (show_scores and idx == 0)
            html_parts.append(render_card(item, rank=idx + 1, show_score=show_scores, is_best=is_best))

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


st.markdown(DARK_SaaS_CSS, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_data():
    return load_all_txts()

st.markdown("""
<div style="text-align: center; margin-bottom: 3rem; padding-top: 1rem;">
    <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; background: linear-gradient(to right, #ffffff, #a1a1aa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Помощник Разметчика
    </h1>
    <p style="color: #a1a1aa; font-size: 1.1rem;">Интеллектуальный поиск по базе знаний</p>
</div>
""", unsafe_allow_html=True)

try:
    with st.spinner("Синхронизация с базой..."):
        df = get_data()
except Exception as exc:
    st.error(f"Сбой загрузки: {exc}")
    st.stop()

case_count = df["case_uid"].nunique()

query_col, top_k_col = st.columns([4, 1])
with query_col:
    query = st.text_input("Поисковый запрос", placeholder="Введите текст, ошибку или ключевые слова...")
with top_k_col:
    top_k = st.number_input("Выдача", min_value=1, max_value=20, value=5, step=1)

if not query.strip():
    st.stop()

with st.spinner("Анализ данных..."):
    semantic_results = semantic_search(query, df, top_k=top_k)
    exact_results = keyword_search(query, df, top_k=top_k)

render_results("Умный поиск (Семантика)", semantic_results, total=case_count, show_scores=True, icon="✨")
render_results("Точный поиск (Ключи)", exact_results, total=case_count, show_scores=False, icon="🎯")
