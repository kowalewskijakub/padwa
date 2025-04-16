# wersja: chet-theia
from datetime import date
from typing import List, Optional, Dict, Tuple

from src.core.dtos.act_dto import ActApiDTO
from src.infrastructure.api.base_api_client import BaseApiClient


class ELIApiClient(BaseApiClient[ActApiDTO]):
    """
    Klient API dla European Legislation Identifier (ELI).

    Pozwala na pobieranie danych o aktach prawnych, ich wyszukiwanie,
    pobieranie tekstów jednolitych i treści w formacie PDF.
    """

    def _parse_references_by_categories(self, references: Dict, categories: List[str]) -> List[Tuple[str, int, int]]:
        """
        Parsuje referencje do aktów prawnych z podanych kategorii.

        :param references: Dane referencji
        :param categories: Lista nazw kategorii do przeszukania
        :return: Lista krotek (publisher, year, position)
        """
        result = []
        for category in categories:
            if category in references:
                for act_ref in references[category]:
                    if "id" in act_ref:
                        act_id = act_ref["id"]
                        parts = act_id.split("/")
                        if len(parts) == 3:
                            ref_publisher = parts[0]
                            ref_year = int(parts[1])
                            ref_position = int(parts[2])
                            result.append((ref_publisher, ref_year, ref_position))
        return result

    def _parse_changing_acts(self, references: Dict) -> List[Tuple[str, int, int]]:
        """
        Parsuje akty zmieniające z referencji.

        :param references: Dane referencji
        :return: Lista krotek (publisher, year, position)
        """
        changing_categories = [
            "Akty zmieniające",
            "Inf. o tekście jednolitym",
        ]

        return self._parse_references_by_categories(references, changing_categories)

    def _parse_changed_acts(self, references: Dict) -> List[Tuple[str, int, int]]:
        """
        Parsuje akty zmieniane z referencji.

        :param references: Dane referencji
        :return: Lista krotek (publisher, year, position)
        """
        changed_categories = [
            "Akty zmienione",
            "Tekst jednolity dla aktu",
        ]

        return self._parse_references_by_categories(references, changed_categories)

    def get_act_types(self) -> List[str]:
        """
        Pobiera dostępne typy aktów prawnych.

        :return: Lista typów
        """
        types = self._make_request("types").json()
        return types

    def get_act_statuses(self) -> List[str]:
        """
        Pobiera dostępne statusy aktów prawnych.

        :return: Lista statusów
        """
        statuses = self._make_request("statuses").json()
        return statuses

    def get_act(self, publisher: str, year: int, position: int) -> Optional[ActApiDTO]:
        """
        Pobiera informacje o konkretnym akcie wraz z referencjami.

        :param publisher: Kod wydawcy (np. 'DU')
        :param year: Rok publikacji
        :param position: Pozycja w publikacji
        :return: Obiekt ActApiDTO, jeśli znaleziono, None w przeciwnym razie
        """
        # Pobierz podstawowe dane aktu
        response = self._make_request(f"acts/{publisher}/{year}/{position}")
        act_data = response.json()

        # Przetwórz podstawowy obiekt ActApiDTO
        act_dto = ActApiDTO.model_validate(act_data)

        # Przetwórz referencje, jeśli są dostępne
        if "references" in act_data:
            references = act_data["references"]
            act_dto.changing_acts = self._parse_changing_acts(references)
            act_dto.changed_acts = self._parse_changed_acts(references)

        return act_dto

    def get_act_pdf(self, publisher: str, year: int, position: int) -> Optional[bytes]:
        """
        Pobiera zawartość PDF konkretnego aktu. Jeżeli istnieje tekst w wersji L to preferuje go ponad wynik
        zapytania do /text.pdf.

        :param publisher: Kod wydawcy (np. 'DU')
        :param year: Rok publikacji
        :param position: Pozycja w publikacji
        :return: Zawartość PDF jako bajty, jeśli znaleziono, None w przeciwnym razie
        """

        if publisher == "DU":
            position_filled = str(position).zfill(4)  # Pozycja wypełniona zerami do 4 cyfr
            l_text = self._make_request(f"acts/{publisher}/{year}/{position}/text/T/D{year}{position_filled}L.pdf")
            if l_text.status_code == 200:
                return l_text.content

        response = self._make_request(f"acts/{publisher}/{year}/{position}/text.pdf")
        return response.content

    def get_consolidation_acts(
            self,
            publisher: str,
            year: int,
            position: int,
            min_date: Optional[date] = None
    ) -> List[ActApiDTO]:
        """
        Pobiera listę tekstów jednolitych dla danego aktu.

        :param publisher: Kod wydawcy (np. 'DU')
        :param year: Rok publikacji
        :param position: Pozycja w publikacji
        :param min_date: Opcjonalna minimalna data zmian
        :return: Lista obiektów ActApiDTO reprezentujących akty skonsolidowane
        """
        response = self._make_request(f"acts/{publisher}/{year}/{position}/references")
        references = response.json()

        consolidation_acts = []

        if "Inf. o tekście jednolitym" in references:
            for item in references["Inf. o tekście jednolitym"]:
                act_data = item.get("act", {})

                # Filtruj według daty, jeśli została ona określona
                if min_date and item.get("date") and date.fromisoformat(item.get("date")) < min_date:
                    continue

                consolidation_acts.append(ActApiDTO.model_validate(act_data))

        return consolidation_acts

    def get_acts_by_title(self, query: str, limit: int = 200) -> List[ActApiDTO]:
        """
        Wyszukuje akty prawne na podstawie zapytania tekstowego.

        :param query: Tekst wyszukiwania (fragment tytułu)
        :param limit: Maksymalna liczba zwracanych wyników
        :return: Lista obiektów ActApiDTO reprezentujących znalezione akty
        :raises APIError: Gdy żądanie wyszukiwania nie powiedzie się
        """
        response = self._make_request(
            "acts/search",
            params={"title": query, "limit": limit}
        )
        acts_data = response.json().get('items', [])

        acts = []
        for act_data in acts_data:
            act = ActApiDTO.model_validate(act_data)
            # Przetwórz referencje, jeśli są dostępne
            if "references" in act_data:
                references = act_data["references"]
                act.changing_acts = self._parse_changing_acts(references)
                act.changed_acts = self._parse_changed_acts(references)
            acts.append(act)

        return acts
