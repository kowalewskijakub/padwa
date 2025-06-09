"""Moduł z klasami bazowymi ORM.

Zawiera klasy bazowe dla wszystkich modeli w aplikacji, w tym modele
z obsługą wektorów i fragmentów tekstu.
"""

from typing import Optional, List

from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field

from src.presentation.app_config import AppConfig

_config = AppConfig.load()


class Base(SQLModel, table=False):
    """Klasa bazowa modelu.
    
    :param id: Unikalny identyfikator encji
    """
    id: Optional[int] = Field(default=None, primary_key=True)


class DictionaryBase(Base, table=False):
    """Model bazowy dla reprezentacji słowników.
    
    :param title: Tytuł elementu słownikowego
    """
    title: str


class EmbeddableBase(Base, table=False):
    """Model bazowy dla reprezentacji obiektów z możliwością osadzania wektorów.
    
    :param text: Tekst do osadzenia wektorowego
    :param embedding: Wektor reprezentujący tekst w przestrzeni embeddingu
    """
    text: Optional[str]
    embedding: Optional[List[float]] = Field(sa_type=Vector(_config.embedding_vector_size))


class ChunkBase(EmbeddableBase, table=False):
    """Model bazowy dla reprezentacji fragmentów (chunków).
    
    :param reference_id: Identyfikator obiektu referencyjnego (akt/dokument)
    """
    reference_id: Optional[int] = None


class ChunkClusterBase(EmbeddableBase, table=False):
    """Model bazowy dla reprezentacji klastrów fragmentów.
    
    :param reference_id: Identyfikator obiektu referencyjnego
    :param parent_cluster_id: Identyfikator klastra nadrzędnego
    :param level: Poziom w hierarchii klastrów
    """
    reference_id: Optional[int] = None
    parent_cluster_id: Optional[int] = None
    level: int = 0
