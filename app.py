import html

import streamlit as st

from utils import decode_text_bytes, keyword_search, load_text_documents, semantic_search


st.set_page_config(page_title="Помощник разметчика", layout="centered")


CARD_CSS = """
<style>
.cpp-chunk-parser,.cpp-chunk-parser *{box-sizing:border-box}.cpp-chunk-parser{font-family:inherit;color:inherit}.cpp-chunk-parser__header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px;margin:0 0 12px;border:1px solid rgba(148,163,184,.24);border-radius:8px;background:rgba(148,163,184,.055);color:inherit}.cpp-chunk-parser__title{min-width:0;font-size:18px;line-height:1.25;font-weight:800;letter-spacing:0;overflow-wrap:anywhere}.cpp-chunk-parser__meta{flex:0 0 auto;padding:6px 10px;border:1px solid rgba(148,163,184,.24);border-radius:999px;background:rgba(148,163,184,.07);font-size:12px;line-height:1;opacity:.86;white-space:nowrap}.cpp-chunk-parser__meta strong{font-weight:800;opacity:1}.cpp-empty{padding:14px 16px;border:1px solid rgba(148,163,184,.24);border-radius:8px;background:rgba(148,163,184,.055);font-size:14px}.cpp-card{padding:14px;margin:0 0 12px;border:1px solid rgba(148,163,184,.24);border-radius:8px;background:rgba(248,250,252,.75);box-shadow:0 1px 2px rgba(0,0,0,.05),0 8px 22px rgba(0,0,0,.055);color:inherit}.cpp-card--best{border-color:rgba(37,99,235,.46);background:rgba(37,99,235,.045)}.cpp-card__top{display:flex;align-items:flex-start;gap:10px;margin-bottom:12px}.cpp-rank{flex:0 0 auto;width:30px;height:30px;display:inline-flex;align-items:center;justify-content:center;border:1px solid rgba(148,163,184,.24);border-radius:8px;background:rgba(148,163,184,.08);font-size:12px;font-weight:800;line-height:1}.cpp-card--best .cpp-rank{border-color:rgba(37,99,235,.38);background:rgba(37,99,235,.10)}.cpp-card__head{flex:1;min-width:0}.cpp-card__title{display:grid;gap:3px;margin-bottom:6px}.cpp-card__title-line{font-size:15px;line-height:1.45;font-weight:720;letter-spacing:0;overflow-wrap:anywhere}.cpp-badge{display:inline-flex;align-items:center;width:fit-content;min-height:26px;padding:5px 8px;border:1px solid rgba(37,99,235,.34);border-radius:999px;background:rgba(37,99,235,.09);font-size:12px;font-weight:750;line-height:1}.cpp-grid{display:grid;gap:8px}.cpp-row{display:grid;grid-template-columns:minmax(96px,136px) minmax(0,1fr);gap:8px;align-items:start}.cpp-row--single,.cpp-row--stacked{grid-template-columns:minmax(0,1fr)}.cpp-label{padding:8px 10px;border:1px solid rgba(148,163,184,.20);border-radius:8px;background:rgba(148,163,184,.07);font-size:11px;line-height:1.35;font-weight:760;letter-spacing:0;text-transform:uppercase;opacity:.68;overflow-wrap:anywhere}.cpp-label--stacked{margin-bottom:-2px}.cpp-value{padding:8px 10px;border:1px solid rgba(148,163,184,.18);border-radius:8px;background:rgba(255,255,255,.58);font-size:13px;line-height:1.55;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}.cpp-value__line{white-space:pre-wrap}.cpp-value__line+.cpp-value__line{margin-top:8px;padding-top:8px;border-top:1px solid rgba(148,163,184,.18)}@media(max-width:640px){.cpp-chunk-parser__header{align-items:flex-start;flex-direction:column;padding:13px}.cpp-card{padding:13px}.cpp-row{grid-template-columns:minmax(0,1fr)}.cpp-label{margin-bottom:-2px}}
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
def build_index(upload_payload):
    documents = [(name, decode_text_bytes(content)) for name, content in upload_payload]
    return load_text_documents(documents)


st.title("Помощник разметчика")

uploaded_files = st.file_uploader("TXT-документы", type=["txt"], accept_multiple_files=True)

if not uploaded_files:
    st.info("Загрузите один или несколько TXT-документов.")
    st.stop()

payload = tuple((uploaded_file.name, uploaded_file.getvalue()) for uploaded_file in uploaded_files)

try:
    with st.spinner("Готовлю индекс..."):
        df = build_index(payload)
except Exception as exc:
    st.error(f"Не удалось разобрать документы: {exc}")
    st.stop()

case_count = df["case_uid"].nunique()
st.caption(f"Кейсов в индексе: {case_count}")

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
