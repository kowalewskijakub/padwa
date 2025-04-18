# wersja: chet-theia
from abc import ABC
from typing import TypeVar, Generic, Dict, Any, Optional

import requests

from src.core.dtos.base_dto import BaseDTO

TBaseDTO = TypeVar('TBaseDTO', bound=BaseDTO)


class BaseApiClient(Generic[TBaseDTO], ABC):
    """
    Abstrakcyjna klasa bazowa dla klientów API.

    Dostarcza podstawowe metody i strukturę dla klientów API, które pobierają i przetwarzają
    dane z zewnętrznych źródeł poprzez HTTP.
    """

    def __init__(self, base_url: str):
        """
        Inicjalizuje klienta API.

        :param base_url: Bazowy URL dla obsługiwanego API
        """
        self.base_url = base_url
        self.session = requests.Session()

    def _make_request(
            self,
            endpoint: str,
            method: str = "GET",
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, Any]] = None,
            timeout: int = 30
    ) -> requests.Response:
        """
        Wykonuje żądanie do API.

        :param endpoint: Endpoint API do zapytania
        :param method: Metoda HTTP (GET, POST, PUT, DELETE)
        :param params: Parametry zapytania dla URL
        :param data: Dane do przesłania w ciele żądania
        :param headers: Nagłówki żądania HTTP
        :param timeout: Limit czasu oczekiwania na odpowiedź w sekundach
        :return: Odpowiedź API
        """
        url = f"{self.base_url}/{endpoint}"

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=data,
            headers=headers,
            timeout=timeout
        )
        return response
