from typing import List, Optional, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped
from sqlmodel import Relationship, SQLModel, Field

from src.infrastructure.database.orms.base_orm import DictionaryBase, Base, ChunkClusterBase, ChunkBase
from src.presentation.app_config import AppConfig

_config = AppConfig.load()


class ActType(DictionaryBase, table=True):
    """
    Model reprezentujący typy aktów prawnych.
    """
    acts: Mapped[List["Act"]] = Relationship(back_populates="type_obj")


class ActStatus(DictionaryBase, table=True):
    """
    Model reprezentujący status aktów prawnych.
    """
    acts: Mapped[List["Act"]] = Relationship(back_populates="status_obj")


class ActChangeLink(SQLModel, table=True):
    """
    Model reprezentujący relację zmiany między aktami prawnymi.

    Przechowuje informację o tym, który akt zmienia który. Jeden akt może zmieniać
    wiele aktów i jeden akt może być zmieniany przez wiele aktów.

    :param changing_act_id: ID aktu zmieniającego
    :param changed_act_id: ID aktu zmienianego
    """
    changing_act_id: int = Field(foreign_key="act.id", primary_key=True)
    changed_act_id: int = Field(foreign_key="act.id", primary_key=True)


class Act(Base, table=True):
    """
    Model reprezentujący akty prawne.

    :param id: Unikalny identyfikator aktu
    :param publisher: Wydawca aktu
    :param year: Rok wydania
    :param position: Pozycja aktu
    :param title: Tytuł aktu
    :param type_id: Identyfikator typu aktu
    :param type_obj: Relacja do obiektu typu aktu
    :param status_id: Identyfikator statusu aktu
    :param status_obj: Relacja do obiektu statusu aktu
    :param summary: Podsumowanie aktu
    :param flag: Flaga aktu
    :param archived: Czy akt jest zarchiwizowany
    """
    # Pola podstawowe
    publisher: str
    year: int
    position: int
    title: str

    type_id: int = Field(foreign_key="acttype.id")
    type_obj: Optional[ActType] = Relationship(
        back_populates="acts",
        sa_relationship_kwargs={"lazy": "joined"}  # Wczytuje obiekt w jednym zapytaniu
    )
    status_id: int = Field(foreign_key="actstatus.id")
    status_obj: Optional[ActStatus] = Relationship(
        back_populates="acts",
        sa_relationship_kwargs={"lazy": "joined"}  # Wczytuje obiekt w jednym zapytaniu
    )

    # Pola generowane w wyniku przetworzenia
    summary: Optional[str] = None
    flag: Optional[bool] = None
    archived: Optional[bool] = None

    @property
    def type(self) -> Optional[str]:
        """
        Zwraca tytuł typu aktu prawnego.

        :return: Tytuł typu aktu lub None, jeśli relacja nie jest załadowana
        """
        return self.type_obj.title if self.type_obj else None

    @property
    def status(self) -> Optional[str]:
        """
        Zwraca tytuł statusu aktu prawnego.

        :return: Tytuł statusu aktu lub None, jeśli relacja nie jest załadowana
        """
        return self.status_obj.title if self.status_obj else None


class ActChunkClusterLink(SQLModel, table=True):
    """
    Model łączący klastry z fragmentami aktów (tabela pośrednia wielu-do-wielu).
    """
    chunk_id: int = Field(foreign_key="actchunk.id", primary_key=True)
    cluster_id: int = Field(foreign_key="actchunkcluster.id", primary_key=True)


class ActChunk(ChunkBase, table=True):
    """
    Model reprezentujący fragmenty aktów prawnych.
    """
    reference_id: int = Field(
        sa_column=Column("act_id", Integer, ForeignKey("act.id"))
    )
    _clusters: Optional[List["ActChunkCluster"]] = Relationship(back_populates="_chunks",
                                                                link_model=ActChunkClusterLink)


class ActChunkCluster(ChunkClusterBase, table=True):
    """
    Model reprezentujący klaster fragmentów aktu prawnego.

    :param id: Unikalny identyfikator klastra
    :param act_id: Identyfikator aktu prawnego
    :param parent_cluster_id: Identyfikator klastra nadrzędnego (dla hierarchii)
    :param level: Poziom w hierarchii rekurencyjnej (0 dla podstawowych)
    :param summary: Podsumowanie klastra
    :param flag: Flaga wskazująca na nieistotność klastra
    """

    # Workaround dla aliasu ze względu na problem z biblioteką SQLModel (issue #725)
    reference_id: int = Field(
        sa_column=Column("act_id", Integer, ForeignKey("act.id"))
    )
    parent_cluster_id: Optional[int] = Field(default=None, foreign_key="actchunkcluster.id")
    level: int = Field(default=0)

    # Pola generowane w wyniku przetworzenia
    text: Optional[str] = Field(sa_column=Column("summary", String, default=None))
    embedding: Optional[Any] = Field(
        sa_column=Column("summary_embedding", Vector(_config.embedding_vector_size), default=None)
    )
    flag: Optional[bool] = False

    # Relacje
    parent_cluster: Optional["ActChunkCluster"] = Relationship(
        back_populates="child_clusters",
        sa_relationship_kwargs={"remote_side": "ActChunkCluster.id"}
    )
    child_clusters: Optional[List["ActChunkCluster"]] = Relationship(
        back_populates="parent_cluster",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Relacja many-to-many z fragmentami aktów
    _chunks: Optional[List["ActChunk"]] = Relationship(
        back_populates="_clusters",
        link_model=ActChunkClusterLink
    )
