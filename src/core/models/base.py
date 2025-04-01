from typing import Optional, List, Any

from pydantic import BaseModel, ConfigDict, AliasChoices, Field

from src.infrastructure.processing.llm.llm_response_models import LLMSummaryResponse


class Base(BaseModel):
    """
    Klasa bazowa modelu.
    """
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None


class EmbeddableBase(Base):
    """
    Klasa reprezentująca tekst, który można przekształcić na embedding.
    Używana jako komponent w modelach wymagających semantycznego wyszukiwania
    i grupowania.
    """
    text: Optional[str]
    embedding: Any = None


class ChunkBase(EmbeddableBase):
    """
    Klasa bazowa modelu fragmentu tekstu (chunka).
    """
    reference_id: Optional[int] = None


class ChunkClusterBase(EmbeddableBase):
    """
    Klasa bazowa modelu klastra.
    """
    reference_id: Optional[int] = None
    parent_cluster_id: Optional[int] = None
    level: int = 0

    _llm_summary_response: Optional[LLMSummaryResponse] = None  # Pola prywatne są pomijane w BaseRepository.update()

    _chunks: Optional[List[ChunkBase]] = []

    text: Optional[str] = Field(
        validation_alias=AliasChoices('summary', 'text'),
        default=None
    )
    embedding: Optional[Any] = Field(
        validation_alias=AliasChoices('embedding', 'summary_embedding'),
        default=None
    )

    flag: Optional[bool] = None

    @property
    def chunks(self) -> List[ChunkBase]:
        return self._chunks

    @chunks.setter
    def chunks(self, value: List[ChunkBase]) -> None:
        self._chunks = value

    @property
    def llm_summary_response(self) -> Optional[LLMSummaryResponse]:
        return self._llm_summary_response

    @llm_summary_response.setter
    def llm_summary_response(self, value: LLMSummaryResponse) -> None:
        self._llm_summary_response = value
        if value is not None:
            summary = getattr(value, 'summary', None)
            flag = getattr(value, 'flag', None)
            if summary is not None:
                self.text = summary
            if flag is not None:
                self.flag = flag
