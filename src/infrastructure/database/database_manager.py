"""Moduł menedżera bazy danych.

Zawiera klasę DatabaseManager odpowiedzialną za zarządzanie połączeniami z bazą danych,
inicjalizację schematu, aktualizację słowników i zarządzanie sesjami.
"""

from contextlib import contextmanager
from typing import Generator, Dict, Type, Any

from sqlmodel import create_engine, Session, SQLModel

from src.common.exceptions import ConnectionError, SessionError, DatabaseError
from src.common.logging_configurator import get_logger
from src.infrastructure.database.database_config import DatabaseConfig
from src.infrastructure.database.orms.base_orm import DictionaryBase

_logger = get_logger()
_db_connection_string = DatabaseConfig.from_env().connection_url


class DatabaseManager:
    """Menedżer bazy danych odpowiedzialny za zarządzanie połączeniami i sesjami.
    
    Zapewnia funkcjonalności inicjalizacji bazy danych, aktualizacji słowników,
    zarządzania sesjami oraz pool-u połączeń.
    """

    def __init__(self, pool_size: int = 20, max_overflow: int = 10):
        """Inicjalizuje menedżera bazy danych.

        :param pool_size: Liczba połączeń do utrzymywania otwartych
        :param max_overflow: Maksymalna liczba połączeń do otwarcia poza pool_size
        :raises ConnectionError: Gdy nie udało się nawiązać połączenia z bazą danych
        """

        try:
            self._engine = create_engine(
                _db_connection_string,
                pool_size=pool_size,
                max_overflow=max_overflow
            )
            _logger.info("Połączenie z bazą danych zostało zainicjalizowane.")
        except Exception:
            raise ConnectionError(f"Połączenie z bazą danych nie zostało zainicjalizowane.")

    def initialize_database(self) -> None:
        """Inicjalizuje bazę danych na podstawie zdefiniowanych modeli SQLModel.

        Funkcja wykorzystuje metadane modeli SQLModel do automatycznego tworzenia
        odpowiednich tabel w bazie danych.

        :raises DatabaseError: Gdy inicjalizacja bazy danych się nie powiedzie
        """
        try:
            SQLModel.metadata.create_all(self._engine)
            _logger.info("Schemat bazy danych został pomyślnie zainicjalizowany.")
        except Exception as e:
            raise DatabaseError(f"Inicjalizacja bazy danych nie powiodła się: {str(e)}")

    def update_dictionaries(self, dictionaries: Dict[Type[DictionaryBase], list[str]]) -> Dict[str, int]:
        """Aktualizuje tabele słownikowe, dodając brakujące wpisy.

        :param dictionaries: Słownik, gdzie kluczem jest klasa słownikowa (np. ActType, ActStatus),
                             a wartością lista tytułów do dodania
        :return: Słownik z liczbą dodanych wpisów dla każdej tabeli
        :raises DatabaseError: Gdy aktualizacja słowników nie powiedzie się
        """
        try:
            results = {}

            for model_class, titles in dictionaries.items():
                added_count = 0
                with self.session_scope() as session:
                    existing_titles = set(row.title for row in session.query(model_class.title).all())
                    for title in titles:
                        if title and title not in existing_titles:
                            session.add(model_class(title=title))
                            added_count += 1

                results[model_class.__name__] = added_count
                _logger.info(f"Zaktualizowano słownik {model_class.__name__}: dodano {added_count} wpisów")

            return results
        except Exception as e:
            raise DatabaseError(f"Aktualizacja słowników nie powiodła się: {str(e)}")

    def get_session(self) -> Session:
        """Tworzy nową sesję bazy danych.

        :return: Obiekt sesji SQLModel
        :raises SessionError: Gdy nie udało się utworzyć sesji
        """
        try:
            return Session(self._engine)
        except Exception as e:
            raise SessionError(f"Sesja z bazą danych nie została utworzona.")

    @contextmanager
    def session_scope(self) -> Generator[Session, Any, None]:
        """Obsługuje sesję bazy danych w bloku with.
        
        Zapewnia automatyczne commit i rollback operacji w przypadku błędów.
        
        :return: Generator sesji SQLModel
        :raises SessionError: Gdy sesja nie została zatwierdzona
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise SessionError(f"Sesja z bazą danych nie została zatwierdzona. {str(e)}")
        finally:
            session.close()

    def dispose(self) -> None:
        """Zamyka wszystkie połączenia z bazą danych.
        
        :raises DatabaseError: Gdy nie udało się zamknąć połączeń
        """
        try:
            self._engine.dispose()
            _logger.info("Połączenie z bazą danych zostało zamknięte.")
        except Exception as e:
            raise DatabaseError(f"Połączenie z bazą danych nie zostało zamknięte.")
