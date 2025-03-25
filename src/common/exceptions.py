class ApplicationError(Exception):
    """
    Klasa bazowa dla wszystkich błędów w aplikacji.
    """


class DatabaseError(ApplicationError):
    """
    Wywoływany, gdy występują problemy z bazą danych.
    """
    pass


class ConnectionError(DatabaseError):
    """
    Wywoływany, gdy występują problemy z połączeniem z bazą danych.
    """
    pass


class SessionError(DatabaseError):
    """
    Wywoływany, gdy występują problemy z sesją bazy danych.
    """
    pass


class RepositoryError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z repozytoriami.
    """


class EntityNotFoundError(RepositoryError):
    pass


class UtilityError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z narzędziami pomocniczymi.
    """
    pass


class TextProcessingError(UtilityError):
    """
    Wywoływany, gdy występują problemy z przetwarzaniem plików PDF.
    """
    pass


class APIError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z API.
    """
    pass


class ServiceError(ApplicationError):
    """
    Klasa bazowa dla błędów związanych z serwisami.
    """
    pass


class EmbeddingError(ServiceError):
    pass
