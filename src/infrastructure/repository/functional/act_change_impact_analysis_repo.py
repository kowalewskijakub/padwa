from typing import List

from src.core.models.act import ActChangeImpactAnalysis as ActChangeImpactAnalysisDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActChangeImpactAnalysis as ActChangeImpactAnalysisORM
from src.infrastructure.repository.base_repository import BaseRepository


class ActChangeImpactAnalysisRepository(BaseRepository[ActChangeImpactAnalysisORM, ActChangeImpactAnalysisDomain]):
    """
    Repozytorium do zarządzania analizami wpływu zmian w aktach prawnych na fragmenty dokumentów.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium analizy wpływu zmian.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, ActChangeImpactAnalysisORM, ActChangeImpactAnalysisDomain)

    def get_by_act_pair(self, changing_act_id: int, changed_act_id: int) -> List[ActChangeImpactAnalysisDomain]:
        """
        Pobiera analizy wpływu dla pary aktów prawnych.

        :param changing_act_id: ID aktu zmieniającego
        :param changed_act_id: ID aktu zmienianego
        """
        with self.db.session_scope() as session:
            results = (
                session.query(ActChangeImpactAnalysisORM)
                .filter(
                    ActChangeImpactAnalysisORM.changing_act_id == changing_act_id,
                    ActChangeImpactAnalysisORM.changed_act_id == changed_act_id
                )
                .all()
            )
            return self._to_domain_list(results)
