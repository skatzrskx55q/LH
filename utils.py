

def semantic_scores(query, df):
    if df.empty or not tokenize(query) or "phrase_embs" not in df.attrs:
        return None
    vector = encode_query(query, df.attrs.get("model_id", MODEL_ID))
    scores = np.clip(df.attrs["phrase_embs"] @ vector.reshape(-1), -1.0, 1.0)
    result = np.full(len(df), -1.0, dtype=np.float32)
    np.maximum.at(result, df.attrs.get("embedding_owners", np.arange(len(df))), scores)
    return result


def _result_from_row(row, score=None, **details):
    result = {key: row[key] for key in ("case_uid", "source_file", "case_index", "title", "fields", "search_text")}
    result["case_index"] = int(result["case_index"])
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


def lexical_scores(query, df, allow_substring=False):
    result = np.zeros(len(df), dtype=np.float32)
    kinds = {}
    words = tokenize(query)
    if not words or df.empty:
        return result, kinds
    norms = tuple(map(lemmatize_cached, words))
    attrs = df.attrs
    # Совместимость с DataFrame, построенным старым способом.
    if "tokens" not in attrs:
        texts = tuple(df["search_proc"])
        tokens = tuple(map(tokenize, texts))
        lemmas = tuple(tuple(map(lemmatize_cached, t)) for t in tokens)
        candidates = set(range(len(df)))
    else:
        tokens, lemmas = attrs["tokens"], attrs["lemmas"]
        exact = set.intersection(*(attrs["postings"].get(w, set()) for w in set(words)))
        inflected = set.intersection(*(attrs["lemma_postings"].get(w, set()) for w in set(norms)))
        candidates = exact | inflected
    for i in candidates:
        if _contains_phrase(tokens[i], words):
            result[i], kinds[i] = 3.0, "Фраза целиком"
        elif not (Counter(words) - Counter(tokens[i])):
            result[i], kinds[i] = 2.0, "Все слова"
        elif not (Counter(norms) - Counter(lemmas[i])):
            result[i], kinds[i] = 1.0, "Словоформы"
    if allow_substring:
        texts = attrs.get("indexed_texts", tuple(df["search_proc"]))
        for i, text in enumerate(texts):
            if result[i] == 0 and preprocess(query) in preprocess(text):
                result[i], kinds[i] = 0.3, "Часть слова (слабый сигнал)"
    return result, kinds


def search_bundle(query, df, top_k=5, threshold=0.5, semantic_weight=0.65,
                  allow_substring=False, use_semantic=True):
    if not 0 <= semantic_weight <= 1 or not -1 <= threshold <= 1:
        raise ValueError("Некорректные параметры поиска.")
    lex, kinds = lexical_scores(query, df, allow_substring)
    sem = semantic_scores(query, df) if use_semantic else None
    hybrid, semantic, lexical = [], [], []
    for i in range(len(df)):
        lscore = float(lex[i])
        sscore = float(sem[i]) if sem is not None else None
        if lscore > 0:
            lexical.append(_result_from_row(df.iloc[i], lscore, match_type=kinds[i]))
        if sscore is not None and sscore >= threshold:
            semantic.append(_result_from_row(df.iloc[i], sscore))
        if not (lscore > 0 or (sscore is not None and sscore >= threshold)):
            continue
        if sem is None:
            combined = lscore / 3
        else:
            combined = semantic_weight * max(0, sscore) + (1 - semantic_weight) * lscore / 3
        if lscore == 3:
            combined += 0.15
        hybrid.append(_result_from_row(df.iloc[i], combined, semantic_score=sscore,
                      lexical_score=lscore, match_type=kinds.get(i, "Семантика")))
    return {"hybrid": deduplicate_results(hybrid, top_k),
            "semantic": deduplicate_results(semantic, top_k),
            "lexical": deduplicate_results(lexical, top_k)}


def semantic_search(query, df, top_k=5, threshold=0.5):
    return search_bundle(query, df, top_k, threshold)["semantic"]


def keyword_search(query, df, top_k=5):
    return search_bundle(query, df, top_k, use_semantic=False)["lexical"]


def hybrid_search(query, df, top_k=5, threshold=0.5, semantic_weight=0.65):
    return search_bundle(query, df, top_k, threshold, semantic_weight)["hybrid"]
