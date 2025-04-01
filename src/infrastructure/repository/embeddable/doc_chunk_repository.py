from typing import List

from src.core.models.doc import DocChunk as DocChunkDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.doc_orm import DocChunk as DocChunkORM
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
