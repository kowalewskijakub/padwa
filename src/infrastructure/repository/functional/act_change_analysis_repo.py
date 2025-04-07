from typing import List


from src.core.models.act import ActChangeAnalysis as ActChangeAnalysisDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActChangeAnalysis as ActChangeAnalysisORM
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