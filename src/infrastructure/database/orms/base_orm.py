from typing import Optional, List

from pgvector.sqlalchemy import Vector
from sqlmodel import SQLModel, Field

from src.presentation.app_config import AppConfig

_config = AppConfig.load()


class Base(SQLModel, table=False):
    """
    Klasa bazowa modelu.
    """
    id: Optional[int] = Field(default=None, primary_key=True)


class DictionaryBase(Base, table=False):
    """
    Model bazowy dla reprezentacji słowników.
    """
    title: str


class EmbeddableBase(Base, table=False):
    """
    Model bazowy dla reprezentacji obiektów z możliwością osadzania wektorów.
    """
    text: Optional[str]
    embedding: Optional[List[float]] = Field(sa_type=Vector(_config.embedding_vector_size))


class ChunkBase(EmbeddableBase, table=False):
    """
    Model bazowy dla reprezentacji fragmentów (chunków).
    """
    reference_id: Optional[int] = None


class ChunkClusterBase(EmbeddableBase, table=False):
    """
    Model bazowy dla reprezentacji klastrów fragmentów.
    """
    reference_id: Optional[int] = None
    parent_cluster_id: Optional[int] = None
    level: int = 0
