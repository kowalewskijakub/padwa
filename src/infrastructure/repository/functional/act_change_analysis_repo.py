from typing import List

from sqlalchemy.orm import aliased

from src.core.models.act import ActChangeAnalysis as ActChangeAnalysisDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActChangeAnalysis as ActChangeAnalysisORM, ActChunk as ActChunkORM
from src.infrastructure.repository.base_repository import BaseRepository


class ActChangeAnalysisRepository(BaseRepository[ActChangeAnalysisORM, ActChangeAnalysisDomain]):
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium analizy zmian aktów prawnych.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, ActChangeAnalysisORM, ActChangeAnalysisDomain)

    def get_by_act_pair(self, changing_act_id: int, changed_act_id: int) -> List[ActChangeAnalysisDomain]:
        with self.db.session_scope() as session:
            results = (
                session.query(ActChangeAnalysisORM)
                .filter(
                    ActChangeAnalysisORM.changing_act_id == changing_act_id,
                    ActChangeAnalysisORM.changed_act_id == changed_act_id
                )
                .all()
            )
            return self._to_domain_list(results)

    def get_by_act_pair_with_texts(self, changing_act_id: int, changed_act_id: int) -> List[ActChangeAnalysisDomain]:
        """
        Pobiera analizy zmian dla par aktów prawnych, dołączając teksty fragmentów.
        :param changing_act_id: ID aktu zmieniającego
        :param changed_act_id: ID aktu zmienianego
        :return: Lista analiz zmian z tekstami fragmentów
        """
        with self.db.session_scope() as session:
            changing_chunk = aliased(ActChunkORM, name='changing_chunk')
            changed_chunk = aliased(ActChunkORM, name='changed_chunk')

            query = (
                session.query(ActChangeAnalysisORM)
                .outerjoin(changing_chunk, ActChangeAnalysisORM.changing_chunk_id == changing_chunk.id)
                .outerjoin(changed_chunk, ActChangeAnalysisORM.changed_chunk_id == changed_chunk.id)
                .filter(
                    ActChangeAnalysisORM.changing_act_id == changing_act_id,
                    ActChangeAnalysisORM.changed_act_id == changed_act_id
                )
                .add_columns(
                    changing_chunk.text.label('changing_chunk_text'),
                    changed_chunk.text.label('changed_chunk_text')
                )
            )

            results = query.all()
            analyses = []

            for row in results:
                analysis_orm, changing_text, changed_text = row
                analysis_domain = self._to_domain(analysis_orm)
                analysis_domain.changing_chunk_text = changing_text
                analysis_domain.changed_chunk_text = changed_text
                analyses.append(analysis_domain)

            return analyses
