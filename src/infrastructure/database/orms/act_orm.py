"""Moduł modeli ORM dla aktów prawnych.

Zawiera modele dla aktów prawnych, ich typów, statusów, fragmentów,
klastery oraz analizy zmian.
"""

from typing import List, Optional, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped
from sqlmodel import Relationship, SQLModel, Field

from src.infrastructure.database.orms.base_orm import DictionaryBase, Base, ChunkClusterBase, ChunkBase
from src.presentation.app_config import AppConfig

_config = AppConfig.load()


class ActType(DictionaryBase, table=True):
    """Model reprezentujący typy aktów prawnych.
    
    :param acts: Relacja do aktów prawnych tego typu
    """
    acts: Mapped[List["Act"]] = Relationship(back_populates="type_obj")


class ActStatus(DictionaryBase, table=True):
    """Model reprezentujący status aktów prawnych.
    
    :param acts: Relacja do aktów prawnych o tym statusie
    """
    acts: Mapped[List["Act"]] = Relationship(back_populates="status_obj")


class ActChangeLink(SQLModel, table=True):
    """Model reprezentujący relację zmiany między aktami prawnymi.

    Przechowuje informację o tym, który akt zmienia który. Jeden akt może zmieniać
    wiele aktów i jeden akt może być zmieniany przez wiele aktów.

    :param changing_act_id: ID aktu zmieniającego
    :param changed_act_id: ID aktu zmienianego
    """
    changing_act_id: int = Field(foreign_key="act.id", primary_key=True)
    changed_act_id: int = Field(foreign_key="act.id", primary_key=True)


class ActChangeAnalysis(SQLModel, table=True):
    """Model reprezentujący analizę zmian między fragmentami aktów prawnych.
    
    :param id: Unikalny identyfikator analizy
    :param changing_act_id: ID aktu zmieniającego
    :param changed_act_id: ID aktu zmienianego
    :param changing_chunk_id: ID fragmentu aktu zmieniającego
    :param changed_chunk_id: ID fragmentu aktu zmienianego
    :param change_type: Typ zmiany ('modified', 'appended', 'removed')
    :param relevancy: Ocena relewatnoci zmiany
    :param justification: Uzasadnienie oceny
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    changing_act_id: int = Field(foreign_key="act.id")
    changed_act_id: int = Field(foreign_key="act.id")
    changing_chunk_id: Optional[int] = Field(default=None, foreign_key="actchunk.id")
    changed_chunk_id: Optional[int] = Field(default=None, foreign_key="actchunk.id")
    change_type: str  # 'modified', 'appended', 'removed'
    relevancy: float
    justification: str


class ActChangeImpactAnalysis(SQLModel, table=True):
    """Model reprezentujący analizę wpływu zmian na dokumenty.
    
    :param id: Unikalny identyfikator analizy wpływu
    :param changing_act_id: ID aktu zmieniającego
    :param changed_act_id: ID aktu zmienianego
    :param change_analysis_id: ID analizy zmiany
    :param doc_chunk_id: ID fragmentu dokumentu
    :param relevancy: Ocena relewatnoci wpływu
    :param justification: Uzasadnienie oceny wpływu
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    changing_act_id: int = Field(foreign_key="act.id")
    changed_act_id: int = Field(foreign_key="act.id")
    change_analysis_id: int = Field(foreign_key="actchangeanalysis.id")
    doc_chunk_id: int = Field(foreign_key="docchunk.id")
    relevancy: float
    justification: str


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

    summary: Optional[str] = None
    flag: Optional[bool] = None
    archived: Optional[bool] = None

    @property
    def type(self) -> Optional[str]:
        """Zwraca tytuł typu aktu prawnego.

        :return: Tytuł typu aktu lub None, jeśli relacja nie jest załadowana
        """
        return self.type_obj.title if self.type_obj else None

    @property
    def status(self) -> Optional[str]:
        """Zwraca tytuł statusu aktu prawnego.

        :return: Tytuł statusu aktu lub None, jeśli relacja nie jest załadowana
        """
        return self.status_obj.title if self.status_obj else None


class ActChunkClusterLink(SQLModel, table=True):
    """Model łączący klastry z fragmentami aktów (tabela pośrednia wielu-do-wielu).
    
    :param chunk_id: ID fragmentu aktu
    :param cluster_id: ID klastra
    """
    chunk_id: int = Field(foreign_key="actchunk.id", primary_key=True)
    cluster_id: int = Field(foreign_key="actchunkcluster.id", primary_key=True)


class ActChunk(ChunkBase, table=True):
    """Model reprezentujący fragmenty aktów prawnych.
    
    :param reference_id: Identyfikator aktu (mapowany jako act_id)
    :param _clusters: Relacja do klastrów fragmentów
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

    reference_id: int = Field(
        sa_column=Column("act_id", Integer, ForeignKey("act.id"))
    )
    parent_cluster_id: Optional[int] = Field(default=None, foreign_key="actchunkcluster.id")
    level: int = Field(default=0)

    text: Optional[str] = Field(sa_column=Column("summary", String, default=None))
    embedding: Optional[Any] = Field(
        sa_column=Column("summary_embedding", Vector(_config.embedding_vector_size), default=None)
    )
    flag: Optional[bool] = False

    parent_cluster: Optional["ActChunkCluster"] = Relationship(
        back_populates="child_clusters",
        sa_relationship_kwargs={"remote_side": "ActChunkCluster.id"}
    )
    child_clusters: Optional[List["ActChunkCluster"]] = Relationship(
        back_populates="parent_cluster",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    _chunks: Optional[List["ActChunk"]] = Relationship(
        back_populates="_clusters",
        link_model=ActChunkClusterLink
    )
