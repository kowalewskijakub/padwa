from typing import Optional

from domain.models.base import Base, ChunkBase
from pydantic import Field, AliasChoices


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
