import streamlit as st

from src.presentation.app_state import get_state


def render_document_uploader():
    """
    Renderuje formularz do przesyłania nowego dokumentu.
    """
    with st.form("upload_document_form"):
        uploaded_file = st.file_uploader(
            "Wybierz plik PDF",
            type=["pdf"]
        )
        submitted = st.form_submit_button("Dodaj", type="primary", icon=":material/add:")

        if submitted and uploaded_file:
            with st.spinner("Przetwarzanie dokumentu..."):
                try:
                    # Pobierz zawartość pliku jako bajty
                    pdf_content = uploaded_file.getvalue()

                    # Przetwórz dokument (zwraca DocProcessedDTO lub None)
                    processed_doc = get_state().docs_service.process_document(
                        pdf_content=pdf_content
                    )

                    if processed_doc:
                        st.success(f"Pomyślnie dodano dokument: {processed_doc.title}")
                    else:
                        st.error("Nie udało się dodać dokumentu.")

                except Exception as e:
                    st.error(f"Nieoczekiwany błąd: {str(e)}")
        elif submitted and not uploaded_file:
            st.warning("Proszę wybrać plik do przesłania.")


st.header("Dodaj dokument")

st.markdown("""
Dodaj dokument organizacyjny do systemu. Dokument zostanie przetworzony, 
a jego fragmenty będą porównane z aktami prawnymi w celu oceny relewancji.
""")

# Wyświetl formularz dodawania dokumentu
render_document_uploader()
