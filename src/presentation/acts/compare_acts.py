import streamlit as st
from src.presentation.app_state import get_state


def render_act_comparison():
    """
    Renderuje interfejs porównywania aktów prawnych.
    """
    all_acts = get_state().acts_service.get_all()

    if not all_acts:
        st.info("Brak dostępnych aktów prawnych do porównania.")
        return

    base_act_options = {f"{act.title} ({act.publisher} {act.year} poz. {act.position})": act.id
                        for act in all_acts}
    base_act_selection = st.selectbox("Wybierz akt bazowy", options=list(base_act_options.keys()))
    base_act_id = base_act_options[base_act_selection] if base_act_selection else None

    changing_options = {}
    if base_act_id:
        changing_acts = get_state().acts_service.get_related_changing_acts(base_act_id)
        changing_options = {f"{act.title} ({act.publisher} {act.year} poz. {act.position})": act.id
                            for act in changing_acts}

    changing_act_selection = st.selectbox("Wybierz akt zmieniający",
                                          options=["Wybierz..."] + list(changing_options.keys()))
    changing_act_id = changing_options[changing_act_selection] if changing_act_selection != "Wybierz..." else None

    if st.button("Porównaj", disabled=not (base_act_id and changing_act_id)):
        with st.spinner("Analizowanie różnic..."):
            try:
                differences = get_state().act_comparisons_service.compare_acts(changing_act_id, base_act_id)

                if not differences:
                    st.info("Nie znaleziono różnic lub analiza nie została jeszcze wykonana.")
                    return

                st.subheader("Wyniki porównania")

                change_types = {"modified": "Zmodyfikowany", "appended": "Dodany", "removed": "Usunięty"}
                for change_type in change_types:
                    type_diffs = [d for d in differences if d.change_type == change_type]
                    if type_diffs:
                        st.markdown(f"### {change_types[change_type]} ({len(type_diffs)})")
                        for diff in type_diffs:
                            with st.expander(f"{change_types[change_type]} fragment"):
                                if change_type == "removed":
                                    st.markdown("**Usunięty tekst:**")
                                    st.text(diff.changed_chunk_text)
                                else:
                                    st.markdown("**Tekst w akcie zmieniającym:**")
                                    st.text(diff.changing_chunk_text or "Brak")
                                    if diff.changed_chunk_text:
                                        st.markdown("**Tekst w akcie zmienianym:**")
                                        st.text(diff.changed_chunk_text)
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Wystąpił błąd podczas porównywania: {str(e)}")

st.header("Porównaj wersje aktów prawnych")
st.markdown("""
Wybierz akt bazowy i akt zmieniający, aby zobaczyć różnice między nimi.
System pokaże, które fragmenty zostały zmodyfikowane, dodane lub usunięte.
""")
render_act_comparison()