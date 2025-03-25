from typing import List

from src.common.logging_configurator import get_logger
from src.domain.models.act import ActChunkCluster as ActChunkClusterDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActChunkCluster as ActChunkClusterORM, ActChunkClusterLink, \
    ActChunk as ActChunkORM
from src.infrastructure.repository.embeddable.embeddable_base_repository import EmbeddableBaseRepository

_logger = get_logger()


class ActChunkClusterRepository(EmbeddableBaseRepository[ActChunkClusterORM, ActChunkClusterDomain]):
    """
    Repozytorium do zarządzania klastrami fragmentów aktów prawnych.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium klastrów.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, ActChunkClusterORM, ActChunkClusterDomain)

    def bulk_create(self, models: List[ActChunkClusterDomain]) -> List[ActChunkClusterDomain]:
        """
        Tworzy wiele nowych klastrów w bazie danych wraz z ich powiązaniami.

        Metoda rozszerza standardowe bulk_create, aby obsłużyć relacje między klastrami a fragmentami
        określone przez pole chunks w modelu domenowym.

        :param models: Lista modeli domenowych klastrów do utworzenia
        :return: Lista modeli domenowych utworzonych klastrów
        """
        with self.db.session_scope() as session:
            created_clusters = []

            for model in models:
                cluster_orm = ActChunkClusterORM(
                    reference_id=model.reference_id,
                    parent_cluster_id=model.parent_cluster_id,
                    level=model.level,
                    text=model.text,
                    embedding=model.embedding,
                    flag=model.flag
                )
                session.add(cluster_orm)
                session.flush()  # Flush to get the ID

                # Powiązanie zależy od poziomu klastra
                if model.level == 0 and model.chunks:
                    # Poziom 0: powiąż z rzeczywistymi fragmentami (ActChunk)
                    self._link_with_chunks(session, cluster_orm.id, model.chunks)
                    _logger.info(
                        f"Utworzono klaster poziomu 0 (ID: {cluster_orm.id}) z {len(model.chunks)} fragmentami")

                created_clusters.append(cluster_orm)

            # Upewnij się, że wszystko jest zapisane
            session.flush()

            # Konwertuj na modele domenowe i zwróć
            return self._to_domain_list(created_clusters)

    @staticmethod
    def _link_with_chunks(session, cluster_id: int, chunks: List):
        """
        Tworzy powiązania między klastrem a fragmentami.

        :param session: Sesja bazodanowa
        :param cluster_id: ID klastra
        :param chunks: Lista fragmentów do powiązania
        """
        for chunk in chunks:
            if not hasattr(chunk, 'id') or chunk.id is None:
                _logger.warning(f"Pominięto fragment bez ID przy tworzeniu powiązań z klastrem {cluster_id}")
                continue

            # Sprawdź czy fragment istnieje w bazie
            existing_chunk = session.query(ActChunkORM).get(chunk.id)
            if not existing_chunk:
                _logger.warning(f"Fragment o ID {chunk.id} nie istnieje w bazie danych")
                continue

            link = ActChunkClusterLink(cluster_id=cluster_id, chunk_id=chunk.id)
            session.add(link)
