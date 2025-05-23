# wersja: chet-theia
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
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
    def load(cls, constants_path: str = "assets/app_constants.json") -> Optional['AppConfig']:
        """
        Wczytuje stałe z pliku JSON.

        :param constants_path: Ścieżka do pliku JSON z danymi stałych
        :return: Obiekt AppConstants
        """
        try:
            with open(constants_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        except Exception as e:
            print(f"Nie udało się wczytać stałych: {e}")
            return None
