import streamlit as st
from presentation.app_state import get_state

from src.application.dtos.act_dto import ActProcessedDTO


def render_act_card(act: ActProcessedDTO) -> None:
    """
    Wyświetla kartę z podstawowymi informacjami o akcie prawnym.

    :param act: Obiekt DTO z danymi aktu prawnego bez referencji
    """
    with st.container(border=True):
        # Tytuł i podstawowe metadane
        st.markdown(f"**{act.title}**")

        st.caption(f"{act.publisher} {act.year} poz. {act.position} | "
                   f"{act.status}")

        # Podsumowanie (skrócone, jeśli za długie)
        if act.summary:
            max_summary_length = 300
            if len(act.summary) > max_summary_length:
                display_summary = act.summary[:max_summary_length] + "..."
            st.markdown(display_summary)

        # Przyciski akcji
        col_details, col_consolidation, col_delete = st.columns(3)

        with col_details:
            details_button = st.button(
                "Więcej",
                key=f"details_{act.id}",
                icon=":material/info:",
                use_container_width=True
            )
            if details_button:
                render_act_details(act)

        with col_consolidation:
            consolidation_button = st.button(
                "Teksty jednolite",
                key=f"consolidation_{act.id}",
                icon=":material/book:",
                use_container_width=True
            )
            if consolidation_button:
                render_consolidation_acts(act)

        with col_delete:
            delete_button = st.button(
                "Archiwizuj",
                key=f"delete_{act.id}",
                icon=":material/archive:",
                use_container_width=True
            )
            if delete_button:
                if get_state().acts_service.archive_act(act.id):
                    st.success(f"Akt '{act.title}' został zarchiwizowany.")
                    st.rerun()
                else:
                    st.error("Nie udało się zarchiwizować aktu.")


@st.dialog("Szczegóły aktu prawnego")
def render_act_details(act: ActProcessedDTO) -> None:
    """
    Wyświetla dialog ze szczegółami aktu prawnego.

    Pokazuje użytkownikowi podstawowe statystyki (np. ilość wyodrębnionych fragmentów) oraz
    ich treść.

    :param act: Obiekt DTO z danymi aktu prawnego bez referencji
    """
    st.header(act.title)
    st.caption(f"{act.publisher} {act.year} poz. {act.position} | "
               f"{act.status}")

    chunks = get_state().acts_service.get_chunks_for_act(act.id)

    # Kolumny z metrykami
    col_count, col_flag, col_status = st.columns(3)

    with col_count:
        st.metric("Fragmenty", len(chunks))

    with col_flag:
        relevancy_status = "nieistotny" if act.flag else "istotny"
        st.metric("Ocena wstępna", relevancy_status)

    with col_status:
        st.metric("Status", act.status)

    # Podsumowanie
    if act.summary:
        st.subheader("Podsumowanie")
        st.info(act.summary)

    # Fragmenty
    st.subheader("Fragmenty")
    for i, chunk in enumerate(chunks):
        with st.expander(f"Fragment nr {i + 1}", expanded=True):
            st.markdown(chunk.text)


@st.dialog("Teksty jednolite")
def render_consolidation_acts(act: ActProcessedDTO):
    """
    Renderuje dialog z tekstami jednolitymi dla aktu.

    :param act: Obiekt DTO z danymi aktu prawnego
    """
    st.header(f"{act.title}")
    with st.spinner("Wczytywanie dostępnych tekstów jednolitych..."):
        try:
            consolidation_acts = get_state().acts_service.get_consolidation_acts(act.id)
            if not consolidation_acts:
                st.info("Nie znaleziono żadnych tekstów jednolitych.")
            else:
                st.write(f"Znaleziono {len(consolidation_acts)} tekstów jednolitych.")
            for cons_act in consolidation_acts:
                with st.container(border=True):
                    st.markdown(f"**{cons_act.title}**")
                    st.caption(f"{cons_act.publisher} {cons_act.year} poz. {cons_act.position} | "
                               f"{cons_act.status}")

                    # Przyciski akcji – zależnie od tego, czy akt jest zapisany w DB
                    if cons_act.is_processed:
                        archive_button = st.button(
                            "Archiwizuj",
                            key=f"cons_archive_{cons_act.id}",
                            icon=":material/archive:",
                        )
                        if archive_button:
                            if get_state().acts_service.archive_act(cons_act.id):
                                st.success(f"Akt '{cons_act.title}' został zarchiwizowany.")
                            else:
                                st.error("Nie udało się zarchiwizować aktu.")
                    else:
                        # Akt niezapisany w DB
                        observe_button = st.button(
                            "Obserwuj",
                            key=f"cons_observe_{cons_act.publisher}_{cons_act.year}_{cons_act.position}",
                            icon=":material/add:"
                        )
                        if observe_button:
                            with st.spinner(f"Przetwarzanie aktu prawnego..."):
                                cons_act_with_references = get_state().acts_service.get_by_identifier(
                                    cons_act.publisher, cons_act.year, cons_act.position
                                )
                                processed_act = get_state().acts_service.process_act(cons_act_with_references)
                            if processed_act:
                                st.success(f"{processed_act.title} został dodany do listy obserwowanych.")
                            else:
                                st.error("Nie udało się dodać aktu prawnego.")
        except Exception as e:
            st.error(f"Wystąpił błąd podczas pobierania tekstów jednolitych: {str(e)}")


st.header("Obserwowane akty prawne")

# Pobierz wszystkie akty
basic_acts = get_state().acts_service.get_all_base()

# Stwórz listę dostępnych lat
years = sorted(set(str(act.year) for act in basic_acts))
years.insert(0, "Wszystkie")

if not basic_acts:
    st.info("Nie obserwujesz jeszcze żadnych aktów prawnych.")
else:
    # Kontrolki filtrów
    with st.container():
        col_year, col_search = st.columns([1, 3])

        with col_year:
            selected_year = st.selectbox("Rok", options=years)

        with col_search:
            title_search = st.text_input(
                "Tytuł"
            )

    show_flagged = st.checkbox(
        "Uwzględnij nieistotne",
        value=False,
        help="""
        Domyślnie ukryte zostały akty prawne, które zostały oznaczone
        jako nieistotne (np. akty indywidualno-konkretne).
        """
    )

    filtered_acts = basic_acts.copy()
    if not show_flagged:
        filtered_acts = [act for act in filtered_acts if not act.flag]
    if selected_year != "Wszystkie":
        year_int = int(selected_year)
        filtered_acts = [act for act in filtered_acts if act.year == year_int]
    if title_search:
        filtered_acts = [
            act for act in filtered_acts
            if title_search.lower() in act.title.lower()
        ]
    if not filtered_acts:
        st.info("Nie znaleziono aktów prawnych, które spełniają kryteria wyszukiwania. "
                "Spróbuj je zmienić, aby wyświetlić dostępne akty prawne.")

    st.write(f"Znaleziono {len(filtered_acts)} aktów prawnych.")

    cols = st.columns(2)
    for i, act in enumerate(filtered_acts):
        with cols[i % 2]:
            render_act_card(act)
