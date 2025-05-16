from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    pass


class LLMSummaryResponse(LLMResponse):
    pass


class ImpactAssessmentResponse(LLMResponse):
    """
    Model odpowiedzi zgodny z klasą LLMHandler służący realizacji funkcjonalności oceny istotności zmian.
    """
    relevancy: float = Field(description="Ocena istotności")
    justification: str = Field(description="Uzasadnienie")


class ActSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania aktu prawnego.

    Zawiera podsumowanie dostarczonego aktu prawnego oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    summary: str = Field(description="Podsumowanie")
    flag: bool = Field(description="Flaga")


class DocSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania dokumentu.

    Zawiera podsumowanie dostarczonego dokumentu oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    title: str = Field(description="Tytuł")
    summary: str = Field(description="Podsumowanie")
    flag: bool = Field(description="Flaga")


class ClusterSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania klastra chunków.

    Zawiera podsumowanie dostarczonych przepisów oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    summary: str = Field(description="Podsumowanie")
    flag: bool = Field(description="Flaga")


class ActClusterSummaryResponse(ClusterSummaryResponse):
    pass
