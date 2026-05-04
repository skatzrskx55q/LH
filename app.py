import html

import streamlit as st

from utils import keyword_search, load_all_txts, semantic_search


st.set_page_config(page_title="Помощник разметчика", layout="centered")


CARD_CSS = """
<style>
.cpp-chunk-parser,.cpp-chunk-parser *{box-sizing:border-box}.cpp-chunk-parser{--cpp-fg:inherit;--cpp-muted:inherit;--cpp-border:rgba(148,163,184,.24);--cpp-soft:rgba(148,163,184,.055);--cpp-soft-2:rgba(148,163,184,.07);--cpp-card:rgba(148,163,184,.045);--cpp-accent:rgba(99,102,241,.46);--cpp-accent-soft:rgba(99,102,241,.045);--cpp-accent-soft-2:rgba(99,102,241,.10);--cpp-shadow:0 1px 2px rgba(0,0,0,.05),0 8px 22px rgba(0,0,0,.055);font-family:inherit;color:var(--cpp-fg)}.cpp-theme-light{--cpp-fg:#172033;--cpp-muted:#64748b;--cpp-border:rgba(100,116,139,.24);--cpp-soft:rgba(241,245,249,.82);--cpp-soft-2:rgba(226,232,240,.72);--cpp-card:rgba(255,255,255,.92);--cpp-accent:rgba(79,70,229,.42);--cpp-accent-soft:rgba(79,70,229,.055);--cpp-accent-soft-2:rgba(79,70,229,.11);--cpp-shadow:0 1px 2px rgba(15,23,42,.05),0 10px 26px rgba(15,23,42,.08)}.cpp-theme-dark{--cpp-fg:#e5e7eb;--cpp-muted:#a1a1aa;--cpp-border:rgba(148,163,184,.24);--cpp-soft:rgba(148,163,184,.055);--cpp-soft-2:rgba(148,163,184,.07);--cpp-card:rgba(148,163,184,.045);--cpp-accent:rgba(129,140,248,.52);--cpp-accent-soft:rgba(129,140,248,.06);--cpp-accent-soft-2:rgba(129,140,248,.12);--cpp-shadow:0 1px 2px rgba(0,0,0,.18),0 8px 22px rgba(0,0,0,.18)}@media(prefers-color-scheme:dark){.cpp-theme-auto{--cpp-fg:#e5e7eb;--cpp-muted:#a1a1aa;--cpp-border:rgba(148,163,184,.24);--cpp-soft:rgba(148,163,184,.055);--cpp-soft-2:rgba(148,163,184,.07);--cpp-card:rgba(148,163,184,.045);--cpp-accent:rgba(129,140,248,.52);--cpp-accent-soft:rgba(129,140,248,.06);--cpp-accent-soft-2:rgba(129,140,248,.12);--cpp-shadow:0 1px 2px rgba(0,0,0,.18),0 8px 22px rgba(0,0,0,.18)}}.cpp-chunk-parser__header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px;margin:0 0 12px;border:1px solid var(--cpp-border);border-radius:18px;background:var(--cpp-soft);color:var(--cpp-fg)}.cpp-chunk-parser__title{min-width:0;font-size:18px;line-height:1.25;font-weight:800;letter-spacing:0;overflow-wrap:anywhere}.cpp-chunk-parser__meta{flex:0 0 auto;padding:6px 10px;border:1px solid var(--cpp-border);border-radius:999px;background:var(--cpp-soft-2);color:var(--cpp-muted);font-size:12px;line-height:1;white-space:nowrap}.cpp-chunk-parser__meta strong{font-weight:800;color:var(--cpp-fg)}.cpp-empty{padding:14px 16px;border:1px solid var(--cpp-border);border-radius:16px;background:var(--cpp-soft);font-size:14px;color:var(--cpp-muted)}.cpp-card{padding:14px;margin:0 0 12px;border:1px solid var(--cpp-border);border-radius:18px;background:var(--cpp-card);box-shadow:var(--cpp-shadow);color:var(--cpp-fg)}.cpp-card--best{border-color:var(--cpp-accent);background:var(--cpp-accent-soft)}.cpp-card__top{display:flex;align-items:flex-start;gap:10px;margin-bottom:12px}.cpp-rank{flex:0 0 auto;width:30px;height:30px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--cpp-border);border-radius:10px;background:var(--cpp-soft-2);color:var(--cpp-fg);font-size:12px;font-weight:800;line-height:1}.cpp-card--best .cpp-rank{border-color:var(--cpp-accent);background:var(--cpp-accent-soft-2)}.cpp-card__head{flex:1;min-width:0}.cpp-card__title{display:grid;gap:3px;margin-bottom:6px}.cpp-card__title-line{font-size:14px;line-height:1.45;font-weight:720;letter-spacing:0;overflow-wrap:anywhere;color:var(--cpp-fg)}.cpp-badge{display:inline-flex;align-items:center;width:fit-content;min-height:26px;padding:5px 8px;border:1px solid var(--cpp-accent);border-radius:999px;background:var(--cpp-accent-soft-2);color:var(--cpp-fg);font-size:12px;font-weight:750;line-height:1}.cpp-grid{display:grid;gap:8px}.cpp-row{display:grid;grid-template-columns:minmax(96px,136px) minmax(0,1fr);gap:8px;align-items:start}.cpp-row--single,.cpp-row--stacked{grid-template-columns:minmax(0,1fr)}.cpp-label{padding:8px 10px;border:1px solid var(--cpp-border);border-radius:12px;background:var(--cpp-soft-2);color:var(--cpp-muted);font-size:11px;line-height:1.35;font-weight:760;letter-spacing:0;text-transform:uppercase;overflow-wrap:anywhere}.cpp-label--stacked{margin-bottom:-2px}.cpp-value{padding:8px 10px;border:1px solid var(--cpp-border);border-radius:12px;background:var(--cpp-card);color:var(--cpp-fg);font-size:13px;line-height:1.55;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}.cpp-value__line{white-space:pre-wrap}.cpp-value__line+.cpp-value__line{margin-top:8px;padding-top:8px;border-top:1px solid var(--cpp-border)}@media(max-width:640px){.cpp-chunk-parser__header{align-items:flex-start;flex-direction:column;border-radius:16px;padding:13px}.cpp-chunk-parser__meta{white-space:normal;line-height:1.25}.cpp-card{border-radius:16px;padding:13px}.cpp-row{grid-template-columns:minmax(0,1fr)}.cpp-label{margin-bottom:-2px}}
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

    parts.extend(["</div>", "</div>"])
    return "\n".join(parts)


def style_class(style_name: str) -> str:
    return {
        "Светлая": "cpp-theme-light",
        "Темная": "cpp-theme-dark",
    }.get(style_name, "cpp-theme-auto")


def render_results(title: str, items, total: int, card_style: str, show_scores: bool = False) -> None:
    parts = [
        CARD_CSS,
        f'<div class="cpp-chunk-parser {style_class(card_style)}">',
        '<div class="cpp-chunk-parser__header">',
        f'<div class="cpp-chunk-parser__title">{escape(title)}</div>',
        f'<div class="cpp-chunk-parser__meta">Найдено совпадений: <strong>{len(items)}</strong> из <strong>{total}</strong></div>',
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

query_col, top_k_col, style_col = st.columns([4, 1, 1.5])
with query_col:
    query = st.text_input("Запрос")
with top_k_col:
    top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, step=1)
with style_col:
    if hasattr(st, "segmented_control"):
        card_style = st.segmented_control("Стиль", ["Авто", "Светлая", "Темная"], default="Авто")
    else:
        card_style = st.selectbox("Стиль", ["Авто", "Светлая", "Темная"], index=0)
    card_style = card_style or "Авто"

if not query.strip():
    st.stop()

with st.spinner("Ищу совпадения..."):
    semantic_results = semantic_search(query, df, top_k=top_k)
    exact_results = keyword_search(query, df, top_k=top_k)

render_results("Умный поиск", semantic_results, total=case_count, card_style=card_style, show_scores=True)
render_results("Точный поиск", exact_results, total=case_count, card_style=card_style, show_scores=False)
