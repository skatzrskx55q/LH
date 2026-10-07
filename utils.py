"""Чтение XLSX, индекс строк и гибридный поиск. Python 3.11–3.12."""
import functools
import hashlib
import math
import re
import threading
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, time
from io import BytesIO
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

import numpy as np
import pandas as pd
import streamlit as st

MODEL_ID = "skatzR/USER-BGE-M3-MiniLM-L12-v2-Distilled"
MAX_XLSX_BYTES = 10 * 1024 * 1024
MAX_XLSX_UNPACKED_BYTES = 50 * 1024 * 1024
MAX_XLSX_ROWS = 20000
MAX_XLSX_COLUMNS = 100
MAX_XLSX_SHEETS = 20
MAX_XLSX_CELLS = 300000
TITLE_ALIASES = {"фраза", "запрос", "обращение", "вопрос", "заголовок", "phrase", "query", "title"}
DATE_ALIASES = {"дата", "date", "дата обращения", "дата создания"}
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
DEFAULT_XLSX_URL = "https://raw.githubusercontent.com/skatzrskx55q/LH/main/example_cases.xlsx"


def github_xlsx_url(value):
    if not safe_http_url(value):
        raise ValueError("Некорректная ссылка XLSX.")
    parts = urlsplit(value)
    path = parts.path
    if parts.hostname == "github.com":
        chunks = path.strip("/").split("/")
        if len(chunks) < 5 or chunks[2] != "blob":
            raise ValueError("Нужна ссылка GitHub на файл XLSX.")
        path = "/" + "/".join(chunks[:2] + chunks[3:])
    elif parts.hostname != "raw.githubusercontent.com":
        raise ValueError("Разрешены только XLSX из GitHub.")
    if parts.scheme != "https" or parts.port not in (None, 443) or not path.lower().endswith(".xlsx"):
        raise ValueError("Нужна HTTPS-ссылка на .xlsx.")
    return urlunsplit(("https", "raw.githubusercontent.com", path, "", ""))


@st.cache_data(show_spinner=False, ttl=300, max_entries=8)
def fetch_github_xlsx(url=DEFAULT_XLSX_URL):
    class SafeRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return super().redirect_request(req, fp, code, msg, headers, github_xlsx_url(newurl))
    url = github_xlsx_url(url)
    opener = build_opener(SafeRedirect())
    request = Request(url, headers={"User-Agent": "AnnotatorExcel/1.0"})
    with opener.open(request, timeout=30) as response:
        content = response.read(MAX_XLSX_BYTES + 1)
    if len(content) > MAX_XLSX_BYTES:
        raise ValueError("Размер GitHub-книги превышает 10 МБ.")
    return content


@st.cache_resource(show_spinner=False)
def get_model(model_id=MODEL_ID):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_id, trust_remote_code=False)


@st.cache_resource(show_spinner=False)
def model_lock():
    # Модель и токенизатор используются несколькими сессиями Streamlit.
    return threading.RLock()


@st.cache_resource(show_spinner=False)
def get_morph():
    import pymorphy3
    return pymorphy3.MorphAnalyzer()


def normalize_spaces(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def preprocess(text):
    return normalize_spaces(text).casefold().replace("ё", "е")



def tokenize(text):
    return tuple(TOKEN_RE.findall(preprocess(text)))


@functools.lru_cache(maxsize=50000)
def lemmatize_cached(word):
    return get_morph().parse(word)[0].normal_form if word.isalpha() else word


def lemmatize(word):
    return lemmatize_cached(word)


def safe_http_url(value):
    """Проверяет адрес для отображения ссылки; ничего не скачивает."""
    value = str(value or "").strip(" ")
    if not value or re.search(r"""[\s\x00-\x1f\x7f<>"'\\]""", value):
        return None
    try:
        parts = urlsplit(value)
        if (parts.scheme.lower() not in {"http", "https"} or not parts.hostname
                or parts.username is not None or parts.password is not None):
            return None
        _ = parts.port  # отклоняет некорректный порт
        return value
    except ValueError:
        return None


def excel_value(value):
    """Сохраняет нули и переносы строк, приводит даты к читаемому виду."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y" if value.time() == time() else "%d.%m.%Y %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        if value.is_integer():
            return str(int(value))
    return str(value).strip()


def excel_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                pass
    return None


def suggest_header_row(rows):
    """Предлагает строку заголовков; её всегда можно изменить вручную."""
    best = (float("-inf"), 1)
    aliases = TITLE_ALIASES | DATE_ALIASES | {"интент", "интенты", "комментарий", "comment", "intent"}
    for number, row in enumerate(rows[:50], 1):
        values = [normalize_spaces(excel_value(v)) for v in row if excel_value(v)]
        if not values:
            continue
        known = sum(preprocess(v) in aliases for v in values)
        short = sum(len(v) <= 60 for v in values)
        unique = len(set(preprocess(v) for v in values))
        score = known * 10 + min(len(values), 10) + short / len(values) + unique / len(values)
        if score > best[0]:
            best = (score, number)
    return best[1]


@st.cache_data(show_spinner=False, max_entries=8)
def read_xlsx(content):
    """Читает только XLSX. Формулы не вычисляет: берёт сохранённые значения."""
    from openpyxl import load_workbook
    if not content or len(content) > MAX_XLSX_BYTES:
        raise ValueError("Пустой XLSX или размер больше 10 МБ.")
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            if len(archive.infolist()) > 2000 or sum(i.file_size for i in archive.infolist()) > MAX_XLSX_UNPACKED_BYTES:
                raise ValueError("Книга слишком велика после распаковки (лимит 50 МБ).")
        formulas = load_workbook(BytesIO(content), read_only=True, data_only=False, keep_links=False)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Не удалось открыть XLSX. Нужна обычная книга без пароля.") from exc
    values = None
    try:
        values = load_workbook(BytesIO(content), read_only=True, data_only=True, keep_links=False)
        if len(formulas.worksheets) > MAX_XLSX_SHEETS:
            raise ValueError(f"В книге больше {MAX_XLSX_SHEETS} листов.")
        sheets, budget = {}, 0
        for ws in formulas.worksheets:
            if (ws.max_row or 0) > MAX_XLSX_ROWS or (ws.max_column or 0) > MAX_XLSX_COLUMNS:
                raise ValueError(f"Лист «{ws.title}»: лимит {MAX_XLSX_ROWS} строк и {MAX_XLSX_COLUMNS} колонок. Удалите лишние пустые строки/колонки и их форматирование.")
            rows, missing, errors = [], 0, 0
            for formula_row, cached_row in zip(ws.iter_rows(), values[ws.title].iter_rows()):
                if len(rows) >= MAX_XLSX_ROWS or len(formula_row) > MAX_XLSX_COLUMNS:
                    raise ValueError(f"Лист «{ws.title}» превышает лимит строк или колонок.")
                budget += len(formula_row)
                if budget > MAX_XLSX_CELLS:
                    raise ValueError(f"В книге больше {MAX_XLSX_CELLS} ячеек. Разделите файл.")
                row = []
                for cell, cached in zip(formula_row, cached_row):
                    value = cached.value
                    if cell.data_type == "f" and value is None:
                        missing += 1
                    if cached.data_type == "e":
                        errors += 1
                        value = None
                    row.append(value)
                rows.append(tuple(row))
            while rows and not any(excel_value(v) for v in rows[-1]):
                rows.pop()
            sheets[ws.title] = {"rows": tuple(rows), "header_row": suggest_header_row(rows),
                               "missing_formulas": missing, "error_cells": errors,
                               "visible": ws.sheet_state == "visible"}
        return sheets
    finally:
        formulas.close()
        if values is not None:
            values.close()


@st.cache_data(show_spinner=False, max_entries=32)
def xlsx_table(sheet, header_row=1):
    rows = sheet["rows"]
    if not isinstance(header_row, int) or not 1 <= header_row <= max(1, len(rows)):
        raise ValueError("Строка заголовков отсутствует на листе.")
    if not rows:
        return {"columns": [], "records": [], "date_columns": []}
    width = max((i + 1 for row in rows[header_row - 1:] for i, v in enumerate(row) if excel_value(v)), default=0)
    header = rows[header_row - 1]
    columns, used = [], set()
    for i in range(width):
        original = normalize_spaces(excel_value(header[i])) if i < len(header) else ""
        base = original or f"Колонка {i + 1}"
        label, suffix = base, 2
        while label in used:
            label = f"{base} ({suffix})"
            suffix += 1
        used.add(label)
        columns.append({"id": f"c{i}", "label": label, "original": original})
    records, date_cols = [], set()
    for row_number, row in enumerate(rows[header_row:], header_row + 1):
        cells, dates = {}, {}
        for i, column in enumerate(columns):
            value = row[i] if i < len(row) else None
            cells[column["id"]] = excel_value(value)
            parsed_date = excel_date(value)
            if parsed_date is not None:
                dates[column["id"]] = parsed_date
                date_cols.add(column["id"])
        if any(cells.values()):
            records.append({"row_number": row_number, "cells": cells, "dates": dates})
    return {"columns": columns, "records": records,
            "date_columns": [c["id"] for c in columns if c["id"] in date_cols]}


def suggest_xlsx_columns(table):
    columns = table["columns"]
    title = next((c["id"] for c in columns if preprocess(c["original"]) in TITLE_ALIASES), None)
    if title is None:
        title = next((c["id"] for c in columns if c["id"] not in table["date_columns"]
                      and preprocess(c["original"]) not in DATE_ALIASES), None)
    title = title or (columns[0]["id"] if columns else None)
    search = [c["id"] for c in columns if c["id"] not in table["date_columns"]
              and preprocess(c["original"]) not in DATE_ALIASES]
    return {"title_column": title, "search_columns": search or ([title] if title else [])}


def parse_xlsx_cases(cfg):
    if cfg.get("kind") != "xlsx" or "table" not in cfg or "sheet_name" not in cfg:
        raise ValueError("Источник должен быть настроенным листом XLSX.")
    table = cfg["table"]
    columns = {c["id"]: c["label"] for c in table["columns"]}
    display_labels = {c["id"]: c.get("display_label", c["label"]) for c in table["columns"]}
    title_col = cfg.get("title_column")
    search_cols = list(cfg.get("search_columns", list(columns)))
    display_cols = list(cfg.get("display_columns", list(columns)))
    if (title_col is not None and title_col not in columns) or any(c not in columns for c in search_cols + display_cols):
        raise ValueError("Выбрана отсутствующая колонка.")
    if not search_cols:
        raise ValueError("Выберите хотя бы одну колонку для поиска.")
    date_col, start, end = cfg.get("date_column"), cfg.get("date_from"), cfg.get("date_to")
    if date_col is not None and date_col not in columns:
        raise ValueError("Колонка даты отсутствует.")
    if start and end and start > end:
        raise ValueError("Начальная дата позже конечной.")
    sheet_id = hashlib.sha256(cfg["sheet_name"].encode("utf-8")).hexdigest()[:16]
    cases = []
    for record in table["records"]:
        cells, row_number = record["cells"], record["row_number"]
        if date_col is not None:
            value = record["dates"].get(date_col)
            if value is None or (start and value < start) or (end and value > end):
                continue
        if not any(cells[c] for c in search_cols):
            continue
        title = (cells.get(title_col, "") if title_col else "") or f"Строка {row_number}"
        # В индекс идут только значения: названия колонок не создают совпадения.
        text = "\n".join(cells[c] for c in search_cols if cells[c])
        uid = f'{cfg.get("source_id", cfg["name"])}::sheet:{sheet_id}::row:{row_number}'
        cases.append({"case_uid": uid, "source_file": cfg["name"], "sheet_name": cfg["sheet_name"],
                      "row_number": row_number, "title": title, "search_text": text,
                      "search_proc": preprocess(text), "fields": [
                          {"label": display_labels[c], "value": cells[c]} for c in display_cols
                          if cells[c] and c != title_col]})
    return cases


@st.cache_data(show_spinner=False, max_entries=32)
def build_database(workbook_configs):
    """Индексирует только строки настроенных листов XLSX."""
    rows, identities = [], set()
    for cfg in workbook_configs:
        if cfg.get("kind") != "xlsx" or "table" not in cfg or "sheet_name" not in cfg:
            raise ValueError("Для индекса нужны настроенные листы XLSX.")
        identity = (cfg.get("source_id", cfg["name"]), cfg["sheet_name"])
        if identity in identities:
            raise ValueError("Один лист одного источника выбран несколько раз.")
        identities.add(identity)
        rows.extend(parse_xlsx_cases(cfg))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    texts = tuple(row["search_text"] for row in rows)
    tokens = tuple(tokenize(text) for text in texts)
    lemmas = tuple(tuple(map(lemmatize_cached, words)) for words in tokens)
    postings, lemma_postings = defaultdict(set), defaultdict(set)
    for i, (words, norms) in enumerate(zip(tokens, lemmas)):
        for word in set(words):
            postings[word].add(i)
        for word in set(norms):
            lemma_postings[word].add(i)
    df.attrs.update(indexed_texts=texts, tokens=tokens, lemmas=lemmas,
                    postings=dict(postings), lemma_postings=dict(lemma_postings),
                    term_counts=tuple(Counter(words) for words in lemmas),
                    doc_lengths=np.asarray([len(words) for words in lemmas], dtype=np.float64))
    return df


def automatic_configs(sheets, name="example_cases.xlsx", source_id="github-default"):
    """Строго: первая строка — подписи, первая физическая колонка — поиск."""
    configs, reports = [], []
    for sheet_name, sheet in sheets.items():
        if not sheet.get("visible", True) or not sheet["rows"]:
            continue
        table = xlsx_table(sheet, 1)
        if not table["columns"]:
            continue
        first = table["columns"][0]["id"]
        skipped = sum(not record["cells"][first] for record in table["records"])
        populated = [r for r in table["records"] if r["cells"][first]]
        date_or_number = sum(first in r["dates"] or bool(re.fullmatch(r"[\d\s.,+-]+", r["cells"][first])) for r in populated)
        reports.append({"sheet": sheet_name, "column": table["columns"][0]["label"],
                        "skipped": skipped, "rows": len(populated),
                        "nontext": bool(populated) and date_or_number / len(populated) >= 0.5,
                        "header_warning": sheet["header_row"] != 1,
                        "missing_formulas": sheet["missing_formulas"], "error_cells": sheet["error_cells"]})
        configs.append({"kind": "xlsx", "name": name, "source_id": source_id, "sheet_name": sheet_name,
                        "table": table, "title_column": first, "search_columns": [first],
                        "display_columns": [c["id"] for c in table["columns"]]})
    return configs, reports


@st.cache_data(show_spinner=False, max_entries=8)
def cached_embeddings(texts, model_id=MODEL_ID):
    """Ключ — тексты, а не параметры отображения. Длинные кейсы режутся по токенам."""
    with model_lock():
        model = get_model(model_id)
        max_tokens = max(8, int(model.max_seq_length) - model.tokenizer.num_special_tokens_to_add(pair=False))
        overlap = min(32, max_tokens // 4)
        chunks, owners = [], []
        for i, text in enumerate(texts):
            ids = model.tokenizer.encode(text, add_special_tokens=False)
            for start in range(0, max(1, len(ids)), max_tokens - overlap):
                chunks.append(model.tokenizer.decode(ids[start:start + max_tokens], skip_special_tokens=True))
                owners.append(i)
                if start + max_tokens >= len(ids):
                    break
        matrix = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True,
                              batch_size=32, show_progress_bar=False)
        return np.asarray(matrix, dtype=np.float32), np.asarray(owners, dtype=np.int64)


def attach_embeddings(df, model_id=MODEL_ID):
    if not df.empty:
        matrix, owners = cached_embeddings(df.attrs["indexed_texts"], model_id)
        df.attrs.update(phrase_embs=matrix, embedding_owners=owners, model_id=model_id)
    return df


@st.cache_data(show_spinner=False, max_entries=256)
def encode_query(query, model_id=MODEL_ID):
    with model_lock():
        return np.asarray(get_model(model_id).encode(normalize_spaces(query), convert_to_numpy=True,
                          normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)


def semantic_scores(query, df):
    if df.empty or not tokenize(query) or "phrase_embs" not in df.attrs:
        return None
    vector = encode_query(query, df.attrs.get("model_id", MODEL_ID))
    scores = np.clip(df.attrs["phrase_embs"] @ vector.reshape(-1), -1.0, 1.0)
    result = np.full(len(df), -1.0, dtype=np.float32)
    np.maximum.at(result, df.attrs.get("embedding_owners", np.arange(len(df))), scores)
    return result


def _result_from_row(row, score=None, **details):
    result = {key: row[key] for key in ("case_uid", "source_file", "sheet_name", "row_number", "title", "fields", "search_text")}
    result["row_number"] = int(result["row_number"])
    if score is not None:
        result["score"] = float(score)
    result.update(details)
    return result


def deduplicate_results(results, top_k):
    best = {}
    for item in results:
        prev = best.get(item["case_uid"])
        if prev is None or item.get("score", 1) > prev.get("score", 1):
            best[item["case_uid"]] = item
    return sorted(best.values(), key=lambda item: (-item.get("score", 1), item["case_uid"]))[:max(0, top_k)]


def _contains_phrase(words, query_words):
    return any(words[start:start + len(query_words)] == query_words
               for start in range(len(words) - len(query_words) + 1))


def lexical_scores(query, df, k1=1.2, b=0.75):
    """BM25 с лемматизацией: OR по словам запроса, без поиска частей слов."""
    if k1 <= 0 or not 0 <= b <= 1:
        raise ValueError("Некорректные параметры BM25.")
    result = np.zeros(len(df), dtype=np.float64)
    words = set(map(lemmatize_cached, tokenize(query)))
    if not words or df.empty:
        return result, {}
    attrs = df.attrs
    lengths = attrs["doc_lengths"]
    avg_length = max(float(lengths.mean()), 1.0)
    for word in words:
        matching = attrs["lemma_postings"].get(word, set())
        if not matching:
            continue
        idf = math.log1p((len(df) - len(matching) + 0.5) / (len(matching) + 0.5))
        for i in matching:
            tf = attrs["term_counts"][i][word]
            result[i] += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * lengths[i] / avg_length))
    return result, {i: "BM25" for i in np.flatnonzero(result > 0)}


def search_bundle(query, df, top_k=5, threshold=0.5, search_type="hybrid",
                  bm25_k1=1.2, bm25_b=0.75, rrf_k=60, candidate_pool=100):
    if search_type not in {"hybrid", "semantic", "lexical"}:
        raise ValueError("Неизвестный тип поиска.")
    if not -1 <= threshold <= 1 or rrf_k < 1 or top_k < 1 or candidate_pool < 1:
        raise ValueError("Некорректные параметры поиска.")
    output = {"hybrid": [], "semantic": [], "lexical": []}
    if df.empty or not tokenize(query):
        return output
    lexical, semantic = [], []
    if search_type in {"hybrid", "lexical"}:
        scores, _ = lexical_scores(query, df, bm25_k1, bm25_b)
        lexical = [_result_from_row(df.iloc[i], score, lexical_score=float(score), match_type="BM25")
                   for i, score in enumerate(scores) if score > 0]
        lexical = deduplicate_results(lexical, len(df))
    if search_type in {"hybrid", "semantic"}:
        scores = semantic_scores(query, df)
        if scores is None:
            raise RuntimeError("Семантический индекс недоступен.")
        semantic = [_result_from_row(df.iloc[i], score, semantic_score=float(score), match_type="Семантика")
                    for i, score in enumerate(scores) if score >= threshold]
        semantic = deduplicate_results(semantic, len(df))
    output["lexical"] = lexical[:top_k]
    output["semantic"] = semantic[:top_k]
    if search_type != "hybrid":
        return output
    pool_size = max(candidate_pool, top_k)
    fused = {}
    for kind, results in (("lexical", lexical), ("semantic", semantic)):
        for rank, item in enumerate(results[:pool_size], 1):
            entry = fused.setdefault(item["case_uid"], {**item, "score": 0.0,
                                     "lexical_score": None, "semantic_score": None,
                                     "lexical_rank": None, "semantic_rank": None,
                                     "match_type": "RRF"})
            entry["score"] += 1.0 / (rrf_k + rank)
            entry[kind + "_score"] = item["score"]
            entry[kind + "_rank"] = rank
    output["hybrid"] = deduplicate_results(list(fused.values()), top_k)
    return output


def keyword_search(query, df, top_k=5):
    return search_bundle(query, df, top_k, search_type="lexical")["lexical"]


def semantic_search(query, df, top_k=5, threshold=0.5):
    return search_bundle(query, df, top_k, threshold, "semantic")["semantic"]


def hybrid_search(query, df, top_k=5, threshold=0.5):
    return search_bundle(query, df, top_k, threshold, "hybrid")["hybrid"]
