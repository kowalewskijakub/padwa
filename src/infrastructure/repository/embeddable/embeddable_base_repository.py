# wersja: chet-theia
from typing import TypeVar, Generic, List, Type

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
