from typing import Optional

from pydantic import Field, AliasChoices

from src.domain.models.base import Base, ChunkBase


class Doc(Base):
    """
    Model reprezentujący dokument prawny.

    :param title: Tytuł dokumentu
    :param summary: Podsumowanie dokumentu (generowane przez LLM)
    :param flag: Flaga oznaczająca specjalne cechy dokumentu
    :param archived: Czy dokument jest zarchiwizowany
    """
    title: str
    summary: Optional[str] = None
    flag: Optional[bool] = None
    archived: Optional[bool] = False


class DocChunk(ChunkBase):
    """
    Model reprezentujący fragment dokumentu prawnego.

    :param reference_id: ID dokumentu, do którego należy fragment
    """
    reference_id: int = Field(validation_alias=AliasChoices('doc_id', 'reference_id'))
