# wersja: chet-theia
from dataclasses import field
from typing import Dict

from src.application.dtos.base_dto import BaseDTO


class StatisticsDTO(BaseDTO):
    """
    Klasa bazowa DTO statystyk.
    Zawiera pola wspólne dla wszystkich DTO statystyk.
    """


class RelevancyStatisticsDTO(StatisticsDTO):
    """
    Model reprezentujący statystyki relewancji dokumentów.

    :param average: Średnia ocena relewancji
    :param minimum: Minimalna ocena relewancji
    :param maximum: Maksymalna ocena relewancji
    """
    average: float
    minimum: float
    maximum: float


class ActStatisticsDTO(StatisticsDTO):
    """
    Model reprezentujący statystyki aktów prawnych.

    :param total_acts: Całkowita liczba aktów
    :param total_chunks: Całkowita liczba fragmentów
    :param avg_chunks_per_act: Średnia liczba fragmentów na akt
    :param by_year: Słownik liczby aktów według roku
    """
    total_acts: int
    total_acts_by_year: Dict[int, int] = field(default_factory=dict)
    total_chunks: int
    avg_chunks_per_act: float


class DocumentStatisticsDTO(StatisticsDTO):
    """
    Model reprezentujący statystyki dokumentów.

    :param total_documents: Całkowita liczba dokumentów
    :param total_chunks: Całkowita liczba fragmentów
    :param avg_chunks_per_document: Średnia liczba fragmentów na dokument
    :param meta_text: Wszystkie teksty w tytułach dokumentów
    """
    total_documents: int
    total_chunks: int
    avg_chunks_per_document: float
    meta_text: str
