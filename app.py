import html
import streamlit as st
from utils import keyword_search, load_all_txts, semantic_search

# Настройка страницы (должна быть первой командой)
st.set_page_config(page_title="Помощник разметчика", layout="centered", page_icon="✨")

# Современный, прокачанный CSS
CARD_CSS = """
<style>
/* Подключаем современный шрифт */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Скрываем дефолтный UI Streamlit для чистоты интерфейса */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 2rem !important; padding-bottom: 2rem !important;}

/* Глобальные стили контейнера */
.cpp-chunk-parser, .cpp-chunk-parser * {
    box-sizing: border-box;
    font-family: 'Inter', sans-serif !important;
}
.cpp-chunk-parser {
    color: var(--text-color);
    margin-bottom: 2rem;
}

/* Заголовок секции результатов */
.cpp-chunk-parser__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px 24px;
    margin: 0 0 20px;
    border: 1px solid rgba(128, 128, 128, 0.15);
    border-radius: 20px;
    background: var(--secondary-background-color);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    backdrop-filter: blur(10px);
}
.cpp-chunk-parser__title {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: -webkit-linear-gradient(45deg, var(--primary-color), #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.cpp-chunk-parser__meta {
    padding: 6px 14px;
    border-radius: 999px;
    background: rgba(128, 128, 128, 0.1);
    font-size: 13px;
    font-weight: 500;
}

/* Пустое состояние */
.cpp-empty {
    padding: 30px;
    text-align: center;
    border: 2px dashed rgba(128, 128, 128, 0.2);
    border-radius: 20px;
    color: rgba(128, 128, 128, 0.8);
    font-size: 15px;
    font-weight: 500;
}

/* Базовая карточка */
.cpp-card {
    padding: 20px;
    margin: 0 0 16px;
    border: 1px solid rgba(128, 128, 128, 0.15);
    border-radius: 20px;
    background: var(--background-color);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.cpp-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.15);
    border-color: rgba(128, 128, 128, 0.3);
}

/* Выделение лучшего совпадения */
.cpp-card--best {
    border: 2px solid var(--primary-color);
    background: linear-gradient(145deg, rgba(var(--primary-color-rgb), 0.05) 0%, transparent 100%);
}
.cpp-card--best:hover {
    box-shadow: 0 12px 20px -8px rgba(var(--primary-color-rgb), 0.3);
    border-color: var(--primary-color);
}

/* Топ карточки (Ранг + Заголовок + Бейдж) */
.cpp-card__top {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 16px;
}
.cpp-rank {
    flex: 0 0 auto;
    width: 36px;
    height: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: var(--secondary-background-color);
    font-size: 14px;
    font-weight: 800;
    color: var(--text-color);
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
}
.cpp-card--best .cpp-rank {
    background: var(--primary-color);
    color: white;
    box-shadow: 0 4px 10px rgba(var(--primary-color-rgb), 0.4);
}
.cpp-card__head {
    flex: 1;
    min-width: 0;
}
.cpp-card__title {
    margin-bottom: 8px;
}
.cpp-card__title-line {
    font-size: 16px;
    line-height: 1.4;
    font-weight: 700;
}

/* Бейдж */
.cpp-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 8px;
    background: rgba(var(--primary-color-rgb), 0.15);
    color: var(--primary-color);
    font-size: 12px;
    font-weight: 700;
}

/* Сетка полей (Ключ-Значение) */
.cpp-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: var(--secondary-background-color);
    padding: 16px;
    border-radius: 16px;
}
.cpp-row {
    display: grid;
    grid-template-columns: minmax(120px, 140px) minmax(0, 1fr);
    gap: 12px;
    align-items: baseline;
}
.cpp-row--stacked {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px;
}
.cpp-label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: rgba(128, 128, 128, 0.8);
}
.cpp-value {
    font-size: 14px;
    line-height: 1.6;
    font-weight: 500;
    color: var(--text-color);
    word-break: break-word;
}
.cpp-value__line {
    white-space: pre-wrap;
}
.cpp-value__line + .cpp-value__line {
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px dashed rgba(128, 128, 128, 0.2);
}

/* Адаптивность для мобильных */
@media(max-width: 640px) {
    .cpp-chunk-parser__header {
        flex-direction: column;
        align-items: flex-start;
        border-radius: 16px;
    }
    .cpp-row {
        grid-template-columns: 1fr;
        gap: 4px;
    }
    .cpp-card__top {
        flex-direction: column;
    }
}
</style>
"""


def escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def render_value(value) -> str:
    lines = [line.strip() for line in str(value or "").split("\n") if line.strip()]
    if not lines:
        return "-"
    if len(lines) == 1:
        return escape(lines[0])
    return "".join(f'<div class="cpp-value__line">{escape(line)}</div>' for line in lines)


def field_row(label, value, stacked: bool = False) -> str:
    label_html = escape(label)
    value_html = render_value(value)

    stacked_class = " cpp-row--stacked" if stacked else ""
    return (
        f'<div class="cpp-row{stacked_class}">'
        f'<div class="cpp-label">{label_html}</div>'
        f'<div class="cpp-value">{value_html}</div>'
        "</div>"
    )


def title_html(title: str) -> str:
    lines = [line.strip() for line in str(title or "").split("\n") if line.strip()]
    return "".join(f'<div class="cpp-card__title-line">{escape(line)}</div>' for line in lines)


def render_card(item, rank: int, show_score: bool, is_best: bool) -> str:
    fields = list(item.get("fields") or [])
    
    # Чтобы первичный цвет Streamlit работал корректно в градиентах, задаем резервный класс
    best_class = " cpp-card--best" if is_best else ""
    
    parts = [
        f'<div class="cpp-card{best_class}">',
        '<div class="cpp-card__top">',
        f'<div class="cpp-rank">{rank}</div>',
        '<div class="cpp-card__head">',
        f'<div class="cpp-card__title">{title_html(item.get("title", ""))}</div>',
    ]

    if is_best:
        # Добавил иконку в бейдж для большей красоты
        parts.append('<div class="cpp-badge"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg> Лучшее совпадение</div>')

    parts.extend(["</div>", "</div>", '<div class="cpp-grid">'])

    for field in fields:
        value = field.get("value") or "-"
        # Автоматически делаем поле "stacked" (в колонку), если текста много
        is_stacked = len(str(value)) >= 90 or "\n" in str(value)
        parts.append(field_row(field.get("label") or "Поле", value, stacked=is_stacked))

    if show_score and item.get("score") is not None:
        # Оценка отображается компактно
        parts.append(field_row("Score", f'{item["score"]:.3f}'))

    parts.extend(["</div>", "</div>"])
    return "\n".join(parts)


def render_results(title: str, items, total: int, show_scores: bool = False) -> None:
    parts = [
        CARD_CSS,
        '<div class="cpp-chunk-parser">',
        '<div class="cpp-chunk-parser__header">',
        f'<div class="cpp-chunk-parser__title">{escape(title)}</div>',
        f'<div class="cpp-chunk-parser__meta">Найдено: <strong>{len(items)}</strong> / {total}</div>',
        "</div>",
    ]

    if not items:
        parts.append('<div class="cpp-empty">Совпадения не найдены. Попробуйте изменить запрос.</div>')
    else:
        parts.extend(
            render_card(item, rank=index + 1, show_score=show_scores, is_best=show_scores and index == 0)
            for index, item in enumerate(items)
        )

    parts.append("</div>")
    st.markdown("\n".join(parts), unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_data():
    return load_all_txts()


# Красивый заголовок страницы через Markdown
st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>✨ Помощник разметчика</h1>", unsafe_allow_html=True)

try:
    with st.spinner("⏳ Подготовка умного индекса..."):
        df = get_data()
except Exception as exc:
    st.error(f"❌ Не удалось загрузить или разобрать документ: {exc}")
    st.stop()

case_count = df["case_uid"].nunique()

# Оформляем блок поиска в красивый контейнер
with st.container():
    st.markdown("### Параметры поиска")
    query_col, top_k_col = st.columns([4, 1])
    with query_col:
        query = st.text_input("Введите текст для поиска", placeholder="Например: ошибка подключения к базе...")
    with top_k_col:
        top_k = st.number_input("Топ результатов", min_value=1, max_value=20, value=5, step=1)

if not query.strip():
    st.info("💡 Введите запрос в поле выше, чтобы начать поиск.")
    st.stop()

# Разделитель перед результатами
st.markdown("---")

with st.spinner("🔍 ИИ анализирует запрос..."):
    semantic_results = semantic_search(query, df, top_k=top_k)
    exact_results = keyword_search(query, df, top_k=top_k)

# Вывод результатов
render_results("Умный поиск", semantic_results, total=case_count, show_scores=True)
render_results("Точный поиск", exact_results, total=case_count, show_scores=False)
