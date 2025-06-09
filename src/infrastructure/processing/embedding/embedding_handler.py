# wersja: chet-theia
from typing import List, Dict

from langchain_openai import OpenAIEmbeddings

from src.common.exceptions import EmbeddingError
from src.common.logging_configurator import get_logger
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository

_logger = get_logger()


class EmbeddingHandler:
    """
    Serwis do obsługi embeddingów dla fragmentów tekstu.

    Używa LangChain z OpenAI do generowania embeddingów wektorowych.
    Zapewnia funkcjonalności generowania pojedynczych embeddingów
    oraz przetwarzania wsadowego dla większej wydajności.
    """

    def __init__(
            self,
            act_chunk_repo: ActChunkRepository,
            model_name: str,
            vector_size: int):
        """
        Inicjalizuje handler embeddingów.

        :param act_chunk_repo: Repozytorium fragmentów aktów
        :param model_name: Nazwa modelu embeddingów
        :param vector_size: Wymiar wektora embeddingów
        """
        self.act_chunk_repo = act_chunk_repo
        self.model_name = model_name
        self.vector_size = vector_size
        self.embedding_model = OpenAIEmbeddings(model=model_name)

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generuje embedding dla danego tekstu używając LangChain z OpenAI.

        :param text: Tekst do wygenerowania embeddingu
        :return: Wektor embeddingu
        :raises EmbeddingError: Gdy nie udało się wygenerować embeddingu
        """
        try:
            embedding = self.embedding_model.embed_query(text)
            return embedding
        except Exception as e:
            raise EmbeddingError(f"Błąd podczas generowania embeddingu: {str(e)}")

    def bulk_generate_embeddings(self, texts_dict: Dict[int, str]) -> dict[int, list[float]]:
        """
        Generuje embeddingi dla listy tekstów.

        :param texts_dict: Słownik zawierający ID fragmentu jako klucz i jego tekst jako wartość
        :return: Słownik mapujący ID fragmentów na ich wektory embeddingów
        :raises EmbeddingError: Gdy nie udało się wygenerować embeddingów
        """
        try:
            # Konwersja słownika na listy, zachowując mapowanie ID -> tekst
            text_ids = list(texts_dict.keys())
            texts = [texts_dict[text_id] for text_id in text_ids]

            # Generowanie embeddingów dla listy tekstów
            embeddings = self.embedding_model.embed_documents(texts)

            # Mapowanie wyników z powrotem na ID fragmentów
            return {text_id: embedding for text_id, embedding in zip(text_ids, embeddings)}
        except Exception as e:
            raise EmbeddingError(f"Błąd podczas generowania embeddingów: {str(e)}")
