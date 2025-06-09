"""Moduł modeli ORM dla dokumentów.

Zawiera modele dla dokumentów prawnych oraz ich fragmentów
w bazie danych.
"""

from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import Field

from src.infrastructure.database.orms.base_orm import Base, ChunkBase


class Doc(Base, table=True):
    """Dokument prawny w bazie danych.
    
    :param title: Tytuł dokumentu
    :param summary: Podsumowanie dokumentu (generowane przez LLM)
    :param flag: Flaga specjalna dokumentu
    :param archived: Czy dokument jest zarchiwizowany
    """
    title: str

    summary: Optional[str] = None
    flag: Optional[bool] = None
    archived: Optional[bool] = None


class DocChunk(ChunkBase, table=True):
    """Fragment dokumentu prawnego (chunk) w bazie danych.
    
    :param reference_id: Identyfikator dokumentu (mapowany jako doc_id)
    """
    reference_id: int = Field(
        sa_column=Column("doc_id", Integer, ForeignKey("doc.id"))
    )
