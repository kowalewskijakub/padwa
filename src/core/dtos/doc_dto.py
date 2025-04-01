from typing import Optional, List

from pydantic import ConfigDict, Field, AliasChoices

from src.core.dtos.base_dto import BaseDTO


class DocChunkDTO(BaseDTO):
    """
    Model DTO reprezentujący fragment dokumentu.

    :param id: Identyfikator fragmentu
    :param doc_id: Identyfikator dokumentu, do którego należy fragment
    :param text: Treść fragmentu
    :param embedding: Wektor embeddingu fragmentu (opcjonalny)
    """
    id: int
    doc_id: int = Field(validation_alias=AliasChoices('reference_id', 'doc_id'))
    text: str
    embedding: Optional[List[float]] = None


class DocDTO(BaseDTO):
    """
    Klasa bazowa DTO dokumentu.
    Zawiera pola wspólne dla wszystkich DTO.
    """
    model_config = ConfigDict(from_attributes=True)
    title: str


class DocProcessedDTO(DocDTO):
    """
    Klasa DTO dokumentu, która przechowuje dane uzyskiwane po zapisaniu w bazie danych.

    :param id: Identyfikator dokumentu
    :param summary: Podsumowanie dokumentu (generowane przez LLM)
    :param flag: Flaga oznaczająca specjalne cechy dokumentu
    """
    id: int
    summary: Optional[str] = None
    flag: Optional[bool] = False
