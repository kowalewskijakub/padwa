# wersja: chet-theia
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from src.application.services.acts_service import ActsService
from src.application.services.dictionaries_service import DictionariesService
from src.application.services.docs_service import DocsService
from src.application.services.statistics_service import StatisticsService
from src.common.exceptions import ApplicationError
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


def get_state() -> AppState:
    """
    Pobiera stan aplikacji z session_state Streamlit.

    :return: Obiekt AppState
    """
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()

    return st.session_state.app_state


def initialize_state() -> bool:
    """
    Inicjalizuje stan aplikacji.

    :return: True, jeśli udało się zainicjalizować serwisy, False w przeciwnym razie
    """
    state = get_state()

    if state.initialized:
        return True

    try:
        state.acts_service = container.acts_service()
        state.docs_service = container.docs_service()
        state.statistics_service = container.statistics_service()
        state.dictionaries_service = container.dictionaries_service()

        # Inicjalizacja bazy danych
        # db_manager = container.db_manager()
        # db_manager.initialize_database()

        state.initialized = True
        return True
    except Exception as e:
        raise ApplicationError(f"Stan aplikacji nie został zainicjalizowany: {str(e)}")
