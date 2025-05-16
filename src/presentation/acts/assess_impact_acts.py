from collections import defaultdict

import streamlit as st

from src.presentation.app_state import get_state

change_type_map = {
    "modified": "zmiana",
    "appended": "dodanie",
    "removed": "usunięcie"
}


def render_assess_impact_acts():
    """
    Renderuje interfejs do oceny wpływu zmian w aktach prawnych.
    """
    all_acts = get_state().acts_service.get_all()
    if not all_acts:
        st.info("Brak dostępnych aktów prawnych, które można analizować.")
        return

    col_base, col_changing = st.columns(2)
    with col_base:
        base_act_options = {
            f"{act.title} ({act.publisher} {act.year} poz. {act.position})": act.id for act in all_acts
        }
        base_act_selection = st.selectbox("Wersja wcześniejsza", options=["Wybierz..."] + list(base_act_options.keys()))
        base_act_id = base_act_options.get(base_act_selection) if base_act_selection != "Wybierz..." else None

    with col_changing:
        changing_act_options = {
            f"{act.title} ({act.publisher} {act.year} poz. {act.position})": act.id for act in all_acts
        }
        changing_act_selection = st.selectbox("Wersja późniejsza",
                                              options=["Wybierz..."] + list(changing_act_options.keys()))
        changing_act_id = changing_act_options.get(
            changing_act_selection) if changing_act_selection != "Wybierz..." else None

    both_selected = base_act_id is not None and changing_act_id is not None
    selected_pair = (base_act_id, changing_act_id)

    if 'current_impact_pair' not in st.session_state or st.session_state['current_impact_pair'] != selected_pair:
        st.session_state['impact_analyses'] = None
        st.session_state['current_impact_pair'] = selected_pair

    if st.button("Analizuj", disabled=not both_selected, type="primary", icon=":material/analytics:"):
        with st.spinner("Analizowanie wpływu..."):
            try:
                analyses = get_state().act_change_impact_service.analyze_impact(changing_act_id, base_act_id)
                st.session_state['impact_analyses'] = analyses
            except Exception as e:
                st.error(f"Błąd podczas analizy wpływu: {str(e)}")

    if 'impact_analyses' in st.session_state and st.session_state['impact_analyses']:
        render_impact_analyses(st.session_state['impact_analyses'])


def render_impact_analyses(analyses, min_relevancy=0):
    """
    Renderuje analizy wpływu zmian w aktach prawnych na fragmenty dokumentów.

    :param analyses: Lista analiz wpływu
    :param min_relevancy: Minimalna istotność fragmentu dokumentu do wyświetlenia
    """

    doc_impacts = defaultdict(list)
    for analysis in analyses:
        for impact in analysis.impacts:
            doc_impacts[impact.doc_chunk_id].append((impact, analysis))

    if not doc_impacts:
        st.write("Brak powiązanych fragmentów dokumentów.")
        return

    st.markdown(f"### Powiązane fragmenty dokumentów ({len(doc_impacts)})")

    # Sortuje fragmenty dokumentów według średniej istotności
    sorted_docs = sorted(
        doc_impacts.items(),
        key=lambda x: sum(impact.relevancy for impact, _ in x[1]) / len(x[1]),
        reverse=True
    )

    for doc_chunk_id, impact_analysis_pairs in sorted_docs:
        filtered_impacts = [(i, a) for i, a in impact_analysis_pairs if i.relevancy >= min_relevancy]
        if not filtered_impacts:
            continue

        filtered_impacts.sort(key=lambda x: x[0].relevancy, reverse=True)
        avg_relevancy = sum(i.relevancy for i, _ in filtered_impacts) / len(filtered_impacts)
        doc_name = f"Dokument (ID chunka: {doc_chunk_id})"

        with st.expander(f"{doc_name} - Średnia istotność: {avg_relevancy:.2f}", expanded=False):
            # Wyświetla tekst fragmentu dokumentu tylko 1 raz
            doc_chunk_text = filtered_impacts[0][0].doc_chunk_text
            st.markdown("**Fragment dokumentu:**")
            st.markdown(doc_chunk_text)
            st.markdown("---")

            for idx, (impact, analysis) in enumerate(filtered_impacts):
                st.markdown(f"#### Analiza {idx + 1}")
                metric_col, text_col = st.columns([1, 3])
                with metric_col:
                    st.metric(
                        label="Istotność",
                        value=f"{impact.relevancy:.2f}",
                        delta=None
                    )
                with text_col:
                    st.markdown(f"**Uzasadnienie:**\n{impact.justification}")

                st.markdown("**Szczegóły zmiany:**")
                st.markdown(f"*Rodzaj zmiany: {change_type_map.get(analysis.change_type, analysis.change_type)}*")
                if analysis.changing_chunk_text:
                    st.markdown(f"**Wersja późniejsza:**")
                    st.markdown(analysis.changing_chunk_text)
                if analysis.changed_chunk_text:
                    st.markdown(f"**Wersja wcześniejsza:**")
                    st.markdown(analysis.changed_chunk_text)

                if idx < len(filtered_impacts) - 1:
                    st.markdown("---")


st.header("Ocena wpływu zmian w aktach prawnych")
st.markdown("""
    Wybierz dwie wersje danego aktu prawnego, aby przeanalizować ich wpływ na dokumentację wewnętrzną.
    """)
render_assess_impact_acts()
