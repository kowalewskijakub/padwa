"""
Moduł przeglądania dokumentów.

Umożliwia użytkownikowi przeglądanie listy obserwowanych dokumentów,
filtrowanie ich oraz zarządzanie nimi (podgląd szczegółów, archiwizacja).
"""
import streamlit as st

from src.core.dtos.doc_dto import DocProcessedDTO
from src.presentation.app_state import get_state


def render_doc_card(doc: DocProcessedDTO) -> None:
    """
    Wyświetla kartę z podstawowymi informacjami o dokumencie.

    Renderuje kontener z tytułem dokumentu, podsumowaniem (skróconym jeśli za długie)
    oraz przyciskami akcji umożliwiającymi podgląd szczegółów i archiwizację.

    :param doc: Obiekt DTO zawierający dane przetworzonego dokumentu
    """
    with st.container(border=True):
        st.markdown(f"**{doc.title}**")

        if doc.summary:
            max_summary_length = 300
            if len(doc.summary) > max_summary_length:
                display_summary = doc.summary[:max_summary_length] + "..."
                st.markdown(display_summary)
            else:
                st.markdown(doc.summary)

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
    Wyświetla dialog ze szczegółymi informacjami o dokumencie.

    Prezentuje kompletne dane dokumentu w formie dialogu, w tym statystyki
    (liczbę fragmentów, ocenę wstępną), pełne podsumowanie oraz treść
    wszystkich wyodrębnionych fragmentów tekstu.

    :param doc: Obiekt DTO zawierający dane przetworzonego dokumentu
    """
    st.header(doc.title)

    chunks = get_state().docs_service.get_chunks_for_doc(doc.id)

    col_count, col_flag = st.columns(2)

    with col_count:
        st.metric("Fragmenty", len(chunks))

    with col_flag:
        relevancy_status = "nieistotny" if doc.flag else "istotny"
        st.metric("Ocena wstępna", relevancy_status)

    if doc.summary:
        st.subheader("Podsumowanie")
        st.info(doc.summary)

    st.subheader("Fragmenty")
    for i, chunk in enumerate(chunks):
        with st.expander(f"Fragment nr {i + 1}", expanded=True):
            st.markdown(chunk.text)


st.header("Dokumentacja prawna")

all_docs = get_state().docs_service.get_all()

if not all_docs:
    st.info("Nie znaleziono żadnych obserwowanych dokumentów.")
else:
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
