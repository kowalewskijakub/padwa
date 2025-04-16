from typing import List

from src.core.models.act import ActChunk as ActChunkDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActChunk as ActChunkORM
from src.infrastructure.repository.embeddable.embeddable_base_repository import EmbeddableBaseRepository


class ActChunkRepository(EmbeddableBaseRepository[ActChunkORM, ActChunkDomain]):
    """
    Repozytorium do zarządzania fragmentami (chunkami) aktów prawnych.

    Klasa rozszerza BaseRepository i obsługuje konwersję między obiektami ORM (ActChunkORM)
    a modelami domenowymi (ActChunkDomain).
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium fragmentów (chunków) aktów prawnych.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, ActChunkORM, ActChunkDomain)

    def get_for_act(self, act_id: int) -> List[ActChunkDomain]:
        """
        Pobiera fragmenty (chunki) dla zadanego aktu.

        :param act_id: ID aktu
        :return: Lista fragmentów (chunków) aktu jako modele domenowe
        """
        with self.db.session_scope() as session:
            act_chunks = session.query(ActChunkORM).filter(ActChunkORM.reference_id == act_id).all()
            return self._to_domain_list(act_chunks)

    def get_count(self) -> int:
        """
        Pobiera liczbę wszystkich fragmentów (chunków) aktów.

        :return: Liczba fragmentów (chunków) aktów.
        """
        with self.db.session_scope() as session:
            return session.query(ActChunkORM).count()
