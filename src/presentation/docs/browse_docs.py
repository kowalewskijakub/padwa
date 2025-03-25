import streamlit as st
from presentation.app_state import get_state

from src.application.dtos.doc_dto import DocProcessedDTO


def render_doc_card(doc: DocProcessedDTO) -> None:
    """
    Wyświetla kartę z podstawowymi informacjami o dokumencie.

    :param doc: Obiekt DTO z danymi dokumentu
    """
    with st.container(border=True):
        # Tytuł
        st.markdown(f"**{doc.title}**")

        # Podsumowanie (skrócone, jeśli za długie)
        if doc.summary:
            max_summary_length = 300
            if len(doc.summary) > max_summary_length:
                display_summary = doc.summary[:max_summary_length] + "..."
                st.markdown(display_summary)
            else:
                st.markdown(doc.summary)

        # Przyciski akcji
        col_details, col_delete = st.columns(2)

        with col_details:
            details_button = st.button(
                "Więcej",
                key=f"details_{doc.id}",
                icon=":material/info:",
                use_container_width=True
            )
            if details_button:
                render_doc_details(doc)

        with col_delete:
            delete_button = st.button(
                "Archiwizuj",
                key=f"delete_{doc.id}",
                icon=":material/archive:",
                use_container_width=True
            )
            if delete_button:
                if get_state().docs_service.archive_document(doc.id):
                    st.success(f"Dokument '{doc.title}' został zarchiwizowany.")
                    st.rerun()
                else:
                    st.error("Nie udało się zarchiwizować dokumentu.")


@st.dialog("Szczegóły dokumentu")
def render_doc_details(doc: DocProcessedDTO) -> None:
    """
    Wyświetla dialog ze szczegółami dokumentu.

    Pokazuje użytkownikowi podstawowe statystyki (np. ilość wyodrębnionych fragmentów) oraz
    ich treść.

    :param doc: Obiekt DTO z danymi dokumentu
    """
    st.header(doc.title)

    chunks = get_state().docs_service.get_chunks_for_doc(doc.id)

    # Kolumny z metrykami
    col_count, col_flag = st.columns(2)

    with col_count:
        st.metric("Fragmenty", len(chunks))

    with col_flag:
        relevancy_status = "nieistotny" if doc.flag else "istotny"
        st.metric("Ocena wstępna", relevancy_status)

    # Podsumowanie
    if doc.summary:
        st.subheader("Podsumowanie")
        st.info(doc.summary)

    # Fragmenty
    st.subheader("Fragmenty")
    for i, chunk in enumerate(chunks):
        with st.expander(f"Fragment nr {i + 1}", expanded=True):
            st.markdown(chunk.text)


st.header("Dokumentacja prawna")

# Pobierz wszystkie dokumenty
all_docs = get_state().docs_service.get_all()

if not all_docs:
    st.info("Nie znaleziono żadnych obserwowanych dokumentów.")
else:
    # Kontrolki filtrów
    with st.container():
        title_search = st.text_input(
            "Tytuł"
        )

    show_flagged = st.checkbox(
        "Uwzględnij nieistotne",
        value=False,
        help="""
        Domyślnie ukryte zostały dokumenty, które zostały oznaczone
        jako nieistotne.
        """
    )

    filtered_docs = all_docs.copy()
    if not show_flagged:
        filtered_docs = [doc for doc in filtered_docs if not doc.flag]
    if title_search:
        filtered_docs = [
            doc for doc in filtered_docs
            if title_search.lower() in doc.title.lower()
        ]

    if not filtered_docs:
        st.info("Nie znaleziono dokumentów, które spełniają kryteria wyszukiwania. "
                "Spróbuj je zmienić, aby wyświetlić dostępne dokumenty.")

    st.write(f"Znaleziono {len(filtered_docs)} dokumentów.")

    cols = st.columns(2)
    for i, doc in enumerate(filtered_docs):
        with cols[i % 2]:
            render_doc_card(doc)
