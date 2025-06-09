"""
Niestandardowe wyjątki aplikacji PADWA-C.

Zawiera hierarchię klas wyjątków używanych w całej aplikacji
do obsługi różnych typów błędów i sytuacji wyjątkowych.
"""


class ApplicationError(Exception):
    """
    Klasa bazowa dla wszystkich błędów w aplikacji.
    
    Wszystkie niestandardowe wyjątki w aplikacji dziedziczą z tej klasy
    dla ujednolicenia obsługi błędów.
    """


class DatabaseError(ApplicationError):
    """
    Wyjątek wywoływany przy problemach z bazą danych.
    
    Klasa bazowa dla wszystkich błędów związanych z operacjami
    na bazie danych, połączeniami i sesjami.
    """


class ConnectionError(DatabaseError):
    """
    Wyjątek wywoływany przy problemach z połączeniem z bazą danych.
    
    Występuje gdy nie można nawiązać połączenia lub gdy połączenie
    zostanie nieoczekiwanie przerwane.
    """


class SessionError(DatabaseError):
    """
    Wyjątek wywoływany przy problemach z sesją bazy danych.
    
    Obejmuje błędy zarządzania sesjami SQLAlchemy, transakcjami
    i operacjami commit/rollback.
    """


class RepositoryError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z repozytoriami.
    
    Obejmuje wszystkie błędy występujące w warstwie dostępu do danych,
    w tym operacje CRUD i mapowanie encji.
    """


class EntityNotFoundError(RepositoryError):
    """
    Wyjątek wywoływany gdy nie można znaleźć żądanej encji.
    
    Występuje przy próbie pobrania encji po ID lub innych kryteriach,
    gdy encja nie istnieje w bazie danych.
    """


class UtilityError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z narzędziami pomocniczymi.
    
    Obejmuje błędy w modułach utility, przetwarzaniu tekstu
    i innych operacjach wspierających.
    """


class TextProcessingError(UtilityError):
    """
    Wyjątek wywoływany przy problemach z przetwarzaniem tekstu.
    
    Obejmuje błędy parsowania plików PDF, ekstrakcji tekstu,
    podziału na fragmenty i czyszczenia tekstu.
    """


class APIError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z API.
    
    Obejmuje błędy komunikacji z zewnętrznymi API, timeout,
    nieprawidłowe odpowiedzi i problemy z autoryzacją.
    """


class ServiceError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z serwisami.
    
    Obejmuje błędy w warstwie serwisów biznesowych,
    logice domenowej i orkiestracji operacji.
    """


class EmbeddingError(ServiceError):
    """
    Wyjątek wywoływany przy problemach z generowaniem embeddingów.
    
    Występuje gdy nie można wygenerować wektorów embeddingów
    dla tekstu przy użyciu modeli OpenAI lub innych dostawców.
    """
