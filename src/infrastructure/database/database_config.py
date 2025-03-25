# wersja: chet-theia
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """
    Konfiguracja połączenia do bazy danych Supabase.
    """
    host: str
    user: str
    password: str
    database: str
    port: str

    @property
    def connection_url(self) -> str:
        """
        Generuje URL połączenia do bazy danych.

        :return: Connection string dla SQLAlchemy
        """
        # DATABASE_URL =
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode=require"

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """
        Tworzy instancję konfiguracji ze zmiennych środowiskowych.

        Wymagane zmienne środowiskowe:
        - SUPABASE_HOST: Host bazy danych
        - SUPABASE_USER: Nazwa użytkownika
        - SUPABASE_PASSWORD: Hasło użytkownika
        - SUPABASE_DB: Nazwa bazy danych
        - SUPABASE_PORT: Port

        :return: Instancja DatabaseConfig
        :raises ValueError: Gdy, brakuje wymaganych zmiennych środowiskowych
        """
        env_vars = {
            "host": "SUPABASE_HOST",
            "user": "SUPABASE_USER",
            "password": "SUPABASE_PASSWORD",
            "database": "SUPABASE_DB",
            "port": "SUPABASE_PORT"
        }

        # Sprawdź, czy wszystkie wymagane zmienne są ustawione
        values = {field: os.getenv(env_name) for field, env_name in env_vars.items()}
        missing = [env_name for field, env_name in env_vars.items() if not values[field]]
        if missing:
            raise ValueError(f"Wymagane zmienne środowiskowe dla połączenia z bazą danych "
                             f"nie zostały określone ({', '.join(missing)}).")

        # Stwórz instancję z pobranymi wartościami
        return cls(**values)
