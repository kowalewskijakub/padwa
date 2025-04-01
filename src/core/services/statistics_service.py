# wersja: chet-theia
from src.core.dtos.statistics_dto import ActStatisticsDTO, DocumentStatisticsDTO
from src.infrastructure.repository.core.act_repository import ActRepository
from src.infrastructure.repository.core.doc_repository import DocRepository
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository
from src.infrastructure.repository.embeddable.doc_chunk_repository import DocChunkRepository


class StatisticsService:

    def __init__(
            self,
            act_repo: ActRepository,
            act_chunk_repo: ActChunkRepository,
            doc_repo: DocRepository,
            doc_chunk_repo: DocChunkRepository
    ):
        """
        Inicjalizuje serwis do obsługi statystyk.

        :param act_repo: Repozytorium aktów prawnych
        :param act_chunk_repo: Repozytorium do fragmentów (chunków) aktów
        :param doc_repo: Repozytorium dokumentów
        :param doc_chunk_repo: Repozytorium do fragmentów (chunków) dokumentów
        """
        self.act_repo = act_repo
        self.act_chunk_repo = act_chunk_repo
        self.doc_repo = doc_repo
        self.doc_chunk_repo = doc_chunk_repo

    def get_act_statistics(self) -> ActStatisticsDTO:
        """
        Pobiera statystyki dotyczące aktów prawnych.

        :return: Słownik ze statystykami aktów
        """
        total_acts = self.act_repo.get_count()
        total_acts_by_year = self.act_repo.get_count_by_year()
        total_chunks = self.act_chunk_repo.get_count()

        # Pobierz liczbę fragmentów (chunków) dla każdego aktu
        avg_chunks_per_act = round(total_chunks / total_acts, 2) if total_acts > 0 else 0

        return ActStatisticsDTO(
            total_acts=total_acts,
            total_acts_by_year=total_acts_by_year,
            total_chunks=total_chunks,
            avg_chunks_per_act=avg_chunks_per_act,
        )

    def get_doc_statistics(self) -> DocumentStatisticsDTO:
        """
        Pobiera statystyki dotyczące dokumentów.

        :return: DTO ze statystykami dokumentów
        """
        total_documents = self.doc_repo.get_count()
        total_chunks = self.doc_chunk_repo.get_count()
        avg_chunks_per_document = round(total_chunks / total_documents, 2) if total_documents > 0 else 0

        # Zbierz tekst ze wszystkich dokumentów do word cloud
        documents = self.doc_repo.get_all()
        meta_text = " ".join([doc.title + " " + (doc.title or "") for doc in documents])

        return DocumentStatisticsDTO(
            total_documents=total_documents,
            total_chunks=total_chunks,
            avg_chunks_per_document=avg_chunks_per_document,
            meta_text=meta_text,
        )
