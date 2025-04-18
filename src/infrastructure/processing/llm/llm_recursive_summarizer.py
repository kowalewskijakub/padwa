from typing import TypeVar, Type, Generator, Any

from src.common.logging_configurator import get_logger
from src.core.models.base import ChunkBase, ChunkClusterBase
from src.infrastructure.processing.embedding.embedding_semantic_clusterer import EmbeddingSemanticClusterer
from src.infrastructure.processing.llm.llm_handler import LLMHandler
from src.infrastructure.processing.llm.llm_response_models import LLMSummaryResponse

_logger = get_logger()

TChunkClusterBase = TypeVar("TChunkClusterBase", bound=ChunkClusterBase)
TChunkBase = TypeVar("TChunkBase", bound=ChunkBase)


class LLMRecursiveSummarizer:
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
    ) -> Generator[list[TChunkClusterBase] | list[Any], list[TChunkClusterBase], TChunkClusterBase | None]:
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
        base_clusters = self._create_base_clusters(
            chunks,
            reference_id,
            cluster_summary_response,
            max_clusters_per_level
        )

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

            next_level_clusters = self._create_next_level_clusters(
                current_clusters,
                reference_id,
                level,
                cluster_summary_response,
                current_max_clusters
            )

            updated_clusters = yield next_level_clusters
            current_clusters = updated_clusters if updated_clusters is not None else next_level_clusters

        return current_clusters[0] if current_clusters else None

    def _create_base_clusters(
            self,
            chunks: list[TChunkBase],
            reference_id: int,
            cluster_summary_response: Type[LLMSummaryResponse],
            max_clusters: int,
    ) -> list[TChunkClusterBase]:
        clusters = self.semantic_clusterer.cluster(chunks, max_clusters)

        batch_args = []
        valid_clusters = []

        for idx, cluster in enumerate(clusters):
            cluster.reference_id = reference_id
            cluster.level = 0

            if not cluster.chunks:
                continue

            combined_text = "\n\n".join(chunk.text for chunk in cluster.chunks if chunk.text)

            if combined_text:
                valid_clusters.append(cluster)
                batch_args.append((str(idx), {"text": combined_text}))

        if batch_args:
            batch_results = self.llm_handler.bulk_invoke(
                cluster_summary_response,
                batch_args
            )
            for idx_str, response in batch_results.items():
                cluster_idx = int(idx_str)
                if cluster_idx < len(valid_clusters):
                    valid_clusters[cluster_idx].llm_summary_response = response

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

        pseudo_chunks = []
        cluster_map = {}

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
        batch_args = []
        valid_meta_clusters = []

        for i, meta_cluster in enumerate(meta_clusters):
            if not meta_cluster.chunks:
                continue

            child_texts = []
            for pseudo_chunk in meta_cluster.chunks:
                if pseudo_chunk.id in cluster_map:
                    child_cluster = cluster_map[pseudo_chunk.id]
                    if child_cluster.text:
                        child_texts.append(child_cluster.text)

            if not child_texts:
                continue

            parent_cluster = ChunkClusterBase(
                reference_id=reference_id,
                level=level,
            )
            next_level_clusters.append(parent_cluster)
            valid_meta_clusters.append(parent_cluster)

            combined_text = "\n\n".join(child_texts)
            batch_args.append((str(i), {"text": combined_text}))

        if batch_args:
            batch_results = self.llm_handler.bulk_invoke(
                cluster_summary_response,
                batch_args
            )

            for idx_str, response in batch_results.items():
                cluster_idx = int(idx_str)
                if cluster_idx < len(valid_meta_clusters):
                    valid_meta_clusters[cluster_idx].llm_summary_response = response

        return next_level_clusters
