"""
Moduł DTO dla dokumentów.

Zawiera klasy Data Transfer Object używane do transferu
danych o dokumentach prawnych między warstwami aplikacji.
"""

from typing import Optional, List

from pydantic import ConfigDict, Field, AliasChoices

from src.core.dtos.base_dto import BaseDTO


class DocChunkDTO(BaseDTO):
    """
    DTO reprezentujące fragment dokumentu.

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
    
    Zawiera pola wspólne dla wszystkich DTO dokumentów.
    
    :param title: Tytuł dokumentu
    """
    model_config = ConfigDict(from_attributes=True)
    title: str


class DocProcessedDTO(DocDTO):
    """
    DTO dokumentu po zapisaniu w bazie danych.

    :param id: Identyfikator dokumentu
    :param summary: Podsumowanie dokumentu (generowane przez LLM)
    :param flag: Flaga oznaczająca specjalne cechy dokumentu
    """
    id: int
    summary: Optional[str] = None
    flag: Optional[bool] = False
