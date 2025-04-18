from typing import TypeVar, Generic, List, Type

import numpy as np

from src.core.models.base import EmbeddableBase
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.base_orm import EmbeddableBase as EmbeddableBaseORM
from src.infrastructure.repository.base_repository import BaseRepository

TEmbeddableORM = TypeVar('TEmbeddableORM', bound=EmbeddableBaseORM)
TEmbeddableDomain = TypeVar('TEmbeddableDomain', bound=EmbeddableBase)


class EmbeddableBaseRepository(BaseRepository[TEmbeddableORM, TEmbeddableDomain],
                               Generic[TEmbeddableORM, TEmbeddableDomain]):
    """
    Repozytorium bazowe do zarządzania encjami z embeddingami.

    Klasa rozszerza BaseRepository i dodaje funkcjonalności związane z embeddingami,
    takie jak pobieranie encji bez embeddingów i inne operacje specyficzne dla modeli
    z wektorami embeddingów.
    """

    def __init__(self, db_manager: DatabaseManager, orm_class: Type[TEmbeddableORM],
                 domain_class: Type[TEmbeddableDomain]):
        """
        Inicjalizuje repozytorium dla encji z embeddingami.

        :param db_manager: Menedżer bazy danych
        :param orm_class: Klasa ORM, której dotyczy zadane repozytorium
        :param domain_class: Klasa domeny, której dotyczy zadane repozytorium
        """
        super().__init__(db_manager, orm_class, domain_class)

    def get_for_parent(self, reference_id: int) -> List[TEmbeddableORM]:
        """
        Pobiera encje dla zadanego rodzica.

        :param reference_id: ID rodzica
        :return: Lista encji jako obiekty ORM
        """
        with self.db.session_scope() as session:
            entities = session.query(self.orm_class).filter(self.orm_class.reference_id == reference_id).all()
            return self._to_domain_list(entities)

    def get_where_embeddings_missing(self) -> List[TEmbeddableDomain]:
        """
        Pobiera encje, dla których brakuje embeddingów.

        :return: Lista encji jako modele domenowe bez embeddingów
        """
        with self.db.session_scope() as session:
            entities = (
                session.query(self.orm_class)
                .filter(self.orm_class.embedding.is_(None))
                .all()
            )
            return self._to_domain_list(entities)

    def _get_top_n_similar(
            self,
            all_entities: [TEmbeddableORM],
            embedding: list[float], n: int = 5
    ) -> list[TEmbeddableDomain]:
        """
        Pobiera n najbardziej podobnych encji do zadanego embeddingu.

        :param all_entities: Lista wszystkich encji
        :param embedding: Wektor embeddingu
        :param n: Liczba encji do zwrócenia
        :return: Lista najbardziej podobnych encji jako modele domenowe
        """
        similarities = []
        for entity in all_entities:
            entity_embedding = entity.embedding
            similarity = np.dot(embedding, entity_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(entity_embedding))
            similarities.append((entity, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)

        top_entities = [entity for entity, _ in similarities[:n]]
        return self._to_domain_list(top_entities)
