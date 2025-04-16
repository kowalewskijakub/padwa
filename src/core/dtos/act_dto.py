# wersja: chet-theia
from typing import Optional, Dict, Any, List, Tuple

from pydantic import ConfigDict, Field, AliasChoices

from src.core.dtos.base_dto import BaseDTO


class ActChunkDTO(BaseDTO):
    id: int
    act_id: int = Field(validation_alias=AliasChoices('reference_id', 'act_id'))
    text: str
    embedding: Optional[List[float]] = None


class ActDTO(BaseDTO):
    """
    Klasa bazowa DTO aktu prawnego.
    Zawiera pola wspólne dla wszystkich DTO.
    """
    model_config = ConfigDict(from_attributes=True)
    publisher: str
    year: int
    position: int = Field(validation_alias=AliasChoices('position', 'pos'))
    title: str
    references: Optional[Dict[str, Any]] = None


class ActApiDTO(ActDTO):
    """
    Klasa DTO aktu prawnego, która przechowuje podstawowe informacje zwracane przez ELI API.
    """
    type: str
    status: str

    changing_acts: Optional[List[Tuple[str, int, int]]] = None
    changed_acts: Optional[List[Tuple[str, int, int]]] = None


class ConsolidationActDTO(ActApiDTO):
    """
    DTO reprezentujący tekst jednolity aktu prawnego wraz z informacją o jego ID (jeżeli został już
    zapisany w DB).

    :param is_processed: Czy akt jest już przetworzony i znajduje się w bazie danych
    :param id: ID aktu w bazie danych, jeśli jest przetworzony
    """
    id: Optional[int] = None

    @property
    def is_processed(self) -> bool:
        return self.id is not None


class ActProcessedDTO(ActDTO):
    """
    Klasa DTO aktu prawnego, która przechowuje dane uzyskiwane po zapisaniu w bazie danych.
    """
    id: int
    summary: Optional[str] = None
    flag: Optional[bool] = False
    status: Optional[str] = None


class ActChangeImpactAnalysisDTO(BaseDTO):
    """
    DTO reprezentujące wyniki analizy wpływu zmiany w akcie prawnym na fragment dokumentu.

    :param id: Identyfikator analizy wpływu
    :param change_analysis_id: ID analizy zmiany (FK do ActChangeAnalysis)
    :param doc_chunk_id: ID fragmentu dokumentu
    :param relevancy Wynik podobieństwa semantycznego
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
    DTO reprezentujące wyniki analizy zmian między fragmentami aktów prawnych.
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
