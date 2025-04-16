# wersja: chet-theia
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    pass


class LLMSummaryResponse(LLMResponse):
    pass


class ImpactAssessmentResponse(LLMResponse):
    """
    Klasa odpowiedzi LLM dla oceny wpływu zmiany.
    """
    relevancy: float = Field(
        description="Ocena wpływu zmiany w akcie prawnym na fragment dokumentu."
    )
    justification: str = Field(
        description="Uzasadnienie oceny wpływu zmiany w akcie prawnym na fragment dokumentu."
    )


class ActSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania aktu prawnego.

    Zawiera podsumowanie dostarczonego aktu prawnego oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    summary: str = Field(
        description="Podsumowanie dostarczonego aktu prawnego, ok. 300 znaków."
    )
    flag: bool = Field(
        description=
        """
        True  – jeżeli dostarczony tekst nie jest aktem prawnym lub jest nieistotny w przyjętej domenie.
        False – w przeciwnym wypadku.
        """
    )


class DocSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania dokumentu.

    Zawiera podsumowanie dostarczonego dokumentu oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    title: str = Field(
        description="Tytuł dostarczonego dokumentu."
    )
    summary: str = Field(
        description="Podsumowanie dostarczonego dokumentu, ok. 300 znaków."
    )
    flag: bool = Field(
        description=
        """
        True  – jeżeli dostarczony tekst nie jest dokumentem lub jest nieistotny w przyjętej domenie.
        False – w przeciwnym wypadku.
        """
    )


class ClusterSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania klastra chunków.

    Zawiera podsumowanie dostarczonych przepisów oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    summary: str = Field(
        description="Podsumowanie dostarczonych przepisów, ok. 300 znaków."
    )
    flag: bool = Field(
        description=
        """
        True  – jeżeli dostarczony tekst zawiera elementy, które nie są przepisami prawnymi lub są 
                nieistotne w przyjętej domenie.
        False – w przeciwnym wypadku.
        """
    )


class ActClusterSummaryResponse(ClusterSummaryResponse):
    pass
