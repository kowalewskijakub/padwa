from typing import Optional

from infrastructure.processing.embedding.embedding_handler import EmbeddingHandler
from infrastructure.processing.llm.llm_handler import LLMHandler
from infrastructure.processing.llm.llm_response_models import DocSummaryResponse
from infrastructure.processing.text.text_processor import get_doc_processors, TextProcessor

from src.application.dtos.doc_dto import DocProcessedDTO, DocChunkDTO
from src.common.exceptions import EmbeddingError
from src.common.logging_configurator import get_logger
from src.domain.models.doc import Doc, DocChunk
from src.infrastructure.repository.core.doc_repository import DocRepository
from src.infrastructure.repository.embeddable.doc_chunk_repository import DocChunkRepository

_logger = get_logger()


class DocsService:
    """
    Orchestrator operacji na dokumentach.
    Zarządza całym procesem przetwarzania dokumentów, od wczytania po wygenerowanie podsumowania.
    """

    def __init__(
            self,
            doc_repo: DocRepository,
            doc_chunk_repo: DocChunkRepository,
            llm_handler: LLMHandler,
            embedding_handler: EmbeddingHandler
    ):
        """
        Inicjalizuje orchestrator dokumentów.

        :param doc_repo: Repozytorium dokumentów
        :param doc_chunk_repo: Repozytorium fragmentów dokumentów
        :param llm_handler: Handler modeli językowych
        :param embedding_handler: Handler embeddingów
        """
        self.doc_repo = doc_repo
        self.doc_chunk_repo = doc_chunk_repo
        self.llm_handler = llm_handler
        self.embedding_handler = embedding_handler

    def get_all(self) -> list[DocProcessedDTO]:
        """
        Zwraca wszystkie aktywne dokumenty zapisane w bazie danych.

        :return: Lista obiektów DocProcessedDTO
        """
        return [DocProcessedDTO.model_validate(doc) for doc in self.doc_repo.get_all()]

    def get_chunks_for_doc(self, doc_id: int) -> list[DocChunkDTO]:
        """
        Zwraca z bazy danych fragmenty (chunki) dla danego dokumentu.

        :param doc_id: ID dokumentu
        :return: Lista obiektów DocChunkDTO
        """
        return [
            DocChunkDTO.model_validate(chunk)
            for chunk in self.doc_chunk_repo.get_for_doc(doc_id)
        ]

    def update_missing_embeddings(self) -> None:
        """
        Aktualizuje embeddingi dla wszystkich fragmentów dokumentów, które jeszcze ich nie mają.

        :raises EmbeddingError: Gdy nie udało się zaktualizować embeddingów
        """
        try:
            # Pobierz chunki, które nie mają embeddingów
            chunks = self.doc_chunk_repo.get_where_embeddings_missing()

            # Utwórz słownik: id_chunka -> tekst_chunka
            texts_dict = {chunk.id: chunk.text for chunk in chunks}

            # Wygeneruj embeddingi za pomocą embedding_handler
            embeddings_dict = self.embedding_handler.bulk_generate_embeddings(texts_dict)

            # Przypisz embeddingi do odpowiednich chunków
            for chunk in chunks:
                chunk.embedding = embeddings_dict.get(chunk.id)

            # Zapisz zaktualizowane chunki w bazie danych
            self.doc_chunk_repo.bulk_update(chunks)
        except Exception as e:
            raise EmbeddingError(f"Błąd podczas aktualizacji embeddingów dokumentów: {str(e)}")

    def archive_document(self, doc_id: int) -> bool:
        """
        Archiwizuje dokument (ustawia flagę archived=True).

        :param doc_id: ID dokumentu do zarchiwizowania
        :return: True, jeśli operacja się powiodła, False w przeciwnym razie
        """
        doc = self.doc_repo.get_by_id(doc_id)
        if not doc:
            return False

        doc.archived = True
        doc = self.doc_repo.update(doc)
        return True if doc else False

    def process_document(self, pdf_content: bytes) -> Optional[DocProcessedDTO]:
        """
        Przetwarza dokument PDF.
        Wykonuje następujące operacje:
        1. Przetwarza PDF (parsuje, wyodrębnia chunki)
        2. Generuje podsumowanie i tytuł dla dokumentu
        3. Tworzy obiekt dokumentu w bazie danych
        4. Zapisuje chunki w bazie danych
        5. Aktualizuje embeddingi dla zapisanych chunków

        :param pdf_content: Zawartość pliku PDF jako bajty
        :return: Obiekt DocProcessedDTO lub None w przypadku niepowodzenia
        """
        try:
            # --- 1. Przetwarza PDF (parsuje, wyodrębnia chunki) ---
            chunking_function, element_processors = get_doc_processors()
            chunks = TextProcessor.process_document(
                pdf_content,
                chunking_function,
                element_processors
            )

            # --- 2. Generuje podsumowanie i tytuł dla dokumentu ---
            full_text = "\n\n".join(chunks)
            response = self.llm_handler.invoke(
                DocSummaryResponse,
                {"text": full_text}
            )

            # --- 3. Tworzy obiekt dokumentu w bazie danych ---
            doc = Doc(
                title=response.title,
                summary=response.summary,
                flag=response.flag,
            )
            doc = self.doc_repo.create(doc)

            # --- 4. Zapisz chunki w bazie danych ---
            self.doc_chunk_repo.bulk_create(
                [DocChunk(reference_id=doc.id, text=chunk) for chunk in chunks]
            )

            # --- 5. Zaktualizuj embeddingi dla zapisanych chunków ---
            self.update_missing_embeddings()

            return DocProcessedDTO.model_validate(doc)
        except Exception as e:
            _logger.error(f"Błąd podczas przetwarzania dokumentu PDF: {str(e)}")
            return None
