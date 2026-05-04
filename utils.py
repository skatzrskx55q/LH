import functools
import re
from itertools import product
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import requests


MODEL_ID = "skatzR/USER-BGE-M3-MiniLM-L12-v2-Distilled"
GITHUB_TXT_URLS: List[str] = [
    # "https://raw.githubusercontent.com/<user>/<repo>/<branch>/<file>.txt",
]
REQUEST_TIMEOUT_SECONDS = 30

CASE_MARKER_RE = re.compile(r"==\s*(?P<title>.*?)\s*==", re.DOTALL)
SERVICE_FIELD_RE = re.compile(r"^\s*(?P<label>[^:\n]{1,80})\s*:\s*(?P<value>.*)$")


@functools.lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_ID)


@functools.lru_cache(maxsize=1)
def get_morph():
    try:
        import pymorphy3

        return pymorphy3.MorphAnalyzer()
    except Exception:
        pass

    try:
        import pymorphy2

        return pymorphy2.MorphAnalyzer()
    except Exception:
        return None


def decode_text_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def normalize_spaces(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def preprocess(text: Any) -> str:
    return normalize_spaces(text).lower()


def lemmatize(word: str) -> str:
    morph = get_morph()
    if morph is None:
        return word
    return morph.parse(word)[0].normal_form


@functools.lru_cache(maxsize=10000)
def lemmatize_cached(word: str) -> str:
    return lemmatize(word)


def split_by_slash(phrase: str) -> List[str]:
    phrase = normalize_spaces(phrase)
    if not phrase:
        return []

    segments = [seg.strip() for seg in phrase.split("|")]
    variants: List[str] = []

    for segment in segments:
        parts: List[List[str]] = []
        last_idx = 0

        for match in re.finditer(r"\b[\w-]+(?:/[\w-]+)+\b", segment):
            if match.start() > last_idx:
                prefix = segment[last_idx:match.start()].strip()
                if prefix:
                    parts.append([prefix])

            options = [option.strip() for option in match.group(0).split("/") if option.strip()]
            parts.append(options)
            last_idx = match.end()

        if last_idx < len(segment):
            suffix = segment[last_idx:].strip()
            if suffix:
                parts.append([suffix])

        if not parts:
            variants.append(segment)
            continue

        for combination in product(*parts):
            combined = normalize_spaces(" ".join(combination))
            if combined:
                variants.append(combined)

    return list(dict.fromkeys(variants))


def parse_service_fields(tail: str) -> List[Dict[str, str]]:
    lines = [line.rstrip() for line in normalize_line_endings(tail).split("\n")]
    fields: List[Dict[str, str]] = []
    label = ""
    value_lines: List[str] = []
    preamble: List[str] = []

    def flush() -> None:
        nonlocal label, value_lines
        if label:
            fields.append({"label": label, "value": "\n".join(value_lines).strip()})
            label = ""
            value_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        match = SERVICE_FIELD_RE.match(line)
        if match:
            flush()
            label = normalize_spaces(match.group("label"))
            value = match.group("value").strip()
            value_lines = [value] if value else []
            continue

        if label:
            value_lines.append(line)
        else:
            preamble.append(line)

    flush()

    if preamble:
        fields.insert(0, {"label": "Описание", "value": "\n".join(preamble).strip()})

    return [field for field in fields if field["label"] or field["value"]]


def normalize_line_endings(text: Any) -> str:
    return str(text or "").replace("\r\n", "\n").replace("\r", "\n")


def parse_txt_cases(text: str, source_name: str = "document.txt") -> List[Dict[str, Any]]:
    text = normalize_line_endings(text)
    markers = list(CASE_MARKER_RE.finditer(text))
    cases: List[Dict[str, Any]] = []

    for index, marker in enumerate(markers, start=1):
        title = normalize_spaces(marker.group("title"))
        if not title:
            continue

        next_start = markers[index].start() if index < len(markers) else len(text)
        tail = text[marker.end():next_start].strip()
        fields = parse_service_fields(tail)
        variants = split_by_slash(title) or [title]

        for variant_index, variant in enumerate(variants, start=1):
            search_proc = preprocess(variant)
            cases.append(
                {
                    "case_uid": f"{source_name}::{index}",
                    "variant_uid": f"{source_name}::{index}::{variant_index}",
                    "source_file": source_name,
                    "case_index": index,
                    "title": title,
                    "search_text": variant,
                    "search_proc": search_proc,
                    "search_lemmas": {lemmatize_cached(word) for word in re.findall(r"\w+", search_proc)},
                    "fields": fields,
                    "raw_tail": tail,
                }
            )

    return cases


def load_text_documents(documents: Sequence[Tuple[str, str]]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []

    for source_name, text in documents:
        records.extend(parse_txt_cases(text, source_name=source_name))

    if not records:
        raise ValueError("В TXT-документах не найдено кейсов формата ==текст для поиска==.")

    df = pd.DataFrame(records)
    model = get_model()
    df.attrs["phrase_embs"] = model.encode(df["search_proc"].tolist(), convert_to_tensor=True)
    return df


def load_github_text_documents(urls: Optional[Sequence[str]] = None) -> pd.DataFrame:
    source_urls = [url.strip() for url in (urls if urls is not None else GITHUB_TXT_URLS) if str(url).strip()]
    if not source_urls:
        raise ValueError("Не указан GitHub TXT-файл. Добавьте raw URL в GITHUB_TXT_URLS в utils.py.")

    documents: List[Tuple[str, str]] = []
    for url in source_urls:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise ValueError(f"Ошибка загрузки {url}: HTTP {response.status_code}")

        source_name = url.rstrip("/").split("/")[-1] or "github.txt"
        documents.append((source_name, decode_text_bytes(response.content)))

    return load_text_documents(documents)


def _result_from_row(row: pd.Series, score: Optional[float] = None) -> Dict[str, Any]:
    result = {
        "case_uid": row["case_uid"],
        "source_file": row["source_file"],
        "case_index": int(row["case_index"]),
        "title": row["title"],
        "fields": row["fields"],
        "search_text": row["search_text"],
    }
    if score is not None:
        result["score"] = float(score)
    return result


def deduplicate_results(results: Iterable[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    best_by_case: Dict[str, Dict[str, Any]] = {}

    for item in results:
        uid = item["case_uid"]
        current_score = item.get("score", 1.0)
        previous = best_by_case.get(uid)
        if previous is None or current_score > previous.get("score", 1.0):
            best_by_case[uid] = item

    ordered = sorted(best_by_case.values(), key=lambda item: item.get("score", 1.0), reverse=True)
    return ordered[:top_k]


def semantic_search(query: str, df: pd.DataFrame, top_k: int = 5) -> List[Dict[str, Any]]:
    if df.empty:
        return []

    from sentence_transformers import util

    model = get_model()
    query_emb = model.encode(preprocess(query), convert_to_tensor=True)
    sims = util.pytorch_cos_sim(query_emb, df.attrs["phrase_embs"])[0]

    ranked = sorted(
        (_result_from_row(df.iloc[idx], float(score)) for idx, score in enumerate(sims)),
        key=lambda item: item["score"],
        reverse=True,
    )
    return deduplicate_results(ranked, top_k=top_k)


def keyword_search(query: str, df: pd.DataFrame, top_k: int = 5) -> List[Dict[str, Any]]:
    query_proc = preprocess(query)
    query_words = re.findall(r"\w+", query_proc)
    if not query_words:
        return []

    query_lemmas = [lemmatize_cached(word) for word in query_words]
    matched: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        text = row["search_proc"]
        full_query_match = query_proc in text
        word_match = all(word in text for word in query_words)
        lemma_match = all(query_lemma in row["search_lemmas"] for query_lemma in query_lemmas)

        if not (full_query_match or word_match or lemma_match):
            continue

        if full_query_match:
            score = 3.0
        elif word_match:
            score = 2.0
        else:
            score = 1.0

        matched.append(_result_from_row(row, score=score))

    return deduplicate_results(matched, top_k=top_k)
