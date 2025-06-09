"""
Główny moduł aplikacji Streamlit do zarządzania aktami prawnymi i dokumentacją.

Ten moduł zawiera główną logikę aplikacji webowej, konfigurację stron
oraz renderowanie strony głównej z podstawowymi statystykami.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
from wordcloud import WordCloud

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.core.dtos.statistics_dto import ActStatisticsDTO, DocumentStatisticsDTO
from src.presentation.app_config import AppConfig
from src.presentation.app_state import initialize_state, get_state

_config = AppConfig.load()


def render_home_page(act_statistics: ActStatisticsDTO, doc_statistics: DocumentStatisticsDTO):
    """
    Wyświetla stronę główną ze statystykami aktów prawnych i dokumentów.

    Renderuje dashboard z metrykami podstawowymi oraz wykresami przedstawiającymi
    rozkład aktów prawnych według roku i chmurę słów z dokumentacji wewnętrznej.

    :param act_statistics: Obiekt DTO zawierający statystyki aktów prawnych
    :param doc_statistics: Obiekt DTO zawierający statystyki dokumentów
    """
    st.markdown(
        f"""
        ## {_config.app_acronym}
        ##### {_config.app_name}
        """
    )

    if act_statistics.total_acts > 0:

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            st.metric(
                "Akty prawne",
                act_statistics.total_acts
            )
        with col2:
            st.metric(
                "Dokumenty",
                doc_statistics.total_documents
            )

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.subheader("Akty prawne")
                st.markdown(f"**Średnia wielkość:**\t{act_statistics.avg_chunks_per_act} fragmentów")

                if act_statistics.total_acts_by_year:
                    years = list(act_statistics.total_acts_by_year.keys())
                    counts = list(act_statistics.total_acts_by_year.values())

                    fig = px.bar(
                        x=years,
                        y=counts,
                        labels={'x': 'Rok', 'y': 'Liczba aktów prawnych'},
                        title="Akty prawne według roku"
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with col2:
            if doc_statistics.total_documents > 0:
                with st.container(border=True):
                    st.subheader("Dokumentacja wewnętrzna")
                    st.markdown(f"**Średnia wielkość:**\t{doc_statistics.avg_chunks_per_document} fragmentów")
                    wordcloud = WordCloud(
                        width=800,
                        height=400,
                        background_color='white',
                        colormap='PuBu',
                        max_words=100
                    ).generate(doc_statistics.meta_text)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wordcloud)
                    ax.axis('off')
                    st.pyplot(fig)


st.set_page_config(
    page_title=_config.app_acronym,
    page_icon=":material/policy:",
    layout="wide"
)

initialized = initialize_state()
if initialized:

    get_state().dictionaries_service.sync_dictionaries()

    st.html('<style>' + open('assets/styles.css').read() + '</style>')

    act_statistics = get_state().statistics_service.get_act_statistics()
    doc_statistics = get_state().statistics_service.get_doc_statistics()

    pages = {
        "": [
            st.Page(lambda: render_home_page(act_statistics, doc_statistics),
                    title="Strona główna", icon=":material/home:"
                    ),
        ],
        "Akty prawne": [
            st.Page("acts/search_acts.py", title="Wyszukaj", icon=":material/search:"),
            st.Page("acts/browse_acts.py", title="Obserwowane", icon=":material/folder:"),
            st.Page("acts/compare_acts.py", title="Porównaj", icon=":material/compare_arrows:"),
            st.Page("acts/assess_impact_acts.py", title="Analizuj", icon=":material/analytics:")
        ],
        "Dokumentacja": [
            st.Page("docs/add_docs.py", title="Dodaj", icon=":material/add:"),
            st.Page("docs/browse_docs.py", title="Obserwowane", icon=":material/folder:")
        ]
    }

    sidebar = st.navigation(pages)
    sidebar.run()
else:
    st.error("Platforma jest tymczasowo niedostępna. Proszę spróbować ponownie później.")

st.caption(
    f"""
    {_config.app_name} ({_config.app_acronym}) v. {_config.app_version} –
    © {_config.copyright_year} {_config.copyright_author}
    """)
