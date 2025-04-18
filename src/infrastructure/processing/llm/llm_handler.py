from typing import Type, Dict, Any, Tuple, Optional, TypeVar

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.common.batch_processor import BatchProcessor
from src.infrastructure.processing.llm.llm_prompts_retriever import get_llm_prompt_retriever
from src.infrastructure.processing.llm.llm_response_models import ActSummaryResponse, LLMResponse, \
    ActClusterSummaryResponse, \
    DocSummaryResponse, ImpactAssessmentResponse

TLLMResponse = TypeVar("TLLMResponse", bound=LLMResponse)


class LLMHandler:
    """
    Klasa do obsługi interakcji z modelami językowymi.

    Używa LangChain LCEL do tworzenia łańcuchów przetwarzania między promptami,
    modelami językowymi i parsowaniem wyjść.
    """

    _prompt_mapping = {
        ActSummaryResponse: "act-summarization",
        ActClusterSummaryResponse: "act-cluster-summarization",
        DocSummaryResponse: "doc-summarization",
        ImpactAssessmentResponse: "impact-assessment",
    }

    def __init__(self, model_name):
        """
        Inicjalizuje obiekt LLMHandler.

        :param model_name: Nazwa modelu LLM OpenAI, który ma być wykorzystywany przez model
        """
        self.model_name = model_name
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
        )
        self.chains = {}

    def _create_chain(self, model_class: Type[LLMResponse]) -> Any:
        """
        Tworzy łańcuch przetwarzania LCEL dla danego modelu wyjściowego.

        :param model_class: Klasa modelu wyjściowego
        :return: Łańcuch przetwarzania LCEL
        """
        # Nie tworzy nowego łancucha, jeżeli był już utworzony
        if model_class in self.chains:
            return self.chains[model_class]

        # Utwórz parser JSON dla modelu
        json_parser = JsonOutputParser(pydantic_object=model_class)

        # Utwórz ChatPromptTemplate na podstawie szablon promptu oraz instrukcje formatowania
        prompt_id = self._prompt_mapping[model_class]
        prompt_template = get_llm_prompt_retriever().get_prompt(prompt_id)

        chat_prompt = ChatPromptTemplate.from_template(
            prompt_template
        ).partial(
            format_instructions=json_parser.get_format_instructions()
        )

        # Utwórz łańcuch przetwarzania
        chain = chat_prompt | self.llm | json_parser

        # Zapisz łańcuch w polu klasy
        self.chains[model_class] = chain

        return chain

    def invoke(self, model_class: Type[LLMResponse], args: Dict[str, Any]) -> TLLMResponse:
        """
        Wywołuje LLM z podanymi argumentami i zwraca strukturyzowany wynik.

        :param model_class: Klasa modelu wyjściowego
        :param args: Argumenty do przekazania do promptu
        :return: Ustrukturyzowany wynik zgodny z modelem wyjściowym
        """
        # Utwórz łańcuch przetwarzania
        chain = self._create_chain(model_class)

        # Wywołaj łańcuch z argumentami
        result = chain.invoke(args)

        return model_class.model_validate(result)

    def bulk_invoke(
            self,
            model_class: Type[LLMResponse],
            args_list: list[Tuple[str, Dict[str, Any]]]) -> Optional[Dict[str, TLLMResponse]]:
        """
        Wywołuje LLM z podanymi argumentami i zwraca strukturyzowany wynik.

        :param model_class: Klasa modelu wyjściowego
        :param args_list: Lista krotek (identyfikator, argumenty do przekazania do promptu)
        :return: Ustrukturyzowany wynik zgodny z modelem wyjściowym
        """
        # Utwórz łańcuch przetwarzania
        chain = self._create_chain(model_class)
        responses = {}

        with BatchProcessor(chain.invoke) as processor:
            responses = processor.process_batch(args_list)

        return {key: model_class.model_validate(value) for key, value in responses.items()}
