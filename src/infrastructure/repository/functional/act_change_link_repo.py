# wersja: chet-theia
from src.core.models.act import ActChangeLink as ActChangeLinkDomain
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.orms.act_orm import ActChangeLink as ActChangeLinkORM
from src.infrastructure.repository.base_repository import BaseRepository


class ActChangeLinkRepository(BaseRepository[ActChangeLinkORM, ActChangeLinkDomain]):
    """
    Repozytorium do zarządzania relacjami zmian między aktami prawnymi.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium relacji zmian aktów prawnych.

        :param db_manager: Menedżer bazy danych
        """
        super().__init__(db_manager, ActChangeLinkORM, ActChangeLinkDomain)

    def get_changing_acts(self, changed_act_id: int) -> list[int]:
        """
        Pobiera ID aktów, które zmieniają dany akt.

        :param changed_act_id: ID aktu zmienianego
        :return: Lista ID aktów zmieniających
        """
        with self.db.session_scope() as session:
            results = (
                session.query(ActChangeLinkORM.changing_act_id)
                .filter(ActChangeLinkORM.changed_act_id == changed_act_id)
                .all()
            )
            return [r[0] for r in results]

    def get_changed_acts(self, changing_act_id: int) -> list[int]:
        """
        Pobiera ID aktów, które są zmieniane przez dany akt.

        :param changing_act_id: ID aktu zmieniającego
        :return: Lista ID aktów zmienianych
        """
        with self.db.session_scope() as session:
            results = (
                session.query(ActChangeLinkORM.changed_act_id)
                .filter(ActChangeLinkORM.changing_act_id == changing_act_id)
                .all()
            )
            return [r[0] for r in results]
