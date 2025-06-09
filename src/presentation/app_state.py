"""
Moduł zarządzania stanem aplikacji.

Zawiera klasę AppState oraz funkcje do inicjalizacji i pobierania stanu
aplikacji w ramach sesji Streamlit. Zarządza serwisami domenowymi
dostępnymi dla warstwy prezentacji.
"""
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from src.common.exceptions import ApplicationError
from src.core.services.act_change_impact_service import ActChangeImpactService
from src.core.services.act_comparisons_service import ActComparisonsService
from src.core.services.acts_service import ActsService
from src.core.services.dictionaries_service import DictionariesService
from src.core.services.docs_service import DocsService
from src.core.services.statistics_service import StatisticsService
from src.infrastructure.di import container


@dataclass
class AppState:
    """
    Stan aplikacji przechowujący serwisy dostępne dla warstwy prezentacji.

    Klasa udostępnia tylko serwisy aplikacyjne, ukrywając szczegóły implementacyjne
    takie jak repozytoria, handlery itp.
    """
    initialized: bool = False

    # Serwisy domenowe dostępne dla warstwy prezentacji
    acts_service: Optional[ActsService] = None
    docs_service: Optional[DocsService] = None
    statistics_service: Optional[StatisticsService] = None
    dictionaries_service: Optional[DictionariesService] = None
    act_comparisons_service: Optional[ActComparisonsService] = None
    act_change_impact_service: Optional[ActChangeImpactService] = None


def get_state() -> AppState:
    """
    Pobiera stan aplikacji z session_state Streamlit.

    Jeśli stan nie istnieje w session_state, tworzy nowy pusty obiekt AppState.

    :return: Obiekt AppState zawierający stan aplikacji
    """
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()

    return st.session_state.app_state


def initialize_state() -> bool:
    """
    Inicjalizuje stan aplikacji wraz z wszystkimi serwisami domenowymi.

    Tworzy instancje serwisów za pomocą kontenera dependency injection
    oraz inicjalizuje bazę danych. Jeśli stan jest już zainicjalizowany,
    zwraca True bez ponownej inicjalizacji.

    :return: True, jeśli udało się zainicjalizować wszystkie serwisy
    :raises ApplicationError: Gdy inicjalizacja nie powiedzie się
    """
    state = get_state()

    if state.initialized:
        return True

    try:
        state.acts_service = container.acts_service()
        state.docs_service = container.docs_service()
        state.statistics_service = container.statistics_service()
        state.dictionaries_service = container.dictionaries_service()
        state.act_comparisons_service = container.act_comparisons_service()
        state.act_change_impact_service = container.act_change_impact_service()

        # Inicjalizacja bazy danych
        db_manager = container.db_manager()
        db_manager.initialize_database()

        state.initialized = True
        return True
    except Exception as e:
        raise ApplicationError(f"Stan aplikacji nie został zainicjalizowany: {str(e)}")
