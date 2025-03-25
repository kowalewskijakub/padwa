# wersja: chet-theia
from typing import List, TypeVar, Generic

import numpy as np
from sklearn.cluster import KMeans

from src.domain.models.base import ChunkBase, ChunkClusterBase
from src.infrastructure.processing.embedding.embedding_handler import EmbeddingHandler
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository

T = TypeVar('T', bound=ChunkBase)


class EmbeddingSemanticClusterer(Generic[T]):
    """
    Klasa odpowiedzialna za grupowanie semantyczne fragmentów tekstów
    na podstawie ich wektorów embeddingu.

    Wykorzystuje algorytm k-means do identyfikacji klastrów tematycznych o podobnej zawartości.
    """

    def __init__(self, act_chunk_repo: ActChunkRepository, embedding_handler: EmbeddingHandler):
        """
        Inicjalizuje EmbeddingSemanticClusterer.

        :param act_chunk_repo: Repozytorium fragmentów aktów prawnych
        :param embedding_handler: Serwis embeddingów używany do znajdowania podobieństw
        """
        self.act_chunk_repo = act_chunk_repo
        self.embedding_handler = embedding_handler
        self.num_clusters = 10  # Domyślna liczba klastrów

    @staticmethod
    def _split_into_equal_chunks(items: List[T], n: int) -> List[List[T]]:
        """
        Metoda prywatna, która dzieli listę na n równych części.

        Wykorzystywana, jeżeli dostarczona liczba fragmentów jest mniejsza niż oczekiwana
        liczba klastrów.

        :param items: Lista elementów do podziału, dziedziczących po ChunkBase
        :param n: Liczba części
        :return: Lista list, każda zawierająca część elementów
        """
        n = min(n, len(items))
        return [chunk.tolist() for chunk in np.array_split(np.array(items, dtype=object), n)]

    def cluster(self, chunks: List[T], num_clusters: int = 8) -> List[ChunkClusterBase]:
        """
        Grupuje fragmenty (chunki) w klastry.

        Korzysta z algorytmu k-means. Akceptuje tylko fragmenty dziedziczące po ChunkBase.

        :param chunks: Lista fragmentów do zgrupowania, dziedziczących po ChunkBase
        :param num_clusters: Liczba klastrów do utworzenia
        :return: Lista obiektów ChunkClusterBase, gdzie każdy obiekt zawiera listę fragmentów (chunków) w atrybucie 'chunks'
        """
        if not chunks:
            return []

        # Sprawdza, czy wszystkie fragmenty mają embeddingi
        if any(chunk.embedding is None for chunk in chunks):
            return []

        # Sprawdza, czy liczba klastrów nie jest większa niż liczba fragmentów
        # Jeśli tak – dokonaj podziału po równo
        self.num_clusters = min(num_clusters, len(chunks))
        if len(chunks) < self.num_clusters:
            chunk_lists = self._split_into_equal_chunks(chunks, self.num_clusters)
            return [ChunkClusterBase(chunks=chunk_list) for chunk_list in chunk_lists]

        embeddings = np.array([chunk.embedding for chunk in chunks])

        kmeans = KMeans(
            n_clusters=self.num_clusters,
            random_state=42
        )

        cluster_labels = kmeans.fit_predict(embeddings)

        # Tworzy klastry
        cluster_objects = [ChunkClusterBase(chunks=[]) for _ in range(self.num_clusters)]

        # Przypisuje fragmenty do klastrów na podstawie etykiet
        for i, label in enumerate(cluster_labels):
            cluster_objects[label].chunks.append(chunks[i])

        return cluster_objects
