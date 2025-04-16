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
        description="Ocenę wpływu zmiany na dokument organizacyjny w skali od 0 do 1, "
                    "gdzie 1 oznacza pewny wpływ, a 0 brak wpływu"
    )
    justification: str = Field(
        description="Uzasadnienie Twojej oceny wpływu zmiany w akcie prawnym na fragment dokumentu."
    )


class ActSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania aktu prawnego.

    Zawiera podsumowanie dostarczonego aktu prawnego oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    summary: str = Field(
        description="Zwięzłe i konkretne podsumowanie tekstu w języku polskim (200-300 słów)"
    )
    flag: bool = Field(
        description=
        """
        False – jeżeli dostarczony tekst jest istotny
        True  – w przeciwnym wypadku
        """
    )


class DocSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania dokumentu.

    Zawiera podsumowanie dostarczonego dokumentu oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    title: str = Field(
        description="Tytuł dostarczonego tekstu"
    )
    summary: str = Field(
        description="Zwięzłe i konkretne podsumowanie tekstu w języku polskim (200-300 słów)"
    )
    flag: bool = Field(
        description=
        """
        False – jeżeli dostarczony tekst jest istotny
        True  – w przeciwnym wypadku
        """
    )


class ClusterSummaryResponse(LLMSummaryResponse):
    """
    Model odpowiedzi LLM dla podsumowania klastra chunków.

    Zawiera podsumowanie dostarczonych przepisów oraz flagę sygnalizującą, że dostarczony tekst
    powinien być pominięty w kontekście przyjętej domeny.
    """
    summary: str = Field(
        description="Zwięzłe i konkretne podsumowanie tekstu w języku polskim (200-300 słów)"
    )
    flag: bool = Field(
        description=
        """
        False – jeżeli dostarczony tekst jest istotny
        True  – w przeciwnym wypadku
        """
    )


class ActClusterSummaryResponse(ClusterSummaryResponse):
    pass
