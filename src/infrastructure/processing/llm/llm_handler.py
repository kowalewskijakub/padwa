import time
from typing import Type, Dict, Any, Tuple, Optional, TypeVar

from langchain.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.common.batch_processor import BatchProcessor
from src.common.logging_configurator import get_logger
from src.infrastructure.processing.llm.llm_prompts_retriever import get_llm_prompt_retriever
from src.infrastructure.processing.llm.llm_response_models import (LLMResponse, ActClusterSummaryResponse,
                                                                   DocSummaryResponse, ImpactAssessmentResponse)

TLLMResponse = TypeVar("TLLMResponse", bound=LLMResponse)
_logger = get_logger()


class LLMHandler:
    """
    Klasa do obsługi interakcji z modelami językowymi.

    Używa LangChain LCEL do tworzenia łańcuchów przetwarzania między promptami,
    modelami językowymi i parsowaniem wyjść.
    """

    _prompt_mapping = {
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

    def invoke(self, model_class: Type[LLMResponse], args: Dict[str, Any], max_retries: int = 3,
               delay_seconds: int = 5) -> TLLMResponse:
        """
        Wywołuje LLM z podanymi argumentami i zwraca strukturyzowany wynik.
        Implementuje logikę ponawiania prób w przypadku błędów parsowania.

        :param model_class: Klasa modelu wyjściowego
        :param args: Argumenty do przekazania do promptu
        :param max_retries: Maksymalna liczba ponownych prób
        :param delay_seconds: Opóźnienie między ponownymi próbami w sekundach
        :return: Ustrukturyzowany wynik zgodny z modelem wyjściowym
        :raises OutputParserException: Jeśli parsowanie nie powiedzie się po wszystkich próbach
        """
        # Utwórz łańcuch przetwarzania
        chain = self._create_chain(model_class)

        retries = 0
        last_exception = None
        while retries < max_retries:
            try:
                result = chain.invoke(args)
                return model_class.model_validate(result)
            except OutputParserException as e:
                last_exception = e
                retries += 1
                _logger.warning(
                    f"LLM output parsing failed for model {model_class.__name__} (attempt {retries}/{max_retries}): {e}. "
                    f"Args: {args}. Retrying in {delay_seconds}s..."
                )
                if retries >= max_retries:
                    _logger.error(
                        f"LLM output parsing failed after {max_retries} retries for model {model_class.__name__} with args: {args}."
                    )
                    raise last_exception
                time.sleep(delay_seconds)
            except Exception as e:
                _logger.error(
                    f"An unexpected error occurred during LLM invoke for model {model_class.__name__} with args {args}: {e}")
                raise
        if last_exception:
            raise last_exception
        raise RuntimeError(
            f"LLM invoke failed for {model_class.__name__} after {max_retries} retries without a specific parsing error.")

    def bulk_invoke(
            self,
            model_class: Type[LLMResponse],
            args_list: list[Tuple[str, Dict[str, Any]]]) -> Optional[Dict[str, TLLMResponse]]:
        """
        Wywołuje LLM z podanymi argumentami i zwraca strukturyzowany wynik.
        Korzysta z metody invoke, która zawiera logikę ponawiania prób.

        :param model_class: Klasa modelu wyjściowego
        :param args_list: Lista krotek (identyfikator, argumenty do przekazania do promptu)
        :return: Ustrukturyzowany wynik zgodny z modelem wyjściowym
        """

        def process_item(item_args: Dict[str, Any]) -> TLLMResponse:
            return self.invoke(model_class, item_args)

        with BatchProcessor(process_func=process_item) as processor:
            items_for_batch = [(identifier, item_args) for identifier, item_args in args_list]

            try:
                batch_results = processor.process_batch(items_for_batch)
                validated_responses = {}
                for key, value in batch_results.items():
                    if isinstance(value, Exception):
                        _logger.error(f"Error processing item with ID {key} in bulk_invoke: {value}")
                        validated_responses[key] = None  # Or some error indicator
                    else:
                        validated_responses[key] = value
                return validated_responses

            except Exception as e:
                _logger.error(f"An error occurred during bulk_invoke: {str(e)}")
                return None
