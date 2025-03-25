# wersja: chet-theia
from typing import Optional, List, Dict, Tuple

from sqlalchemy import func, and_, or_
from sqlalchemy.sql.operators import is_
from sqlmodel import Session

from src.domain.models.act import Act as ActDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActType, ActStatus, Act as ActORM
from src.infrastructure.repository.base_repository import BaseRepository


class ActRepository(BaseRepository[ActORM, ActDomain]):
    """
    Repozytorium do zarządzania encjami aktów prawnych.

    Klasa rozszerza BaseRepository i obsługuje konwersję między obiektami ORM (ActORM)
    a modelami domenowymi (ActDomain).
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium aktów prawnych.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, ActORM, ActDomain)

    @staticmethod
    def _get_by_identifier(session: Session, publisher: str, year: int, position: int) -> Optional[ActORM]:
        """
        Pobiera akt prawny na podstawie jego identyfikatora w obrębie istniejącej sesji.

        :param session: Sesja SQLAlchemy
        :param publisher: Kod wydawcy (np. 'DU')
        :param year: Rok publikacji
        :param position: Pozycja w publikacji
        :return: Obiekt ORM aktu prawnego, jeśli znaleziony, None w przeciwnym razie
        """
        return (
            session.query(ActORM)
            .filter(and_(ActORM.publisher == publisher, ActORM.year == year, ActORM.position == position))
            .first()
        )

    def get_by_identifier(self, publisher: str, year: int, position: int) -> Optional[ActDomain]:
        """
        Pobiera akt prawny na podstawie jego identyfikatora.

        :param publisher: Kod wydawcy (np. 'DU')
        :param year: Rok publikacji
        :param position: Pozycja w publikacji
        :return: Model domenowy aktu prawnego, który został pobrany z bazy danych
        """
        with self.db.session_scope() as session:
            act_orm = (
                session.query(ActORM)
                .filter(and_(ActORM.publisher == publisher, ActORM.year == year, ActORM.position == position))
                .filter(or_(is_(ActORM.archived, None), ActORM.archived == False))
                .first())
            return self._to_domain(act_orm) if act_orm else None

    def bulk_get_by_identifier(self, identifiers: List[Tuple[str, int, int]]) -> Dict[
        Tuple[str, int, int], Optional[ActDomain]]:
        """
        Pobiera wiele aktów prawnych na podstawie ich identyfikatorów w jednym zapytaniu.

        :param identifiers: Lista krotek (publisher, year, position) identyfikujących akty
        :return: Słownik mapujący identyfikatory na modele domenowe lub None dla nieznalezionych aktów
        """
        if not identifiers:
            return {}

        result = {}
        with self.db.session_scope() as session:
            # Buduj warunek OR dla każdego identyfikatora
            conditions = []
            for publisher, year, position in identifiers:
                conditions.append(
                    and_(
                        ActORM.publisher == publisher,
                        ActORM.year == year,
                        ActORM.position == position
                    )
                )

            # Wykonaj zapytanie z warunkiem OR
            query = session.query(ActORM).filter(or_(*conditions))
            found_acts = query.all()

            # Mapuj znalezione akty na słownik
            found_identifiers = set()
            for act_orm in found_acts:
                key = (act_orm.publisher, act_orm.year, act_orm.position)
                result[key] = self._to_domain(act_orm)
                found_identifiers.add(key)

            # Dla identyfikatorów, dla których nie znaleziono aktów, ustaw None
            for identifier in identifiers:
                if identifier not in found_identifiers:
                    result[identifier] = None

        return result

    def get_all(self) -> List[ActDomain]:
        """
        Pobiera wszystkie aktywne akty.

        :return: Lista aktów jako modele domenowe
        """
        with self.db.session_scope() as session:
            act_orms = (session
                        .query(ActORM)
                        .filter(or_(is_(ActORM.archived, None), ActORM.archived == False))
                        .all()
                        )
            return self._to_domain_list(act_orms)

    def get_count(self) -> int:
        """
        Pobiera liczbę aktywnych aktów.

        :return: Liczba aktywnych aktów
        """
        with self.db.session_scope() as session:
            return session.query(ActORM).filter(or_(is_(ActORM.archived, None), ActORM.archived == False)).count()

    def get_count_by_year(self) -> Dict[int, int]:
        """
        Pobiera liczbę aktywnych aktów pogrupowanych po roku.

        :return: Słownik z liczbą aktywnych aktów dla każdego roku {year: count}
        """
        with self.db.session_scope() as session:
            results = (
                session.query(ActORM.year, func.count(ActORM.id))
                .filter(or_(is_(ActORM.archived, None), ActORM.archived == False))
                .group_by(ActORM.year)
                .all()
            )
            return {year: count for year, count in results}

    def create(self, model: ActDomain) -> (ActDomain, bool):
        """
        Tworzy nowy akt prawny w bazie danych.

        Automatycznie uzupełnia type_id i status_id na podstawie pól type i status,
        jeśli nie zostały one dostarczone bezpośrednio.

        :param model: Model domenowy aktu prawnego do utworzenia
        :return: Krotka (model domenowy utworzonej encji, czy już był w DB)
        """
        with self.db.session_scope() as session:
            # Zwraca istniejący akt, jeśli już istnieje
            act_orm = self._get_by_identifier(session, model.publisher, model.year, model.position)
            if act_orm:
                return False, self._to_domain(act_orm)

            # Pobiera obiekty typu i statusu na podstawie tytułów
            type_obj = session.query(ActType).filter(ActType.title == model.type).first()
            status_obj = session.query(ActStatus).filter(ActStatus.title == model.status).first()

            act_orm = ActORM(
                publisher=model.publisher,
                year=model.year,
                position=model.position,
                title=model.title,
                type_id=type_obj.id,
                status_id=status_obj.id
            )

            session.add(act_orm)
            session.flush()
            session.refresh(act_orm)
            return True, self._to_domain(act_orm)
