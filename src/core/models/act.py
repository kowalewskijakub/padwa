from typing import Optional

from pydantic import Field, AliasChoices
from regex import regex

from src.core.models.base import Base, ChunkBase, ChunkClusterBase


class Act(Base):
    publisher: str
    year: int
    position: int
    title: str
    type: str
    status: str
    summary: Optional[str] = None
    flag: Optional[bool] = None
    archived: Optional[bool] = False

    @property
    def is_base(self) -> bool:
        """
        Sprawdza, czy zadany akt prawny jest ustawą, która nie jest ustawą zmieniającą.

        :return: True, jeśli akt jest ustawą, która nie jest ustawą zmieniającą, w przeciwnym wypadku False
        """
        pattern = r"^Ustawa(?:(?!zmianie).)*$"
        return bool(regex.match(pattern, self.title))

    @property
    def is_consolidation(self) -> bool:
        """
        Sprawdza, czy zadany akt prawny obwieszczeniem w sprawie ogłoszenia jednolitego tekstu ustawy.

        :return: True, jeśli akt jest konsolidacją, w przeciwnym wypadku False
        """
        pattern = r"^Obwieszczenie.*w sprawie ogłoszenia jednolitego tekstu ustawy"
        return bool(regex.match(pattern, self.title))


class ActChunk(ChunkBase):
    reference_id: int = Field(validation_alias=AliasChoices('act_id', 'reference_id'))


class ActChunkCluster(ChunkClusterBase):
    reference_id: int = Field(validation_alias=AliasChoices('act_id', 'reference_id'))


class ActChangeLink(Base):
    """
    Model reprezentujący relację zmiany między aktami prawnymi.

    :param changing_act_id: ID aktu zmieniającego
    :param changed_act_id: ID aktu zmienianego
    """
    changing_act_id: int
    changed_act_id: int


class ActChangeAnalysis(Base):
    """
    Model reprezentujący analizę zmian między fragmentami aktów prawnych.
    """
    changing_act_id: int
    changed_act_id: int
    changing_chunk_id: Optional[int] = None
    changed_chunk_id: Optional[int] = None
    change_type: str
    relevancy: Optional[float] = 0.0
    justification: Optional[str] = ""
    changing_chunk_text: Optional[str] = None
    changed_chunk_text: Optional[str] = None


class ActChangeImpactAnalysis(Base):
    """
    Model reprezentujący analizę wpływu zmiany w akcie prawnym na fragment dokumentu.
    """
    changing_act_id: int
    changed_act_id: int
    change_analysis_id: int
    doc_chunk_id: int
    relevancy: float
    justification: str
