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

/* АНИМИРОВАННЫЙ ГРАДИЕНТНЫЙ ФОН ПРИЛОЖЕНИЯ */
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
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 850px !important;
}

/* КАСТОМИЗАЦИЯ ПОЛЕЙ ВВОДА */
div[data-baseweb="input"] > div, 
div[data-baseweb="base-input"] {
    background-color: rgba(24, 24, 27, 0.7) !important;
    border: 1px solid rgba(63, 63, 70, 0.5) !important;
    border-radius: 12px !important;
    color: #f4f4f5 !important;
    backdrop-filter: blur(8px);
}

div[data-baseweb="input"] > div:focus-within {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.25) !important;
    background-color: rgba(9, 9, 11, 0.8) !important;
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

/* КОНТЕЙНЕР ПРИЛОЖЕНИЯ */
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
    background: rgba(24, 24, 27, 0.4);
    border: 1px solid rgba(63, 63, 70, 0.4);
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
    background: rgba(39, 39, 42, 0.6);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    color: #d4d4d8;
    border: 1px solid rgba(82, 82, 91, 0.5);
}

/* КАРТОЧКА РЕЗУЛЬТАТА (GLASSMORPHISM) */
.modern-card {
    background: rgba(24, 24, 27, 0.45);
    border: 1px solid rgba(63, 63, 70, 0.4);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.modern-card:hover {
    transform: translateY(-3px);
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    background: rgba(24, 24, 27, 0.65);
}

.modern-card.is-best {
    border-color: rgba(139, 92, 246, 0.6);
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.08) 0%, rgba(24, 24, 27, 0.5) 100%);
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
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(9, 9, 11, 0.6);
    border: 1px solid rgba(63, 63, 70, 0.5);
    border-radius: 10px;
    font-weight: 800;
    font-size: 15px;
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

/* СЕТКА ДАННЫХ И КОМПАКТНЫЕ ОТСТУПЫ */
.data-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
    background: rgba(9, 9, 11, 0.3);
    border: 1px solid rgba(63, 63, 70, 0.3);
    border-radius: 12px;
    padding: 16px;
}

.data-row {
    display: flex;
    flex-direction: row;
    gap: 8px;
    align-items: baseline;
    flex-wrap: wrap; /* Позволяет переносить длинный текст */
}

.data-row.stacked {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
}

.data-label {
    font-size: 12px;
    font-weight: 600;
    color: #a1a1aa;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap; /* Лейбл не рвется на части */
}

/* Добавляем двоеточие для полей в одну строку (например: Дата: 19.09.25) */
.data-row:not(.stacked) .data-label::after {
    content: ":";
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

/* СТИЛИ ДЛЯ ИНТЕНТОВ (БЕЙДЖИ) */
.intent-container {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-top: 2px;
}

.intent-badge {
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.3);
    color: #d8b4fe;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    line-height: 1.4;
}

.intent-arrow {
    color: #71717a;
    font-size: 14px;
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
    val = str(value or "-")
    
    # МАГИЯ ДЛЯ ИНТЕНТОВ: Если в тексте есть стрелочка, парсим это в красивые бейджи
    if "→" in val:
        parts = [p.strip() for p in val.split("→")]
        # Генерируем бейджи в один цикл
        badges_html = "".join(
            f'<div class="intent-badge">{escape(part)}</div><div class="intent-arrow">→</div>' 
            if i < len(parts) - 1 else f'<div class="intent-badge">{escape(part)}</div>' 
            for i, part in enumerate(parts)
        )
        # Интенты всегда делаем колонкой (stacked), чтобы бейджам было просторно
        return f'<div class="data-row stacked"><div class="data-label">{lbl}</div><div class="intent-container">{badges_html}</div></div>'
        
    # Обычное поле (например, "Дата: 19.09.2025")
    val_esc = escape(val)
    stacked_cls = " stacked" if stacked else ""
    return f'<div class="data-row{stacked_cls}"><div class="data-label">{lbl}</div><div class="data-value"><pre>{val_esc}</pre></div></div>'


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
        # Ставим флаг stacked, только если текст реально длинный и в нем нет стрелочек (стрелочки обрабатываются отдельно)
        is_stacked = (len(str(val)) > 80 and "→" not in str(val)) or "\n" in str(val)
        html_parts.append(field_row(field.get("label", "Поле"), val, stacked=is_stacked))

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
