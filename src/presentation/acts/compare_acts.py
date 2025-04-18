from typing import List

import pandas as pd
import streamlit as st

from src.core.dtos.act_dto import ActChangeAnalysisDTO
from src.presentation.app_state import get_state

change_type_map = {
    "modified": "zmiana",
    "appended": "dodanie",
    "removed": "usunięcie"
}


def render_act_comparison():
    """
    Renderuje interfejs do porównywania aktów prawnych.

    Umożliwia wybór aktu bazowego i zmieniającego, a następnie ich porównanie.
    Po wykonaniu porównania wyświetla wyniki w ramce danych i umożliwia analizę wpływu na dokumenty.
    """
    all_acts = get_state().acts_service.get_all()
    if not all_acts:
        st.info("Brak dostępnych aktów prawnych, które można porównać.")
        return

    col_base, col_changing = st.columns(2)
    with col_base:
        base_act_options = {
            f"{act.title} ({act.publisher} {act.year} poz. {act.position})": act.id for act in all_acts
        }
        base_act_selection = st.selectbox("Wersja wcześniejsza", options=["Wybierz..."] + list(base_act_options.keys()))
        base_act_id = base_act_options.get(base_act_selection) if base_act_selection != "Wybierz..." else None

        changing_options = {}
        if base_act_id:
            changing_acts = get_state().acts_service.get_referenced_acts(base_act_id)
            changing_options = {
                f"{act.title} ({act.publisher} {act.year} poz. {act.position})": act.id for act in changing_acts
            }

    with col_changing:
        changing_act_selection = st.selectbox("Wersja późniejsza", options=["Wybierz..."] + list(changing_options.keys()))
        changing_act_id = (
            changing_options.get(changing_act_selection) if changing_act_selection != "Wybierz..." else None
        )

    both_selected = base_act_id is not None and changing_act_id is not None
    selected_pair = (base_act_id, changing_act_id)

    if 'current_pair' not in st.session_state or st.session_state['current_pair'] != selected_pair:
        st.session_state['differences'] = None
        st.session_state['impact_analyses'] = None
        st.session_state['current_pair'] = selected_pair

    if st.button("Porównaj", disabled=not both_selected, type="primary", icon=":material/compare_arrows:"):
        with st.spinner("Analizowanie różnic..."):
            differences = get_state().act_comparisons_service.compare_acts(changing_act_id, base_act_id)
            st.session_state['differences'] = differences

    if 'differences' in st.session_state and st.session_state['differences']:
        st.subheader("Porównanie zmian")
        render_differences(st.session_state['differences'])

        st.info("Kliknij poniższy przycisk, aby przeanalizować wpływ tych zmian na dokumenty organizacyjne.")
        if st.button("Analizuj wpływ na dokumenty"):
            with st.spinner("Analizowanie wpływu..."):
                impact_analyses = get_state().act_change_impact_service.analyze_impact(changing_act_id, base_act_id)
                st.session_state['impact_analyses'] = impact_analyses


def render_differences(differences: List[ActChangeAnalysisDTO]):
    """
    Wyświetla wyniki porównania w ramce danych.

    :param differences: Lista obiektów ActChangeAnalysisDTO reprezentujących różnice
    """
    df = pd.DataFrame([
        {
            "Rodzaj zmiany": change_type_map.get(diff.change_type, diff.change_type),
            "Wersja wcześniejsza": diff.changed_chunk_text or "",
            "Wersja późniejsza": diff.changing_chunk_text or "",
        }
        for diff in differences
    ])
    st.dataframe(df)


st.header("Porównanie zmian w aktach prawnych")
st.markdown("""
    Wybierz dwie wersje danego aktu prawnego, aby porównać ich zmiany.
    Możesz również przeanalizować wpływ tych zmian na zapisaną dokumentację.
    """)
render_act_comparison()
