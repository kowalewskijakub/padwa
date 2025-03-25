from typing import List

from sqlalchemy import or_
from sqlalchemy.sql.operators import is_

from src.domain.models.doc import Doc as DocDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.doc_orm import Doc as DocORM
from src.infrastructure.repository.base_repository import BaseRepository


class DocRepository(BaseRepository[DocORM, DocDomain]):
    """
    Repozytorium do zarządzania encjami dokumentów.

    Klasa rozszerza BaseRepository i obsługuje konwersję między obiektami ORM (DocORM)
    a modelami domenowymi (DocDomain).
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium dokumentów.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, DocORM, DocDomain)

    def get_all(self) -> List[DocDomain]:
        """
        Pobiera wszystkie aktywne dokumenty.

        :return: Lista dokumentów jako modele domenowe
        """
        with self.db.session_scope() as session:
            doc_orms = (session
                        .query(DocORM)
                        .filter(or_(is_(DocORM.archived, None), DocORM.archived == False))
                        .all()
                        )
            return self._to_domain_list(doc_orms)

    def get_count(self) -> int:
        """
        Pobiera liczbę aktywnych dokumentów.

        :return: Liczba aktywnych dokumentów
        """
        with self.db.session_scope() as session:
            return session.query(DocORM).filter(or_(is_(DocORM.archived, None), DocORM.archived == False)).count()
