"""
Moduł konfiguracji aplikacji.

Zawiera klasę AppConfig odpowiedzialną za wczytywanie i przechowywanie
parametrów konfiguracyjnych aplikacji z pliku JSON.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """
    Klasa konfiguracyjna aplikacji zawierająca wszystkie stałe systemowe.

    Przechowuje parametry konfiguracyjne wczytywane z pliku JSON, takie jak
    informacje o aplikacji, ustawienia API i modeli AI.
    """
    copyright_author: str
    copyright_year: str
    app_name: str
    app_acronym: str
    app_version: str
    eli_api_base_url: str
    llm_model: str
    embedding_model: str
    embedding_vector_size: int

    @classmethod
    def load(cls, constants_path: str = None) -> Optional['AppConfig']:
        """
        Wczytuje konfigurację aplikacji z pliku JSON.

        Jeśli ścieżka nie zostanie podana, automatycznie wyszukuje plik
        app_constants.json w katalogu assets względem katalogu głównego projektu.

        :param constants_path: Ścieżka do pliku JSON z konfiguracją aplikacji
        :return: Obiekt AppConfig z wczytaną konfiguracją lub None w przypadku błędu
        :raises FileNotFoundError: Gdy plik konfiguracyjny nie istnieje
        :raises json.JSONDecodeError: Gdy plik JSON ma nieprawidłową składnię
        """
        if constants_path is None:
            project_root = Path(__file__).parent.parent.parent
            constants_path = project_root / "assets" / "app_constants.json"
        try:
            with open(constants_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        except Exception as e:
            print(f"Nie udało się wczytać stałych z '{constants_path}': {e}")
            return None
