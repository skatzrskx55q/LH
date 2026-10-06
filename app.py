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
    white-space: normal;
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
@media (prefers-reduced-motion: reduce) { [data-testid="stAppViewContainer"] { animation: none !important; } .modern-card { transition: none !important; } }
</style>
"""


def escape(value):
    return html.escape(str(value or ""), quote=True)


def value_html(value):
    # Ссылки разрешены и в сплошном/ручном режиме, но только http(s).
    import re
    value = str(value or "—")
    parts, last = [], 0
    for match in re.finditer(r"https?://[^\s<>\"']+", value, re.I):
        url = match.group().rstrip(".,;!)]}")
        end = match.start() + len(url)
        parts.append(escape(value[last:match.start()]))
        if safe_http_url(url):
            parts.append(f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" style="color:#c4b5fd">{escape(url)}</a>')
        else:
            parts.append(escape(url))
        last = end
    parts.append(escape(value[last:]))
    return "".join(parts).replace("\n", "<br>")


def field_row(label, value, stacked=False):
    lbl = escape(label)
    val = str(value or "—")
    if "интент" in str(label).casefold() and "→" in val:
        badges = '<span class="intent-arrow">→</span>'.join(
            f'<span class="intent-badge">{escape(p.strip())}</span>' for p in val.split("→"))
        body = f'<div class="intent-container">{badges}</div>'
    else:
        body = f'<div class="data-value">{value_html(val)}</div>'
    label_html = f'<div class="data-label">{lbl}</div>' if lbl else ""
    return f'<div class="data-row{" stacked" if stacked or not lbl else ""}">{label_html}{body}</div>'


def render_card(item, rank, show_score=True, is_best=False):
    parts = [f'<div class="modern-card{" is-best" if is_best else ""}">',
             f'<div class="card-header"><div class="card-rank">{rank}</div>',
             f'<div class="card-title">{escape(item["title"])}</div></div>',
             f'<div style="color:#a1a1aa;font-size:12px;margin-bottom:12px">Источник: {escape(item["source_file"])} · кейс {int(item["case_index"])}</div>']
    if item.get("fields"):
        parts.append('<div class="data-grid">')
        for field in item["fields"]:
            value = field.get("value", "")
            parts.append(field_row(field.get("label", ""), value, len(value) > 80 or "\n" in value))
        parts.append('</div>')
    if show_score and "score" in item:
        parts.append(f'<div class="score-pill">Рейтинг: {item["score"]:.3f}</div>')
        if "lexical_score" in item:
            sem = item.get("semantic_score")
            detail = f'Семантика: {sem:.3f} · ' if sem is not None else ""
            detail += f'Текст: {item["lexical_score"]:.1f} · {item.get("match_type", "")}'
            parts.append(f'<div style="color:#a1a1aa;font-size:12px;margin-top:8px">{escape(detail)}</div>')
    parts.append('</div>')
    return "".join(parts)


def render_results(title, items, total, show_scores=True, icon="🔍"):
    parts = ['<div class="app-container">',
             f'<div class="stats-panel"><div class="stats-title">{icon} {escape(title)}</div><div class="stats-badge">Показано {len(items)} · в базе {total}</div></div>']
    if not items:
        parts.append('<div class="modern-card">Ничего не найдено. Попробуйте другой запрос или уменьшите порог семантики.</div>')
    for i, item in enumerate(items, 1):
        parts.append(render_card(item, i, show_scores, i == 1))
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=32)
def cached_fetch_url(url):
    return fetch_url_text(url)


MODE_MAP = {"Авто": "auto", "Ручной": "custom", "Сплошной": "none"}
DEFAULT_GITHUB = "https://raw.githubusercontent.com/skatzrskx55q/LH/main/Документ 3.txt"


def source_key(kind, value):
    return kind + ":" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def main():
    st.markdown(DARK_SaaS_CSS, unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:#f4f4f5"><h1>Помощник разметчика</h1><p>Поиск по кейсам и сопоставление интентов</p></div>', unsafe_allow_html=True)
    query_col, count_col = st.columns([4, 1])
    with query_col:
        query = st.text_input("Поисковый запрос", placeholder="Например: изменить дату платежа", key="query")
    with count_col:
        top_k = st.number_input("Результатов", min_value=1, max_value=20, value=5)
    scope_label = st.radio("Область поиска", ["Весь кейс", "Только заголовки"], horizontal=True,
                          help="Весь кейс включает заголовок, статью, интенты и остальные поля.")
    scope = "case" if scope_label == "Весь кейс" else "title"
    configs = []
    with st.expander("⚙️ Источники данных и настройки парсинга", expanded=not st.session_state.get("sources_ready", False)):
        col_upload, col_urls = st.columns(2)
        with col_upload:
            uploads = st.file_uploader("Локальные файлы (.txt)", type="txt", accept_multiple_files=True)
        with col_urls:
            urls_text = st.text_area("Прямые ссылки raw.githubusercontent.com", value=DEFAULT_GITHUB, height=100)
        if st.button("Обновить документы по ссылкам"):
            cached_fetch_url.clear()
        docs = {}
        for url in dict.fromkeys(u.strip() for u in urls_text.splitlines() if u.strip()):
            name = "GitHub документ"
            sid = source_key("github", url)
            try:
                name = unquote(urlsplit(url).path.rsplit("/", 1)[-1]) or name
                text = cached_fetch_url(url)
                if not text.strip():
                    raise ValueError("Документ пуст.")
                docs[sid] = {"name": name, "text": text, "source_id": sid}
            except Exception as exc:
                st.warning(f"Не удалось загрузить {name}: {exc}")
        for index, file in enumerate(uploads or []):
            try:
                if file.size > MAX_DOCUMENT_BYTES:
                    raise ValueError("Размер документа превышает 5 МБ.")
                sid = source_key("local", f"{file.name}:{index}")
                docs[sid] = {"name": file.name, "text": decode_text_bytes(file.getvalue()), "source_id": sid}
            except ValueError as exc:
                st.warning(f"{file.name}: {exc}")
        duplicate_names = pd.Series([d["name"] for d in docs.values()]).value_counts().to_dict() if docs else {}
        def doc_label(sid):
            name = docs[sid]["name"]
            return f"{name} · {sid}" if duplicate_names[name] > 1 else name
        active = st.multiselect("Документы для работы", list(docs), default=list(docs), format_func=doc_label)
        for sid in active:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.caption(doc_label(sid))
            with c2:
                choice = st.selectbox("Режим", list(MODE_MAP), key=f"mode_{sid}")
            prefixes = ""
            if choice == "Ручной":
                prefixes = st.text_input("Префиксы через запятую", "Интенты, Дата, Статья, Ссылка", key=f"prefix_{sid}")
            configs.append({**docs[sid], "mode": MODE_MAP[choice],
                            "prefixes": [p.strip() for p in prefixes.split(",") if p.strip()]})
        st.session_state["sources_ready"] = bool(configs)
    with st.expander("Параметры поиска", expanded=False):
        enable_semantic = st.checkbox("Использовать семантическую модель", value=True)
        threshold = st.slider("Порог семантического сходства", 0.0, 1.0, 0.5, 0.01,
                              help="Начальное значение, а не измеренный оптимум. Подберите его на размеченных запросах.")
        weight = st.slider("Вес семантики в гибридном рейтинге", 0.0, 1.0, 0.65, 0.05)
        substring = st.checkbox("Учитывать совпадение части слова (слабый сигнал)", value=False)
        diagnostics = st.checkbox("Показать отдельные выдачи и ID кейсов", value=False)
    if not configs:
        st.info("Загрузите документы и выберите источники для поиска.")
        return
    try:
        df = build_database(configs, scope)
    except Exception as exc:
        st.error(f"Ошибка разбора документов: {exc}")
        return
    if df.empty:
        st.warning("Нет кейсов. Используйте заголовки в формате ==текст кейса==.")
        return
    st.caption(f'В базе: {df["case_uid"].nunique()} кейсов · {len(df)} вариантов')
    if not query.strip():
        return
    semantic_ok = enable_semantic
    if semantic_ok:
        try:
            with st.spinner("Подготовка семантического поиска…"):
                attach_embeddings(df)
        except Exception as exc:
            semantic_ok = False
            st.warning(f"Семантическая модель недоступна. Работает текстовый поиск. Причина: {exc}")
    try:
        with st.spinner("Поиск…"):
            results = search_bundle(query, df, int(top_k), threshold, weight, substring, semantic_ok)
    except Exception as exc:
        # Ошибка кодирования запроса тоже не должна отключать текстовый поиск.
        if not semantic_ok:
            st.error(f"Ошибка поиска: {exc}")
            return
        st.warning(f"Семантический поиск недоступен: {exc}. Показаны текстовые результаты.")
        semantic_ok = False
        results = search_bundle(query, df, int(top_k), threshold, weight, substring, False)
    render_results("Гибридный поиск" if semantic_ok else "Текстовый поиск", results["hybrid"], int(df["case_uid"].nunique()))
    st.caption("Рейтинг служит для сортировки и не является вероятностью правильного ответа.")
    if diagnostics:
        with st.expander("Диагностика", expanded=True):
            render_results("Семантика", results["semantic"], int(df["case_uid"].nunique()), icon="✨")
            render_results("Точные фразы, слова и словоформы", results["lexical"], int(df["case_uid"].nunique()), icon="🎯")
            columns = ["case_uid", "source_file", "case_index", "title"]
            catalog = df[columns].drop_duplicates("case_uid")
            st.dataframe(catalog, use_container_width=True, hide_index=True)
            st.download_button("Скачать ID кейсов для оценки", catalog.to_csv(index=False).encode("utf-8-sig"),
                               "case_catalog.csv", "text/csv")


if __name__ == "__main__":
    main()
