# wersja: chet-theia
import streamlit as st

from src.core.dtos.act_dto import ActApiDTO
from src.presentation.app_state import get_state


def render_act_search_form():
    """
    Wyświetla formularz wyszukiwania aktów prawnych po tytule.
    """

    # Inicjalizuje zmienne stanu
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    # Formularz wyszukiwania
    with st.form("search_act_form"):
        st.text_input("Tytuł", key="search_query")
        submitted = st.form_submit_button("Szukaj", type="primary", icon=":material/search:")
        if submitted:
            if st.session_state.search_query:
                with st.spinner("Wyszukiwanie aktów prawnych..."):
                    results = get_state().acts_service.find_base_acts_by_title(st.session_state.search_query)
                    st.session_state.search_results = results
            else:
                st.warning("Wprowadź tekst do wyszukiwania.")

    # Wyświetlanie wyników
    results = st.session_state.search_results
    if not results:
        if st.session_state.search_query:
            st.info(f"Nie znaleziono aktów prawnych odpowiadających zapytaniu.")
    else:
        st.caption(f"Znaleziono {len(results)} aktów prawnych.")

        for result in results:
            render_act_add_listing(result)


def render_act_add_listing(act: ActApiDTO) -> None:
    """
    Wyświetla akt prawny w formie listy z możliwością jego dodania do listy obserwowanych.
    """
    with st.container(border=True):

        st.markdown(f"**{act.title}**")
        st.caption(
            f"{act.publisher} {act.year} poz. {act.position} | "
            f"{act.status}")

        if st.button(
                label="Obserwuj",
                key=f"add_act_{act.publisher}_{act.year}_{act.position}",
                icon=":material/add:",
                type="secondary",
        ):
            with st.spinner(f"Przetwarzanie aktu prawnego..."):
                # Dodaj akt do listy obserwowanych
                act = get_state().acts_service.process_act(act)
            if act:
                st.success(f"{act.title} została dodany do listy obserwowanych.")
            else:
                st.error("Nie udało się dodać aktu prawnego.")


st.header("Wyszukaj akt prawny")
st.markdown("""
Wyszukaj akt prawny na podstawie nazwy lub jej fragmentu. 
Znalezione akty możesz dodać do listy obserwowanych.
""")

render_act_search_form()
