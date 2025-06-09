"""
Moduł DTO dla aktów prawnych.

Zawiera klasy Data Transfer Object używane do transferu
danych o aktach prawnych między warstwami aplikacji.
"""

from typing import Optional, Dict, Any, List, Tuple

from pydantic import ConfigDict, Field, AliasChoices

from src.core.dtos.base_dto import BaseDTO


class ActChunkDTO(BaseDTO):
    """
    DTO reprezentujące fragment aktu prawnego.
    
    :param id: Identyfikator fragmentu
    :param act_id: Identyfikator aktu prawnego
    :param text: Treść fragmentu
    :param embedding: Wektor embeddingu fragmentu (opcjonalny)
    """
    id: int
    act_id: int = Field(validation_alias=AliasChoices('reference_id', 'act_id'))
    text: str
    embedding: Optional[List[float]] = None


class ActDTO(BaseDTO):
    """
    Klasa bazowa DTO aktu prawnego.
    
    Zawiera pola wspólne dla wszystkich DTO aktów prawnych.
    
    :param publisher: Kod wydawcy (np. 'DU')
    :param year: Rok publikacji
    :param position: Pozycja w publikacji
    :param title: Tytuł aktu
    :param references: Opcjonalne referencje do innych aktów
    """
    model_config = ConfigDict(from_attributes=True)
    publisher: str
    year: int
    position: int = Field(validation_alias=AliasChoices('position', 'pos'))
    title: str
    references: Optional[Dict[str, Any]] = None


class ActApiDTO(ActDTO):
    """
    DTO aktu prawnego z informacjami z ELI API.
    
    Przechowuje podstawowe informacje o akcie prawnym zwracane przez ELI API.
    
    :param type: Typ aktu prawnego
    :param status: Status aktu prawnego
    :param changing_acts: Lista aktów zmieniających ten akt
    :param changed_acts: Lista aktów zmienianych przez ten akt
    """
    type: str
    status: str

    changing_acts: Optional[List[Tuple[str, int, int]]] = None
    changed_acts: Optional[List[Tuple[str, int, int]]] = None


class ConsolidationActDTO(ActApiDTO):
    """
    DTO tekstu jednolitego aktu prawnego.
    
    Reprezentuje tekst jednolity aktu prawnego wraz z informacją o jego ID
    jeżeli został już zapisany w bazie danych.

    :param id: ID aktu w bazie danych, jeśli jest przetworzony
    """
    id: Optional[int] = None

    @property
    def is_processed(self) -> bool:
        return self.id is not None


class ActProcessedDTO(ActDTO):
    """
    DTO aktu prawnego po zapisaniu w bazie danych.
    
    Przechowuje dane aktu prawnego wraz z dodatkowymi polami
    wygenerowanymi po przetworzeniu i zapisaniu w bazie danych.
    
    :param id: Identyfikator aktu w bazie danych
    :param summary: Podsumowanie aktu (generowane przez LLM)
    :param flag: Flaga specjalna aktu
    :param status: Status aktu
    """
    id: int
    summary: Optional[str] = None
    flag: Optional[bool] = False
    status: Optional[str] = None


class ActChangeImpactAnalysisDTO(BaseDTO):
    """
    DTO analizy wpływu zmiany w akcie prawnym na dokument.

    :param id: Identyfikator analizy wpływu
    :param change_analysis_id: ID analizy zmiany (FK do ActChangeAnalysis)
    :param doc_chunk_id: ID fragmentu dokumentu
    :param relevancy: Wynik podobieństwa semantycznego
    :param justification: Uzasadnienie oceny wpływu
    :param doc_chunk_text: Tekst fragmentu dokumentu
    """
    id: Optional[int] = None
    change_analysis_id: int
    doc_chunk_id: int
    relevancy: float
    justification: str
    doc_chunk_text: str


class ActChangeAnalysisDTO(BaseDTO):
    """
    DTO analizy zmian między fragmentami aktów prawnych.
    
    :param id: Identyfikator analizy
    :param changing_act_id: ID aktu zmieniającego
    :param changed_act_id: ID aktu zmienianego
    :param changing_chunk_id: ID fragmentu aktu zmieniającego
    :param changed_chunk_id: ID fragmentu aktu zmienianego
    :param change_type: Typ zmiany
    :param relevancy: Ocena relewatnoci
    :param justification: Uzasadnienie oceny
    :param changing_chunk_text: Tekst fragmentu zmieniającego
    :param changed_chunk_text: Tekst fragmentu zmienianego
    :param impacts: Lista analiz wpływu na dokumenty
    """
    id: Optional[int] = None
    changing_act_id: int
    changed_act_id: int
    changing_chunk_id: Optional[int] = None
    changed_chunk_id: Optional[int] = None
    change_type: str
    relevancy: float
    justification: str
    changing_chunk_text: Optional[str] = None
    changed_chunk_text: Optional[str] = None
    impacts: Optional[List[ActChangeImpactAnalysisDTO]] = None
