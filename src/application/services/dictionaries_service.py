# wersja: chet-theia
from src.infrastructure.api.eli_api_client import ELIApiClient
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActType, ActStatus


class DictionariesService:
    """
    Serwis do zarządzania słownikami w aplikacji.
    """

    def __init__(self, db_manager: DatabaseManager, api_client: ELIApiClient):
        """
        Inicjalizuje serwis słowników.

        :param db_manager: Menedżer bazy danych
        :param api_client: Klient API ELI
        """
        self.db_manager = db_manager
        self.api_client = api_client

    def sync_dictionaries(self):
        """
        Synchronizuje słowniki z API z bazą danych.

        :return: Słownik z liczbą dodanych wpisów dla każdej tabeli
        """
        # Pobierz typy i statusy z API
        types = self.api_client.get_act_types()
        statuses = self.api_client.get_act_statuses()

        # Aktualizuj tabele słownikowe
        return self.db_manager.update_dictionaries({
            ActType: types,
            ActStatus: statuses
        })
