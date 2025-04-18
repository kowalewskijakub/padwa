from typing import Optional, List, TypeVar, Type

from src.common.exceptions import EntityNotFoundError, EmbeddingError
from src.common.logging_configurator import get_logger
from src.core.dtos.act_dto import ActProcessedDTO
from src.core.models.base import EmbeddableBase, ChunkClusterBase, Base
from src.infrastructure.processing.embedding.embedding_handler import EmbeddingHandler
from src.infrastructure.processing.llm.llm_recursive_summarizer import LLMRecursiveSummarizer
from src.infrastructure.processing.llm.llm_response_models import LLMSummaryResponse, ActClusterSummaryResponse
from src.infrastructure.repository.base_repository import BaseRepository
from src.infrastructure.repository.core.act_repository import ActRepository
from src.infrastructure.repository.embeddable.act_chunk_cluster_repository import ActChunkClusterRepository
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository
from src.infrastructure.repository.embeddable.embeddable_base_repository import EmbeddableBaseRepository

_logger = get_logger()

TBase = TypeVar('TBase', Base, EmbeddableBase)
TChunkClusterBase = TypeVar('TChunkClusterBase', bound=ChunkClusterBase)


class ClustersService:
    """
    Przetwarza klastry obiektów dziedziczących po EmbeddableBase.
    """

    def __init__(
            self,
            act_repo: ActRepository,
            act_chunk_repo: ActChunkRepository,
            act_chunk_cluster_repo: ActChunkClusterRepository,
            embedding_handler: EmbeddingHandler,
            llm_recursive_summarizer: LLMRecursiveSummarizer
    ):
        """
        Inicjalizuje orchestrator klastrów.

        :param act_repo: Repozytorium aktów prawnych
        :param act_chunk_repo: Repozytorium fragmentów aktów
        :param act_chunk_cluster_repo: Repozytorium klastrów fragmentów
        :param embedding_handler: Handler do zarządzania embeddingami
        :param llm_recursive_summarizer: Obiekt do rekurencyjnego podsumowywania
        """
        self.act_repo = act_repo
        self.act_chunk_repo = act_chunk_repo
        self.act_chunk_cluster_repo = act_chunk_cluster_repo
        self.embedding_handler = embedding_handler
        self.llm_recursive_summarizer = llm_recursive_summarizer

    def generate_act_summary(self, act_id: int) -> Optional[ActProcessedDTO]:
        """
        Generuje podsumowanie aktu prawnego z wykorzystaniem rekurencyjnej metody.
        Zapisuje pośrednie klastry w bazie danych podczas procesu.

        :param act_id: ID aktu prawnego
        :return: DTO zawierające dane przetworzonego aktu lub None w przypadku niepowodzenia
        :raises EntityNotFoundError: Gdy akt o podanym ID nie istnieje
        """
        try:
            # --- 1. Pobierz akt prawny ---
            act = self.act_repo.get_by_id(act_id)

            # --- 2. Przetwórz rekurencyjne podsumowanie ---
            final_summary = self._process_recursive_summarization(
                act_id,
                self.act_chunk_repo,
                self.act_chunk_cluster_repo,
                ActClusterSummaryResponse
            )

            # --- 3. Aktualizuj akt o końcowe podsumowanie ---
            if final_summary:
                return self._update_entity_with_meta_summary(
                    act,
                    final_summary,
                    self.act_repo
                )

            return None
        except EntityNotFoundError:
            _logger.error(f"Akt o ID {act_id} nie istnieje")
            raise
        except EmbeddingError as e:
            _logger.error(f"Błąd podczas generowania embeddingów dla aktu {act_id}: {str(e)}")
            return None
        except Exception as e:
            _logger.error(f"Nieoczekiwany błąd podczas generowania podsumowania aktu {act_id}: {str(e)}")
            return None

    def _add_embeddings_to_clusters(self, clusters: List[TChunkClusterBase]) -> List[TChunkClusterBase]:
        """
        Dodaje embeddingi do klastrów.

        :param clusters: Lista klastrów
        :return: Lista klastrów z embeddingami
        """
        if not clusters:
            return clusters

        # Stwórz słownik tekstów z klastrów (indeks tymczasowy -> tekst)
        texts_dict = {i: cluster.text for i, cluster in enumerate(clusters) if cluster.text}
        if not texts_dict:
            return clusters

        embeddings_dict = self.embedding_handler.bulk_generate_embeddings(texts_dict)

        # Przypisz embeddingi do odpowiednich klastrów
        for i, cluster in enumerate(clusters):
            if i in embeddings_dict:
                cluster.embedding = embeddings_dict[i]

        return clusters

    def _process_recursive_summarization(
            self,
            reference_id: int,
            chunk_repository: EmbeddableBaseRepository,
            chunk_cluster_repository: EmbeddableBaseRepository,
            cluster_summary_response: Type[LLMSummaryResponse],
            max_clusters_per_level: int = 8
    ) -> TChunkClusterBase:
        """
        Przetwarza rekurencyjne podsumowanie dla encji.

        :param reference_id: ID encji
        :param chunk_repository: Repozytorium fragmentów
        :param chunk_cluster_repository: Repozytorium klastrów fragmentów
        :param cluster_summary_response: Klasa odpowiedzi LLM
        :param max_clusters_per_level: Maksymalna liczba klastrów na poziom
        :return: Końcowe podsumowanie
        """
        chunks = chunk_repository.get_for_parent(reference_id)
        summarizer_gen = self.llm_recursive_summarizer.summarize(
            chunks,
            reference_id,
            cluster_summary_response,
            max_clusters_per_level
        )

        try:
            clusters = next(summarizer_gen)
            while True:
                # Dodaj embeddingi i zapisz klastry
                clusters_with_embeddings = self._add_embeddings_to_clusters(clusters)
                saved_clusters = chunk_cluster_repository.bulk_create(clusters_with_embeddings)

                # Przygotuj klastry dla następnego poziomu
                next_level_clusters = summarizer_gen.send(saved_clusters)

                # Ustaw relacje rodzic-dziecko dla klastrów wyższego poziomu
                if saved_clusters and saved_clusters[0].level > 0:
                    self._set_parent_child_relations(next_level_clusters)

                clusters = next_level_clusters
        except StopIteration as e:
            return e.value

    def _set_parent_child_relations(self, parent_clusters: List[TChunkClusterBase]) -> None:
        """
        Ustawia relacje rodzic-dziecko dla klastrów.

        :param parent_clusters: Lista klastrów nadrzędnych
        """
        for parent_cluster in parent_clusters:
            if hasattr(parent_cluster, 'chunks') and parent_cluster.chunks:
                for child in parent_cluster.chunks:
                    if hasattr(child, 'id') and child.id is not None:
                        parent_cluster.parent_cluster_id = child.id
                        break
                # Czyścimy pole chunks dla klastrów wyższego poziomu
                parent_cluster.chunks = []

    def _update_entity_with_meta_summary(
            self,
            entity: Base,
            summary: TChunkClusterBase,
            parent_repository: BaseRepository) -> Optional[TBase]:
        """
        Aktualizuje encję o podsumowanie.

        :param entity: Encja do aktualizacji
        :param summary: Obiekt zawierający podsumowanie
        :return: Zaktualizowana encja lub None w przypadku niepowodzenia
        """
        entity.summary = summary.text
        entity.flag = summary.flag
        parent_repository.update(entity)
        return entity
