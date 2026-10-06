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
