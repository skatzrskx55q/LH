import html

import streamlit as st

from utils import GITHUB_TXT_URLS, keyword_search, load_all_txts, semantic_search


st.set_page_config(page_title="Помощник разметчика", layout="centered")


CARD_CSS = """
<style>
.cpp-chunk-parser,
.cpp-chunk-parser * {
    box-sizing: border-box;
}

.cpp-chunk-parser {
    --cpp-text: #0f172a;
    --cpp-muted: #475569;
    --cpp-border: rgba(71, 85, 105, .22);
    --cpp-border-strong: rgba(37, 99, 235, .42);
    --cpp-panel: rgba(248, 250, 252, .82);
    --cpp-card: rgba(255, 255, 255, .88);
    --cpp-field: rgba(241, 245, 249, .82);
    --cpp-value: rgba(255, 255, 255, .72);
    --cpp-accent: #2563eb;
    --cpp-accent-soft: rgba(37, 99, 235, .09);
    --cpp-shadow: 0 1px 2px rgba(15, 23, 42, .06), 0 12px 28px rgba(15, 23, 42, .08);
    color: var(--cpp-text);
    font-family: inherit;
    width: 100%;
}

@media (prefers-color-scheme: dark) {
    .cpp-chunk-parser {
        --cpp-text: #e5e7eb;
        --cpp-muted: #a1a1aa;
        --cpp-border: rgba(148, 163, 184, .24);
        --cpp-border-strong: rgba(96, 165, 250, .48);
        --cpp-panel: rgba(30, 41, 59, .54);
        --cpp-card: rgba(15, 23, 42, .72);
        --cpp-field: rgba(30, 41, 59, .72);
        --cpp-value: rgba(2, 6, 23, .24);
        --cpp-accent: #60a5fa;
        --cpp-accent-soft: rgba(96, 165, 250, .12);
        --cpp-shadow: 0 1px 2px rgba(0, 0, 0, .22), 0 14px 30px rgba(0, 0, 0, .18);
    }
}

html[data-theme="dark"] .cpp-chunk-parser,
body[data-theme="dark"] .cpp-chunk-parser,
[data-theme="dark"] .cpp-chunk-parser {
    --cpp-text: #e5e7eb;
    --cpp-muted: #a1a1aa;
    --cpp-border: rgba(148, 163, 184, .24);
    --cpp-border-strong: rgba(96, 165, 250, .48);
    --cpp-panel: rgba(30, 41, 59, .54);
    --cpp-card: rgba(15, 23, 42, .72);
    --cpp-field: rgba(30, 41, 59, .72);
    --cpp-value: rgba(2, 6, 23, .24);
    --cpp-accent: #60a5fa;
    --cpp-accent-soft: rgba(96, 165, 250, .12);
    --cpp-shadow: 0 1px 2px rgba(0, 0, 0, .22), 0 14px 30px rgba(0, 0, 0, .18);
}

.cpp-chunk-parser__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 16px;
    margin: 18px 0 12px;
    border: 1px solid var(--cpp-border);
    border-radius: 8px;
    background: var(--cpp-panel);
    color: var(--cpp-text);
}

.cpp-chunk-parser__title {
    min-width: 0;
    font-size: 18px;
    line-height: 1.25;
    font-weight: 800;
    letter-spacing: 0;
    overflow-wrap: anywhere;
}

.cpp-chunk-parser__meta {
    flex: 0 0 auto;
    max-width: 100%;
    padding: 6px 10px;
    border: 1px solid var(--cpp-border);
    border-radius: 999px;
    background: var(--cpp-field);
    color: var(--cpp-muted);
    font-size: 12px;
    line-height: 1.2;
    white-space: nowrap;
}

.cpp-chunk-parser__meta strong {
    color: var(--cpp-text);
    font-weight: 800;
}

.cpp-empty {
    padding: 14px 16px;
    border: 1px solid var(--cpp-border);
    border-radius: 8px;
    background: var(--cpp-panel);
    color: var(--cpp-muted);
    font-size: 14px;
}

.cpp-card {
    padding: 14px;
    margin: 0 0 12px;
    border: 1px solid var(--cpp-border);
    border-radius: 8px;
    background: var(--cpp-card);
    box-shadow: var(--cpp-shadow);
    color: var(--cpp-text);
}

.cpp-card--best {
    border-color: var(--cpp-border-strong);
    background: linear-gradient(0deg, var(--cpp-accent-soft), var(--cpp-accent-soft)), var(--cpp-card);
}

.cpp-card__top {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 12px;
}

.cpp-rank {
    flex: 0 0 auto;
    width: 30px;
    height: 30px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--cpp-border);
    border-radius: 8px;
    background: var(--cpp-field);
    color: var(--cpp-text);
    font-size: 12px;
    font-weight: 800;
    line-height: 1;
}

.cpp-card--best .cpp-rank {
    border-color: var(--cpp-border-strong);
    background: var(--cpp-accent-soft);
    color: var(--cpp-accent);
}

.cpp-card__head {
    flex: 1;
    min-width: 0;
}

.cpp-card__title {
    display: grid;
    gap: 3px;
    margin-bottom: 6px;
}

.cpp-card__title-line {
    color: var(--cpp-text);
    font-size: 15px;
    line-height: 1.45;
    font-weight: 720;
    letter-spacing: 0;
    overflow-wrap: anywhere;
}

.cpp-badge {
    display: inline-flex;
    align-items: center;
    width: fit-content;
    min-height: 26px;
    padding: 5px 8px;
    border: 1px solid var(--cpp-border-strong);
    border-radius: 999px;
    background: var(--cpp-accent-soft);
    color: var(--cpp-accent);
    font-size: 12px;
    font-weight: 750;
    line-height: 1;
}

.cpp-grid {
    display: grid;
    gap: 8px;
}

.cpp-row {
    display: grid;
    grid-template-columns: minmax(96px, 136px) minmax(0, 1fr);
    gap: 8px;
    align-items: stretch;
}

.cpp-row--single,
.cpp-row--stacked {
    grid-template-columns: minmax(0, 1fr);
}

.cpp-label {
    padding: 8px 10px;
    border: 1px solid var(--cpp-border);
    border-radius: 8px;
    background: var(--cpp-field);
    color: var(--cpp-muted);
    font-size: 11px;
    line-height: 1.35;
    font-weight: 760;
    letter-spacing: 0;
    text-transform: uppercase;
    overflow-wrap: anywhere;
}

.cpp-label--stacked {
    margin-bottom: -2px;
}

.cpp-value {
    min-width: 0;
    padding: 8px 10px;
    border: 1px solid var(--cpp-border);
    border-radius: 8px;
    background: var(--cpp-value);
    color: var(--cpp-text);
    font-size: 13px;
    line-height: 1.55;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
}

.cpp-value__line {
    white-space: pre-wrap;
}

.cpp-value__line + .cpp-value__line {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--cpp-border);
}

@media (max-width: 640px) {
    .cpp-chunk-parser__header {
        align-items: flex-start;
        flex-direction: column;
        padding: 13px;
    }

    .cpp-chunk-parser__meta {
        white-space: normal;
    }

    .cpp-card {
        padding: 13px;
    }

    .cpp-card__top {
        gap: 8px;
    }

    .cpp-row {
        grid-template-columns: minmax(0, 1fr);
    }

    .cpp-label {
        margin-bottom: -2px;
    }
}
</style>
""".strip()


def escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def render_value(value) -> str:
    lines = [line.strip() for line in str(value or "").split("\n") if line.strip()]
    if not lines:
        return "—"
    if len(lines) == 1:
        return escape(lines[0])
    return "".join(f'<div class="cpp-value__line">{escape(line)}</div>' for line in lines)


def field_row(label, value, stacked: bool = False) -> str:
    label_html = escape(label)
    value_html = render_value(value)

    if stacked:
        return (
            '<div class="cpp-row cpp-row--stacked">'
            f'<div class="cpp-label cpp-label--stacked">{label_html}</div>'
            f'<div class="cpp-value">{value_html}</div>'
            "</div>"
        )

    return (
        '<div class="cpp-row">'
        f'<div class="cpp-label">{label_html}</div>'
        f'<div class="cpp-value">{value_html}</div>'
        "</div>"
    )


def title_html(title: str) -> str:
    lines = [line.strip() for line in str(title or "").split("\n") if line.strip()]
    return "".join(f'<div class="cpp-card__title-line">{escape(line)}</div>' for line in lines)


def render_card(item, rank: int, show_score: bool, is_best: bool) -> str:
    fields = list(item.get("fields") or [])
    parts = [
        f'<div class="cpp-card{" cpp-card--best" if is_best else ""}">',
        '<div class="cpp-card__top">',
        f'<div class="cpp-rank">{rank}</div>',
        '<div class="cpp-card__head">',
        f'<div class="cpp-card__title">{title_html(item.get("title", ""))}</div>',
    ]

    if is_best:
        parts.append('<div class="cpp-badge">Лучшее совпадение</div>')

    parts.extend(["</div>", "</div>", '<div class="cpp-grid">'])

    for field in fields:
        value = field.get("value") or "—"
        parts.append(field_row(field.get("label") or "Поле", value, stacked=len(str(value)) >= 90 or "\n" in str(value)))

    if show_score and item.get("score") is not None:
        parts.append(field_row("Score", f'{item["score"]:.3f}'))

    parts.append(field_row("Документ", item.get("source_file", "")))
    parts.extend(["</div>", "</div>"])
    return "\n".join(parts)


def render_results(title: str, items, total: int, show_scores: bool = False) -> None:
    parts = [
        CARD_CSS,
        '<div class="cpp-chunk-parser">',
        '<div class="cpp-chunk-parser__header">',
        f'<div class="cpp-chunk-parser__title">{escape(title)}</div>',
        f'<div class="cpp-chunk-parser__meta">Найдено: <strong>{len(items)}</strong> из <strong>{total}</strong></div>',
        "</div>",
    ]

    if not items:
        parts.append('<div class="cpp-empty">Совпадения не найдены.</div>')
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


st.title("Помощник разметчика")

try:
    with st.spinner("Загружаю документы с GitHub и готовлю индекс..."):
        df = get_data()
except Exception as exc:
    st.error(f"Не удалось загрузить или разобрать документ: {exc}")
    st.stop()

case_count = df["case_uid"].nunique()
source_label = ", ".join(GITHUB_TXT_URLS) if GITHUB_TXT_URLS else "GitHub"
st.caption(f"Кейсов в индексе: {case_count}. Источник: {source_label}")

query_col, top_k_col = st.columns([4, 1])
with query_col:
    query = st.text_input("Запрос")
with top_k_col:
    top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, step=1)

if not query.strip():
    st.stop()

with st.spinner("Ищу совпадения..."):
    semantic_results = semantic_search(query, df, top_k=top_k)
    exact_results = keyword_search(query, df, top_k=top_k)

render_results("Умный поиск", semantic_results, total=case_count, show_scores=True)
render_results("Точный поиск", exact_results, total=case_count, show_scores=False)
