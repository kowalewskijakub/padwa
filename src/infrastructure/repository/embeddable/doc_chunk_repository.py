from typing import List

from sqlalchemy.orm import Session
from sqlmodel import and_

from src.core.models.doc import DocChunk as DocChunkDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.doc_orm import DocChunk as DocChunkORM, Doc as DocORM
from src.infrastructure.repository.base_repository import TORM
from src.infrastructure.repository.embeddable.embeddable_base_repository import EmbeddableBaseRepository


class DocChunkRepository(EmbeddableBaseRepository[DocChunkORM, DocChunkDomain]):
    """
    Repozytorium do zarządzania fragmentami (chunkami) dokumentów.

    Klasa rozszerza EmbeddableBaseRepository i obsługuje konwersję między obiektami ORM (DocChunkORM)
    a modelami domenowymi (DocChunkDomain).
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium fragmentów (chunków) dokumentów.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, DocChunkORM, DocChunkDomain)

    def _get_all(self, session: Session) -> List[TORM]:
        """
        Zwraca wszystkie fragmenty (chunki) dokumentów, które nie są zarchiwizowane lub nieistotne.

        :param session: Sesja bazy danych
        """
        return (
            session.query(DocChunkORM)
            .join(DocORM)
            .filter(and_(DocORM.is_archived.is_(False)), DocORM.flag.is_(False))
        ).all()

    def get_for_doc(self, doc_id: int) -> List[DocChunkDomain]:
        """
        Pobiera fragmenty (chunki) dla zadanego dokumentu.

        :param doc_id: ID dokumentu
        :return: Lista fragmentów (chunków) dokumentu jako modele domenowe
        """
        with self.db.session_scope() as session:
            doc_chunks = session.query(DocChunkORM).filter(DocChunkORM.reference_id == doc_id).all()
            return self._to_domain_list(doc_chunks)

    def get_count(self) -> int:
        """
        Pobiera liczbę wszystkich fragmentów (chunków) dokumentów.

        :return: Liczba fragmentów (chunków) dokumentów.
        """
        with self.db.session_scope() as session:
            return session.query(DocChunkORM).count()

    def get_top_n_similar(self, embedding: list[float], n: int = 5):
        """
        Pobiera n najbliższych fragmentów (chunków) dokumentów na podstawie embeddingu.

        :param embedding: Wektor embeddingu
        :param n: Liczba najbliższych fragmentów (chunków) do pobrania
        """
        with self.db.session_scope() as session:
            all_entities = session.query(DocChunkORM).all()
            return self._get_top_n_similar(all_entities, embedding, n)
