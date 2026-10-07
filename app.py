import hashlib
import html

import pandas as pd
import streamlit as st

from utils import (
    attach_embeddings, build_database, search_bundle, safe_http_url,
    read_xlsx, xlsx_table, suggest_xlsx_columns, MAX_XLSX_BYTES,
    automatic_configs, fetch_github_xlsx, DEFAULT_XLSX_URL, tokenize,
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
    # В ячейках разрешены только ссылки http(s).
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


def compact_value(value, limit=300):
    value = str(value or "")
    if len(value) <= limit and value.count("\n") < 5:
        return value_html(value)
    preview = value[:limit].rstrip()
    return (f'<details class="cell-details"><summary>{escape(preview)}… '
            '<span style="color:#c4b5fd">Развернуть полностью</span></summary>'
            f'<div style="margin-top:12px">{value_html(value)}</div></details>')


def field_row(label, value, stacked=False):
    lbl = escape(label)
    val = str(value or "—")
    if len(val) <= 300 and val.count("\n") < 5 and "интент" in str(label).casefold() and "→" in val:
        badges = '<span class="intent-arrow">→</span>'.join(
            f'<span class="intent-badge">{escape(p.strip())}</span>' for p in val.split("→"))
        body = f'<div class="intent-container">{badges}</div>'
    else:
        body = f'<div class="data-value">{compact_value(val)}</div>'
    label_html = f'<div class="data-label">{lbl}</div>' if lbl else ""
    return f'<div class="data-row{" stacked" if stacked or not lbl else ""}">{label_html}{body}</div>'


def render_card(item, rank, show_score=True, is_best=False):
    parts = [f'<div class="modern-card{" is-best" if is_best else ""}">',
             f'<div class="card-header"><div class="card-rank">{rank}</div>',
             f'<div class="card-title">{compact_value(item["title"], 180)}</div></div>',
             f'<div style="color:#a1a1aa;font-size:12px;margin-bottom:12px">Источник: {escape(item["source_file"])} · лист «{escape(item["sheet_name"])}» · строка {int(item["row_number"])}</div>']
    if item.get("fields"):
        parts.append('<div class="data-grid">')
        for field in item["fields"]:
            value = field.get("value", "")
            parts.append(field_row(field.get("label", ""), value, len(value) > 80 or "\n" in value))
        parts.append('</div>')
    if show_score and "score" in item:
        parts.append(f'<div class="score-pill">Рейтинг: {item["score"]:.3f}</div>')
        if "lexical_score" in item or "semantic_score" in item:
            sem = item.get("semantic_score")
            detail = f'Семантика: {sem:.3f} · ' if sem is not None else ""
            lexical = item.get("lexical_score")
            if lexical is not None:
                detail += f'BM25: {lexical:.3f} · '
            detail += item.get("match_type", "")
            parts.append(f'<div style="color:#a1a1aa;font-size:12px;margin-top:8px">{escape(detail)}</div>')
    parts.append('</div>')
    return "".join(parts)


def render_results(title, items, total, show_scores=True, icon="🔍"):
    parts = ['<div class="app-container">',
             f'<div class="stats-panel"><div class="stats-title">{icon} {escape(title)}</div><div class="stats-badge">Показано {len(items)} · в базе {total}</div></div>']
    if not items:
        parts.append('<div class="modern-card">Ничего не найдено. Попробуйте другой запрос или тип поиска.</div>')
    for i, item in enumerate(items, 1):
        parts.append(render_card(item, i, show_scores, i == 1))
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def source_key(kind, value):
    return kind + ":" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def configure_xlsx(doc, sid):
    """Настройки каждого листа независимы и сохраняются в текущей сессии."""
    sheets = doc["sheets"]
    widget_source = sid + ":" + doc.get("content_stamp", "")
    selected = st.multiselect("Листы для поиска", list(sheets), default=list(sheets)[:1], key=f"sheets_{widget_source}")
    configs = []
    for name in selected:
        sheet = sheets[name]
        key = source_key("sheet", widget_source + ":" + name)
        with st.container(border=True):
            st.markdown(f"**Лист: {escape(name)}**")
            if not sheet["rows"]:
                st.info("Лист пуст.")
                continue
            st.caption("Предпросмотр первых 20 строк. Число слева — номер строки в Excel.")
            preview = pd.DataFrame([[str(v) if v is not None else "" for v in row]
                                    for row in sheet["rows"][:20]],
                                   index=range(1, min(20, len(sheet["rows"])) + 1))
            preview.columns = [f"Колонка {i + 1}" for i in range(len(preview.columns))]
            st.dataframe(preview, use_container_width=True)
            header = int(st.number_input("Строка с названиями колонок", min_value=1,
                          max_value=len(sheet["rows"]), value=sheet["header_row"], step=1, key=f"header_{key}"))
            table = xlsx_table(sheet, header)
            columns = table["columns"]
            if not columns:
                st.info("Ниже выбранной строки нет данных.")
                continue
            key += f"_h{header}"
            labels = {c["id"]: c["label"] for c in columns}
            ids = list(labels)
            suggested = suggest_xlsx_columns(table)
            if any(not c["original"] for c in columns) or len({c["original"] for c in columns}) < len(columns):
                st.caption("Пустые заголовки получили название «Колонка N»; повторяющиеся — числовой суффикс.")
            if sheet["missing_formulas"]:
                st.warning(f'У {sheet["missing_formulas"]} ячеек с формулами нет сохранённого результата. Они считаются пустыми. Пересчитайте книгу в Excel/LibreOffice и сохраните её.')
            if sheet["error_cells"]:
                st.warning(f'Ячейки с ошибками Excel считаются пустыми: {sheet["error_cells"]}.')
            title_options = [None] + ids
            title = st.selectbox("Колонка заголовка карточки", title_options,
                                 index=title_options.index(suggested["title_column"]),
                                 format_func=lambda c: "Номер строки" if c is None else labels[c],
                                 key=f"title_{key}")
            mode = st.radio("Искать в таблице", ["По основной фразе", "По выбранным колонкам", "По всей строке"],
                            horizontal=True, key=f"search_mode_{key}")
            if mode == "По основной фразе":
                search_columns = [title] if title else []
            elif mode == "По всей строке":
                search_columns = ids
            else:
                search_columns = st.multiselect("Колонки для поиска", ids,
                                default=suggested["search_columns"], format_func=labels.get, key=f"search_cols_{key}")
            display_columns = st.multiselect("Колонки для отображения", ids, default=ids,
                                            format_func=labels.get, key=f"display_{key}",
                                            help="Заголовок карточки показывается отдельно. Остальные пустые поля скрываются.")
            st.caption("Поисковые колонки определяют совпадения. Колонки для отображения определяют только содержимое карточки.")
            display_table = table
            if st.checkbox("Изменить подписи полей", key=f"rename_{key}"):
                renamed = []
                for column in columns:
                    label = st.text_input(f'Подпись: {column["label"]}', value=column["label"],
                                          key=f'rename_{key}_{column["id"]}').strip()
                    renamed.append({**column, "display_label": label or column["label"]})
                display_table = {**table, "columns": renamed}
            date_column, date_from, date_to = None, None, None
            if table["date_columns"] and st.checkbox("Фильтровать по дате", key=f"date_filter_{key}"):
                date_column = st.selectbox("Колонка даты", table["date_columns"], format_func=labels.get, key=f"date_col_{key}")
                dates = [r["dates"][date_column] for r in table["records"] if date_column in r["dates"]]
                c1, c2 = st.columns(2)
                with c1:
                    date_from = st.date_input("Дата с", value=min(dates), key=f"from_{key}_{date_column}")
                with c2:
                    date_to = st.date_input("Дата по", value=max(dates), key=f"to_{key}_{date_column}")
                st.caption("Границы включены. Строки без распознанной даты исключаются при включённом фильтре.")
            if not search_columns:
                st.warning("Выберите колонку основной фразы или хотя бы одну колонку для поиска.")
                continue
            if date_from and date_to and date_from > date_to:
                st.warning("Дата начала должна быть не позже даты окончания.")
                continue
            st.caption(f'Строк данных: {len(table["records"])}. Строки с пустыми поисковыми ячейками не индексируются.')
            configs.append({"kind": "xlsx", "name": doc["name"], "source_id": sid,
                            "sheet_name": name, "table": display_table, "title_column": title,
                            "search_columns": search_columns, "display_columns": display_columns,
                            "date_column": date_column, "date_from": date_from, "date_to": date_to})
    return configs


def github_book():
    content = fetch_github_xlsx(DEFAULT_XLSX_URL)
    return {"name": "example_cases.xlsx", "sheets": read_xlsx(content),
            "content_stamp": hashlib.sha256(content).hexdigest()[:16]}


def main():
    st.markdown(DARK_SaaS_CSS, unsafe_allow_html=True)
    st.markdown('<style>.cell-details summary{cursor:pointer;white-space:pre-wrap;overflow-wrap:anywhere}.cell-details[open] summary{color:#a1a1aa}.cell-details>div{white-space:normal;overflow-wrap:anywhere}</style>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:#f4f4f5"><h1>Помощник разметчика</h1><p>Поиск по Excel-таблицам</p></div>', unsafe_allow_html=True)
    mode = st.radio("Режим работы", ["Автоматический", "Ручной"], horizontal=True, key="work_mode")
    query_col, type_col, count_col = st.columns([4, 2, 1])
    with query_col:
        query = st.text_input("Поисковый запрос", placeholder="Например: изменить дату платежа", key="query")
    with type_col:
        label = st.selectbox("Тип поиска", ["Гибридный", "Семантический", "По совпадению"], key="search_type")
    with count_col:
        top_k = int(st.number_input("Результатов", min_value=1, max_value=20, value=5))
    search_type = {"Гибридный": "hybrid", "Семантический": "semantic", "По совпадению": "lexical"}[label]
    if search_type == "lexical":
        st.caption("Фрагменты от трёх символов или словоформы. Достаточно одного совпадения; больше совпадений — выше результат. Выдача ограничена полем «Результатов».")
    configs = []
    threshold, k1, b, rrf_k, pool, diagnostics = 0.5, 1.2, 0.75, 60, 100, False
    if mode == "Автоматический":
        try:
            doc = github_book()
            configs, reports = automatic_configs(doc["sheets"], doc["name"], source_key("github", DEFAULT_XLSX_URL))
            st.caption("Таблица загружена из GitHub. Поиск идёт по колонкам с *** в названии; без меток — по первой колонке. Все поля строки доступны в карточке.")
            for report in reports:
                column_names = "», «".join(report["columns"])
                st.caption(f'{report["sheet"]}: поиск по «{column_names}» · строк: {report["rows"]} · пропущено без поискового текста: {report["skipped"]}')
                if report["nontext"]:
                    st.warning(f'На листе «{report["sheet"]}» в поисковых колонках преимущественно даты или числа. Можно отметить другие заголовки меткой *** в Excel или выбрать колонки в ручном режиме.')
                if report["header_warning"]:
                    st.warning(f'На листе «{report["sheet"]}» заголовки, возможно, ниже первой строки. Автоматический режим использует строку 1; другую можно выбрать в ручном режиме.')
                if report["missing_formulas"] or report["error_cells"]:
                    st.warning(f'Лист «{report["sheet"]}»: пустых результатов формул — {report["missing_formulas"]}, ошибок ячеек — {report["error_cells"]}. Эти ячейки считаются пустыми.')
        except Exception as exc:
            st.error(f"Не удалось загрузить таблицу из GitHub: {exc}")
            st.info("Попробуйте позже или откройте ручной режим и загрузите свою XLSX-книгу.")
            return
    else:
        with st.expander("⚙️ Ручной режим — источники, колонки и параметры поиска", expanded=True):
            uploads = st.file_uploader("Свои Excel-книги (.xlsx), необязательно", type=["xlsx"], accept_multiple_files=True, key="manual_uploads")
            st.caption("Без загрузки используется GitHub-таблица. Свои файлы заменяют её только в ручном режиме.")
            books = {}
            if uploads:
                for index, file in enumerate(uploads):
                    try:
                        if not file.name.casefold().endswith(".xlsx"):
                            raise ValueError("Поддерживаются только .xlsx.")
                        content = file.getvalue()
                        if len(content) > MAX_XLSX_BYTES:
                            raise ValueError("Размер книги превышает 10 МБ.")
                        sid = source_key("local", f"{file.name}:{index}")
                        books[sid] = {"name": file.name, "sheets": read_xlsx(content),
                                      "content_stamp": hashlib.sha256(content).hexdigest()[:16]}
                    except Exception as exc:
                        st.warning(f"{file.name}: {exc}")
            else:
                if st.button("Обновить GitHub-таблицу", key="refresh_github"):
                    fetch_github_xlsx.clear()
                try:
                    books[source_key("github", DEFAULT_XLSX_URL)] = github_book()
                except Exception as exc:
                    st.warning(f"GitHub-таблица недоступна: {exc}. Можно загрузить свою книгу выше.")
            def book_label(sid):
                name = books[sid]["name"]
                duplicate = sum(book["name"] == name for book in books.values()) > 1
                return f"{name} · {sid}" if duplicate else name
            active = st.multiselect("Книги для работы", list(books), default=list(books), format_func=book_label, key="manual_books")
            for sid in active:
                st.subheader(book_label(sid))
                configs.extend(configure_xlsx(books[sid], sid))
            threshold = st.slider("Порог семантического сходства", 0.0, 1.0, 0.5, 0.01,
                                  help="Действует в семантическом и гибридном поиске. Значение нужно проверить на реальных запросах.")
            k1 = st.slider("BM25: насыщение частоты k1", 0.1, 3.0, 1.2, 0.1)
            b = st.slider("BM25: учёт длины текста b", 0.0, 1.0, 0.75, 0.05)
            rrf_k = int(st.number_input("RRF: константа объединения", min_value=1, max_value=200, value=60))
            pool = int(st.number_input("Кандидатов из каждого рейтинга", min_value=20, max_value=1000, value=100))
            diagnostics = st.checkbox("Показать отдельные выдачи и ID строк", value=False)
    if not configs:
        st.info("Нет настроенных листов для поиска.")
        return
    try:
        df = build_database(configs)
    except Exception as exc:
        st.error(f"Ошибка обработки таблиц: {exc}")
        return
    if df.empty:
        st.warning("Нет строк для поиска. Проверьте отмеченные колонки (или первую, если меток нет) либо настройки ручного режима.")
        return
    total = int(df["case_uid"].nunique())
    st.caption(f"В базе: {total} строк · листов: {len(configs)}")
    if not query.strip():
        return
    if search_type == "lexical" and not any(len(word) >= 3 for word in tokenize(query)):
        st.info("Введите хотя бы одно слово или фрагмент длиной от трёх символов.")
        return
    actual_type = search_type
    try:
        if search_type != "lexical":
            with st.spinner("Подготовка семантического поиска…"):
                attach_embeddings(df)
        with st.spinner("Поиск…"):
            results = search_bundle(query, df, top_k, threshold, search_type, k1, b, rrf_k, pool)
    except Exception as exc:
        if search_type != "hybrid":
            st.error(f"Выбранный поиск недоступен: {exc}")
            if search_type == "semantic":
                st.info("Для текстового поиска выберите «По совпадению».")
            return
        st.warning(f"Семантическая часть недоступна: {exc}. Показаны только результаты BM25.")
        actual_type = "lexical"
        try:
            results = search_bundle(query, df, top_k, threshold, "bm25", k1, b, rrf_k, pool)
        except Exception as fallback_exc:
            st.error(f"Лексический поиск недоступен: {fallback_exc}")
            return
    titles = {"hybrid": "Гибридный поиск · RRF", "semantic": "Семантический поиск", "lexical": "Лексический поиск · BM25" if search_type == "hybrid" else "По совпадению"}
    render_results(titles[actual_type], results[actual_type], total)
    st.caption("Баллы BM25, семантики и RRF имеют разные шкалы и не являются вероятностью правильного ответа.")
    if diagnostics:
        st.subheader("Диагностика")
        if search_type == "hybrid" and actual_type == "hybrid":
            render_results("BM25", results["lexical"], total)
            render_results("Семантика", results["semantic"], total, icon="✨")
        catalog = df[["case_uid", "source_file", "sheet_name", "row_number", "title"]]
        st.dataframe(catalog, use_container_width=True, hide_index=True)
        st.download_button("Скачать ID строк", catalog.to_csv(index=False).encode("utf-8-sig"), "row_catalog.csv", "text/csv")


if __name__ == "__main__":
    main()
