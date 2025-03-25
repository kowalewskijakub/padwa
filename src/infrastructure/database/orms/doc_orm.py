from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import Field

from src.infrastructure.database.orms.base_orm import Base, ChunkBase


class Doc(Base, table=True):
    """
    Dokument prawny w bazie danych.
    """
    title: str

    # Pola generowane w wyniku przetworzenia
    summary: Optional[str] = None
    flag: Optional[bool] = None
    archived: Optional[bool] = None


class DocChunk(ChunkBase, table=True):
    """
    Fragment dokumentu prawnego (chunk) w bazie danych.
    """
    reference_id: int = Field(
        sa_column=Column("doc_id", Integer, ForeignKey("doc.id"))
    )
