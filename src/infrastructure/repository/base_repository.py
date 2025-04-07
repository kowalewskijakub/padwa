# wersja: chet-theia
from abc import ABC
from typing import TypeVar, Generic, List, Optional, Any, Type

from sqlalchemy.orm import Session

from src.common.exceptions import EntityNotFoundError
from src.common.logging_configurator import get_logger
from src.infrastructure.database.database_manager import DatabaseManager

TORM = TypeVar('TORM')
TDomain = TypeVar('TDomain')

_logger = get_logger()


class BaseRepository(ABC, Generic[TORM, TDomain]):
    """
    Abstrakcyjna klasa bazowa dla repozytoriów.

    Dostarcza podstawowe metody i strukturę dla repozytoriów, które zarządzają
    encjami w bazie danych i automatycznie konwertują je na modele domenowe.
    """

    def __init__(self, db_manager: DatabaseManager, orm_class: Type[TORM], domain_class: Type[TDomain]):
        """
        Inicjalizuje repozytorium.

        :param db_manager: Instancja DatabaseManager
        :param orm_class: Klasa ORM, której dotyczy zadane repozytorium
        :param domain_class: Klasa domeny, której dotyczy zadane repozytorium
        """
        self.db = db_manager
        self.orm_class = orm_class
        self.domain_class = domain_class

    def _to_domain(self, orm_obj: TORM) -> TDomain:
        """
        Konwertuje obiekt ORM na model domenowy.

        :param orm_obj: Obiekt ORM do konwersji
        :return: Model domenowy lub None, jeśli orm_obj to None
        """
        return self.domain_class.model_validate(orm_obj)

    def _to_domain_list(self, orm_objs: List[TORM]) -> List[TDomain]:
        """
        Konwertuje listę obiektów ORM na listę modeli domenowych.

        :param orm_objs: Lista obiektów ORM do konwersji
        :return: Lista modeli domenowych
        """
        return [self._to_domain(orm_obj) for orm_obj in orm_objs]

    def _to_orm(self, domain_obj: TDomain) -> TORM:
        """
        Konwertuje obiekt domenowy na model ORM.

        :param domain_obj: Obiekt domenowy do konwersji
        :return: Model ORM lub None, jeśli domain_obj to None
        """
        return self.orm_class.model_validate(domain_obj)

    def _to_orm_list(self, domain_objs: List[TDomain]) -> List[TORM]:
        """
        Konwertuje listę obiektów domenowych na listę modeli ORM.

        :param domain_objs: Lista obiektów domenowych do konwersji
        :return: Lista modeli ORM
        """
        return [self._to_orm(domain_obj) for domain_obj in domain_objs]

    def _get_by_id(self, session: Session, entity_id: Any) -> Optional[TORM]:
        """
        Pobiera encję na podstawie jej klucza głównego w obrębie istniejącej sesji.

        :param session: Sesja SQLAlchemy
        :param entity_id: ID klucza głównego encji
        :return: Obiekt encji ORM, jeśli znaleziony, None w przeciwnym razie
        """
        return session.query(self.orm_class).get(entity_id)

    def bulk_get_by_ids(self, entity_ids: List[Any]) -> List[TDomain]:
        """
        Pobiera wiele encji na podstawie ich identyfikatorów w jednym zapytaniu.

        :param entity_ids: Lista identyfikatorów encji
        :return: Lista modeli domenowych odpowiadających podanym identyfikatorom
        """
        if not entity_ids:
            return []

        with self.db.session_scope() as session:
            orm_objs = (
                session.query(self.orm_class)
                .filter(self.orm_class.id.in_(entity_ids))
                .all()
            )
            return self._to_domain_list(orm_objs)

    def get_by_id(self, entity_id: Any) -> Optional[TDomain]:
        """
        Pobiera encję na podstawie jej klucza głównego (ID).

        :param entity_id: ID klucza głównego encji
        :return: Obiekt modelu domenowego, jeśli znaleziony, None w przeciwnym razie
        """
        with self.db.session_scope() as session:
            orm_obj = self._get_by_id(session, entity_id)
            return self._to_domain(orm_obj)

    def get_all(self) -> List[TDomain]:
        """
        Pobiera wszystkie encje tego typu.

        :return: Lista wszystkich encji jako modele domenowe
        """
        with self.db.session_scope() as session:
            orm_objs = session.query(self.orm_class).all()
            return self._to_domain_list(orm_objs)

    def bulk_create(self, models: List[TDomain]) -> List[TDomain]:
        """
        Tworzy wiele nowych encji w bazie danych.

        :param models: Lista modeli domenowych do utworzenia
        :return: Lista modeli domenowych utworzonych encji
        """
        orm_objs = self._to_orm_list(models)

        with self.db.session_scope() as session:
            session.bulk_save_objects(orm_objs)
            session.flush()  # Zapewnia wygenerowanie ID
            return self._to_domain_list(orm_objs)

    def create(self, model: TDomain) -> TDomain:
        """
        Tworzy nową encję w bazie danych.

        :param model: Model domenowy do utworzenia
        :return: Model domenowy utworzonej encji
        """
        # Konwertuj model domenowy na model ORM
        orm_obj = self._to_orm(model)

        with self.db.session_scope() as session:
            session.add(orm_obj)
            session.flush()  # Zapewnia wygenerowanie ID
            session.refresh(orm_obj)
            return self._to_domain(orm_obj)

    def bulk_update(self, models: List[TORM]) -> List[TDomain]:
        """
        Aktualizuje wiele encji naraz.

        Metoda wykrywa ID encji z dostarczonych modeli, pobiera ich aktualne wersje z bazy danych,
        aktualizuje ich atrybuty i zapisuje zmiany. Encje, których nie można znaleźć, są pomijane.

        :param models: Lista modeli ORM do aktualizacji
        :return: Lista zaktualizowanych modeli domenowych
        """
        if not models:
            return []

        updated_models = []

        with self.db.session_scope() as session:
            for model in models:
                if not hasattr(model, 'id') or model.id is None:
                    _logger.warning(f"Pominięto model bez atrybutu 'id' podczas masowej aktualizacji")
                    continue

                entity = self._get_by_id(session, model.id)
                if not entity:
                    _logger.warning(f"Nie znaleziono encji o ID={model.id} podczas masowej aktualizacji")
                    continue

                # Aktualizacja atrybutów
                for attr_name, attr_value in vars(model).items():
                    if attr_name != 'id':
                        setattr(entity, attr_name, attr_value)
                updated_models.append(entity)

            session.flush()
            return self._to_domain_list(updated_models)

    def update(self, model: TDomain) -> TDomain:
        """
        Aktualizuje encję na podstawie dostarczonego modelu domenowego.

        Metoda wykrywa ID encji z dostarczonego modelu, pobiera aktualną wersję z bazy danych,
        aktualizuje jej atrybuty i zapisuje zmiany.

        :param model: Model domenowy z zaktualizowanymi wartościami
        :return: Model domenowy zaktualizowanej encji
        :raises EntityNotFoundError: Gdy, encja o podanym ID nie istnieje
        :raises ValueError: Gdy, model nie ma atrybutu 'id'
        """
        if not hasattr(model, 'id') or model.id is None:
            raise ValueError("Model musi zawierać atrybut 'id' z poprawną wartością")

        with self.db.session_scope() as session:
            entity_id = model.id
            entity = self._get_by_id(session, entity_id)

            if not entity:
                raise EntityNotFoundError(entity_id)

            # Zaktualizuj atrybuty encji ORM na podstawie dostarczonego modelu
            for attr_name, attr_value in vars(model).items():
                # Zawsze pomiń 'id'
                if attr_name == 'id':
                    continue

                try:
                    # Sprawdź, czy atrybut jest właściwością (property)
                    if hasattr(entity.__class__, attr_name):
                        attr_descriptor = getattr(entity.__class__, attr_name)
                        if isinstance(attr_descriptor, property):
                            # Sprawdź, czy właściwość ma setter
                            if attr_descriptor.fset is None:
                                _logger.debug(f"Pominięto właściwość '{attr_name}' bez settera podczas aktualizacji")
                                continue

                    # Ustaw atrybut
                    setattr(entity, attr_name, attr_value)
                except Exception as e:
                    _logger.warning(f"Nie można ustawić atrybutu '{attr_name}': {str(e)}")

            session.flush()
            return self._to_domain(entity)
