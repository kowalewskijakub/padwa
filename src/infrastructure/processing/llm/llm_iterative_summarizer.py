from typing import TypeVar, Type, Generator

from src.common.logging_configurator import get_logger
from src.domain.models.base import ChunkBase, ChunkClusterBase
from src.infrastructure.processing.embedding.embedding_semantic_clusterer import EmbeddingSemanticClusterer
from src.infrastructure.processing.llm.llm_handler import LLMHandler
from src.infrastructure.processing.llm.llm_response_models import LLMSummaryResponse

_logger = get_logger()

TChunkClusterBase = TypeVar("TChunkClusterBase", bound=ChunkClusterBase)
TChunkBase = TypeVar("TChunkBase", bound=ChunkBase)


class LLMIterativeSummarizer:
    """
    Klasa do iteratywnego generowania podsumowań dla aktów prawnych.

    Wykorzystuje grupowanie semantyczne fragmentów tekstu, generuje podsumowania dla każdego klastra,
    a następnie rekurencyjnie generuje podsumowania wyższego poziomu, aż do osiągnięcia pojedynczego
    podsumowania dla całego aktu.
    """

    def __init__(
            self,
            llm_handler: LLMHandler,
            semantic_clusterer: EmbeddingSemanticClusterer
    ):
        """
        Inicjalizuje obiekt LLMIterativeSummarizer.

        :param llm_handler: Handler do obsługi modeli językowych
        :param semantic_clusterer: Narzędzie do klastrowania semantycznego
        """
        self.llm_handler = llm_handler
        self.semantic_clusterer = semantic_clusterer

    def summarize(
            self,
            chunks: list[TChunkBase],
            reference_id: int,
            cluster_summary_response: Type[LLMSummaryResponse],
            max_clusters_per_level: int = 8,
    ) -> Generator[list[TChunkClusterBase], list[TChunkClusterBase], TChunkClusterBase]:
        """
        Generuje rekurencyjnie podsumowanie dla aktu prawnego, zwracając pośrednie wyniki.
        Oczekuje, że po każdym yield, caller przekaże zaktualizowane klastry z IDs.

        :param chunks: Lista fragmentów tekstu (chunków)
        :param reference_id: ID obiektu, do którego przynależą chunki
        :param cluster_summary_response: Klasa modelu LLM do użycia przy generowaniu odpowiedzi
        :param max_clusters_per_level: Maksymalna liczba klastrów na najniższym poziomie
        :yield: Lista klastrów na każdym poziomie
        :return: Obiekt z końcowym podsumowaniem
        """
        level = 0
        _logger.info(f"Rozpoczęcie rekurencyjnego podsumowywania dla obiektu {reference_id}")

        base_clusters = self._create_base_clusters(
            chunks,
            reference_id,
            cluster_summary_response,
            max_clusters_per_level
        )
        _logger.info(f"Utworzono {len(base_clusters)} klastrów podstawowych")

        # Yield – oczekuje na zaktualizowane klastry z przypisanymi ID
        updated_clusters = yield base_clusters
        current_clusters = updated_clusters if updated_clusters is not None else base_clusters

        # Iteracyjnie tworzy klastry wyższego poziomu, aż do osiągnięcia pojedynczego klastra
        while len(current_clusters) > 1:
            level += 1

            if len(current_clusters) <= 3:
                current_max_clusters = 1
            else:
                current_max_clusters = max(1, max_clusters_per_level // (2 ** level))
            _logger.info(f"Tworzenie klastrów poziomu {level} (maks. {current_max_clusters} klastrów)")

            next_level_clusters = self._create_next_level_clusters(
                current_clusters,
                reference_id,
                level,
                cluster_summary_response,
                current_max_clusters
            )
            _logger.info(f"Utworzono {len(next_level_clusters)} klastrów poziomu {level}")

            # Yield – oczekuje na zaktualizowane klastry z przypisanymi ID
            updated_clusters = yield next_level_clusters
            current_clusters = updated_clusters if updated_clusters is not None else next_level_clusters

        # Zwraca końcowy klaster
        if current_clusters and len(current_clusters) > 0:
            _logger.info(
                f"Zakończono rekurencyjne podsumowanie z {len(current_clusters)} klastrami na końcowym poziomie"
            )
            return current_clusters[0]
        else:
            _logger.warning("Zakończono rekurencyjne podsumowanie bez żadnych klastrów końcowych")
            return None

    def _create_base_clusters(
            self,
            chunks: list[TChunkBase],
            reference_id: int,
            cluster_summary_response: Type[LLMSummaryResponse],
            max_clusters: int,
    ) -> list[TChunkClusterBase]:
        """
        Tworzy podstawowe klastry (poziom 0) na podstawie fragmentów tekstu.

        :param chunks: Lista fragmentów tekstu (chunków)
        :param reference_id: ID obiektu, do którego przynależą chunki
        :param cluster_summary_response: Klasa modelu LLM do użycia przy generowaniu odpowiedzi
        :param max_clusters: Maksymalna liczba klastrów
        :return: Lista obiektów ChunkClusterBase z podsumowaniami
        """
        # Grupuje fragmenty semantycznie
        clusters = self.semantic_clusterer.cluster(chunks, max_clusters)

        # Uzupełnia metadane klastrów
        for cluster in clusters:
            cluster.reference_id = reference_id
            cluster.level = 0

            if not cluster.chunks:
                continue

            combined_text = "\n\n".join(chunk.text for chunk in cluster.chunks if chunk.text)

            if combined_text:
                response = self.llm_handler.invoke(
                    cluster_summary_response,
                    {"text": combined_text}
                )
                cluster.llm_summary_response = response

        return clusters

    def _create_next_level_clusters(
            self,
            prev_clusters: list[TChunkClusterBase],
            reference_id: int,
            level: int,
            cluster_summary_response: Type[LLMSummaryResponse],
            max_clusters: int,
    ) -> list[TChunkClusterBase]:
        """
        Tworzy klastry wyższego poziomu na podstawie klastrów niższego poziomu.

        :param prev_clusters: Lista klastrów niższego poziomu
        :param reference_id: ID obiektu, do którego przynależą klastry
        :param level: Aktualny poziom hierarchii klastrów
        :param cluster_summary_response: Klasa modelu LLM do użycia przy generowaniu odpowiedzi
        :param max_clusters: Maksymalna liczba klastrów do utworzenia
        :return: Lista klastrów wyższego poziomu
        """
        if len(prev_clusters) <= 1:
            return prev_clusters

        # Używamy klastrowania do pogrupowania klastrów z poprzedniego poziomu
        pseudo_chunks = []
        cluster_map = {}  # Mapowanie ID pseudo-chunka na oryginalny klaster

        for cluster in prev_clusters:
            # Tworzy pseudo-chunki z klastrów niższego poziomu
            chunk = ChunkBase(
                id=cluster.id,
                text=cluster.text,
                embedding=cluster.embedding
            )
            pseudo_chunks.append(chunk)
            cluster_map[chunk.id] = cluster

        meta_clusters = self.semantic_clusterer.cluster(pseudo_chunks, max_clusters)

        next_level_clusters = []

        for i, meta_cluster in enumerate(meta_clusters):
            if not meta_cluster.chunks:
                continue

            # Zbieramy teksty i ID klastrów z niższego poziomu
            child_clusters = []
            child_texts = []

            for pseudo_chunk in meta_cluster.chunks:
                if pseudo_chunk.id in cluster_map:
                    # Dodajemy oryginalny klaster niższego poziomu
                    child_clusters.append(cluster_map[pseudo_chunk.id])
                    if pseudo_chunk.text:
                        child_texts.append(pseudo_chunk.text)

            if not child_clusters or not child_texts:
                continue

            # Tworzenie nowego klastra wyższego poziomu
            parent_cluster = ChunkClusterBase(
                reference_id=reference_id,
                level=level,
            )
            combined_text = "\n\n".join(child_texts)
            response = self.llm_handler.invoke(
                cluster_summary_response,
                {"text": combined_text}
            )
            parent_cluster.llm_summary_response = response
            next_level_clusters.append(parent_cluster)

        return next_level_clusters
