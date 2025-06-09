"""Moduł konfiguracji połączenia z bazą danych.

Zawiera klasę DatabaseConfig służącą do zarządzania parametrami połączenia
z bazą danych Supabase i generowania connection string.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Konfiguracja połączenia do bazy danych Supabase.
    
    :param host: Adres hosta bazy danych
    :param user: Nazwa użytkownika
    :param password: Hasło użytkownika
    :param database: Nazwa bazy danych
    :param port: Port połączenia
    """
    host: str
    user: str
    password: str
    database: str
    port: str

    @property
    def connection_url(self) -> str:
        """Generuje URL połączenia do bazy danych.

        :return: Connection string dla SQLAlchemy
        """
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode=require"

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Tworzy instancję konfiguracji ze zmiennych środowiskowych.

        Wymagane zmienne środowiskowe:
        - SUPABASE_HOST: Host bazy danych
        - SUPABASE_USER: Nazwa użytkownika
        - SUPABASE_PASSWORD: Hasło użytkownika
        - SUPABASE_DB: Nazwa bazy danych
        - SUPABASE_PORT: Port

        :return: Instancja DatabaseConfig
        :raises ValueError: Gdy brakuje wymaganych zmiennych środowiskowych
        """
        env_vars = {
            "host": "SUPABASE_HOST",
            "user": "SUPABASE_USER",
            "password": "SUPABASE_PASSWORD",
            "database": "SUPABASE_DB",
            "port": "SUPABASE_PORT"
        }

        values = {field: os.getenv(env_name) for field, env_name in env_vars.items()}
        missing = [env_name for field, env_name in env_vars.items() if not values[field]]
        if missing:
            raise ValueError(f"Wymagane zmienne środowiskowe dla połączenia z bazą danych "
                             f"nie zostały określone ({', '.join(missing)}).")

        return cls(**values)
