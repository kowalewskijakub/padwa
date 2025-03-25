# wersja: chet-theia
from typing import List

from src.application.dtos.act_dto import ActProcessedDTO, ActChunkDTO, ActApiDTO, ConsolidationActDTO
from src.application.services.clusters_service import ClustersService
from src.common.exceptions import EntityNotFoundError
from src.domain.models.act import Act, ActChunk, ActChangeLink
from src.infrastructure.api.eli_api_client import ELIApiClient
from src.infrastructure.processing.embedding.embedding_handler import EmbeddingHandler
from src.infrastructure.processing.embedding.embedding_semantic_clusterer import EmbeddingSemanticClusterer
from src.infrastructure.processing.text.text_processor import get_act_processors, TextProcessor
from src.infrastructure.repository.core.act_repository import ActRepository
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository
from src.infrastructure.repository.functional.act_change_link_repo import ActChangeLinkRepository


class ActsService:

    def __init__(
            self,
            api_client: ELIApiClient,
            act_repo: ActRepository,
            act_chunk_repo: ActChunkRepository,
            act_change_link_repo: ActChangeLinkRepository,
            embedding_handler: EmbeddingHandler,
            embedding_semantic_clusterer: EmbeddingSemanticClusterer,
            cluster_orchestrator: ClustersService,
    ):
        """
        Inicjalizuje serwis aktów prawnych.

        :param api_client: Klient API do pobierania aktów prawnych
        :param act_repo: Repozytorium do zarządzania aktami
        :param act_chunk_repo: Repozytorium do zarządzania fragmentami aktów
        :param act_change_link_repo: Repozytorium do zarządzania relacjami zmian aktów
        :param embedding_handler: Serwis do zarządzania embedingami
        :param embedding_semantic_clusterer: Serwis do grupowania semantycznego
        :param cluster_orchestrator: Orchestrator klastrów
        """
        self.api_client = api_client
        self.act_repo = act_repo
        self.act_chunk_repo = act_chunk_repo
        self.act_change_link_repo = act_change_link_repo
        self.embedding_handler = embedding_handler
        self.embedding_semantic_clusterer = embedding_semantic_clusterer
        self.cluster_orchestrator = cluster_orchestrator

    def get_by_identifier(self, publisher: str, year: int, position: int) -> ActApiDTO:
        """
        Pobiera akt prawny po identyfikatorze.

        :param publisher: Kod publikatora
        :param year: Rok publikacji
        :param position: Pozycja w publikacji
        :return: Obiekt ActApiDTO
        """
        act = self.api_client.get_act(publisher, year, position)
        return ActApiDTO.model_validate(act)

    def get_all(self) -> list[ActProcessedDTO]:
        """
        Zwraca wszystkie aktywne akty prawne zapisane w bazie danych.

        :return: Lista obiektów ActProcessedDTO
        """
        return [ActProcessedDTO.model_validate(act) for act in self.act_repo.get_all()]

    def get_all_base(self) -> list[ActProcessedDTO]:
        """
        Zwraca spośród aktów prawnych zapisanych w bazie danych tylko te, które są podstawowe (tzn. ustawy,
        które nie są ustawami zmieniającymi) i aktywne.

        :return: Lista obiektów ActProcessedDTO
        """
        base_acts = [
            ActProcessedDTO.model_validate(act)
            for act in self.act_repo.get_all()
            if act.is_base
        ]
        return base_acts

    def get_chunks_for_act(self, act_id: int) -> list[ActChunkDTO]:
        """
        Zwraca z bazy danych fragmenty (chunki) dla danego aktu prawnego.

        :param act_id: ID aktu
        :return: Lista obiektów ActChunkDTO
        """
        return [
            ActChunkDTO.model_validate(chunk)
            for chunk in self.act_chunk_repo.get_for_act(act_id)
        ]

    def get_clustered_chunks_for_act(self, act_id: int, num_clusters: int = 10) -> List[List[ActChunkDTO]]:
        """
        Grupuje fragmenty aktu prawnego w klastry semantyczne.

        :param act_id: ID aktu prawnego
        :param num_clusters: Liczba klastrów do utworzenia
        :return: Lista klastrów, gdzie każdy klaster to lista fragmentów aktu prawnego w formacie DTO
        """
        chunks = self.act_chunk_repo.get_for_act(act_id)
        domain_clusters = self.embedding_semantic_clusterer.cluster(chunks, num_clusters)

        # Konwersja klastrów z modeli domenowych na DTO
        dto_clusters = []
        for cluster in domain_clusters:
            dto_cluster = [ActChunkDTO.model_validate(chunk) for chunk in cluster]
            dto_clusters.append(dto_cluster)

        return dto_clusters

    def find_acts_by_title(self, title: str) -> list[ActApiDTO]:
        """
        Wyszukuje akty prawne po tytule.

        :param title: Tytuł aktu
        :return: Lista obiektów ActApiDTO
        """
        return self.api_client.get_acts_by_title(title)

    def find_base_acts_by_title(self, title: str) -> list[ActApiDTO]:
        """
        Wyszukuje akty prawne zmieniające po tytule.

        :param title: Tytuł aktu
        :return: Lista obiektów ActApiDTO
        """
        acts = [Act.model_validate(act) for act in self.api_client.get_acts_by_title(title)]
        return [
            ActApiDTO.model_validate(act) for act in acts
            if act.is_base
        ]

    def find_consolidation_acts_by_title(self, title: str) -> list[ActApiDTO]:
        """
        Wyszukuje akty prawne zmieniające po tytule.

        :param title: Tytuł aktu
        :return: Lista obiektów ActApiDTO
        """
        acts = [Act.model_validate(act) for act in self.api_client.get_acts_by_title(title)]
        return [
            ActApiDTO.model_validate(act) for act in acts
            if act.is_consolidation
        ]

    def update_missing_embeddings(self) -> None:
        """
        Aktualizuje embeddingi dla wszystkich fragmentów aktów prawnych, które jeszcze ich nie mają.

        @return: Liczba zaktualizowanych fragmentów (chunków)
        @raises EmbeddingError: Gdy nie udało się zaktualizować embeddingów
        """
        try:
            # Pobierz chunki, które nie mają embeddingów
            chunks = self.act_chunk_repo.get_where_embeddings_missing()

            # Utwórz słownik: id_chunka -> tekst_chunka
            texts_dict = {chunk.id: chunk.text for chunk in chunks}
            # Wygeneruj embeddingi za pomocą embedding_handler
            embeddings_dict = self.embedding_handler.bulk_generate_embeddings(texts_dict)

            # Przypisz embeddingi do odpowiednich chunków
            for chunk in chunks:
                chunk.embedding = embeddings_dict.get(chunk.id)

            # Zapisz zaktualizowane chunki w bazie danych
            self.act_chunk_repo.bulk_update(chunks)
        except Exception as e:
            from src.common.exceptions import EmbeddingError
            raise EmbeddingError(f"Błąd podczas aktualizacji embeddingów aktów: {str(e)}")

    def archive_act(self, act_id: int) -> bool:
        """
        Archiwizuje akt prawny (ustawia flagę archived=True).

        :param act_id: ID aktu do zarchiwizowania
        :return: True, jeśli operacja się powiodła, False w przeciwnym razie
        """
        act = self.act_repo.get_by_id(act_id)
        if not act:
            return False

        act.archived = True
        act = self.act_repo.update(act)
        return True if act else False

    def get_consolidation_acts(self, act_id: int) -> List[ConsolidationActDTO]:
        """
        Pobiera listę tekstów jednolitych dla danego aktu wraz z informacją,
        czy są one już przetworzone i dodane do bazy danych.

        :param act_id: ID aktu prawnego
        :return: Lista obiektów ConsolidationActDTO
        :raises EntityNotFoundError: Gdy akt o podanym ID nie istnieje
        """
        act = self.act_repo.get_by_id(act_id)
        if not act:
            raise EntityNotFoundError()

        # Pobierz teksty jednolite z API
        api_acts = self.api_client.get_consolidation_acts(
            act.publisher,
            act.year,
            act.position
        )

        consolidation_acts = []
        for api_act in api_acts:
            db_act = self.act_repo.get_by_identifier(
                api_act.publisher,
                api_act.year,
                api_act.position
            )
            if db_act:
                consolidation_acts.append(ConsolidationActDTO.model_validate(db_act))
            else:
                consolidation_acts.append(ConsolidationActDTO.model_validate(api_act))

        return consolidation_acts

    def process_act(self, act_dto: ActApiDTO) -> ActProcessedDTO:
        """
        Przetwarza akt prawny.
        Wykonuje następujące operacje:
        1. tworzy obiekt aktu prawnego w bazie danych,
        2. pobiera ogłoszony akt prawny w formacie PDF,
        3. przetwarza PDF (parsuje, wyodrębnia chunki i zapisuje w bazie danych),
        4. aktualizuje embeddingi dla zapisanych chunków,
        5. generuje podsumowanie dla aktu prawnego,
        6. przetwarza relacje aktu z innymi aktami.

        :param act_dto: Obiekt ActApiDTO
        :return: Obiekt ActProcessedDTO
        """
        # 1. Tworzy obiekt aktu prawnego w bazie danych (lub pobiera jeśli istnieje)
        is_new, act = self.act_repo.create(Act.model_validate(act_dto))
        if not is_new and act.archived:  # Jeśli był już w DB i jest zarchiwizowany – nadaj status aktywnego i zwróć
            # bez przetwarzania
            act.archived = False
            self.act_repo.update(act)
            return ActProcessedDTO.model_validate(act)

        # 2. Pobiera ogłoszony akt prawny w formacie PDF
        act_pdf = self.api_client.get_act_pdf(act.publisher, act.year, act.position)

        # 3. Przetwarza PDF (parsuje, wyodrębnia chunki i zapisuje w bazie danych)
        chunking_function, element_processors = get_act_processors()
        chunks = TextProcessor.process_document(
            act_pdf,
            chunking_function=chunking_function,
            element_processors=element_processors
        )

        self.act_chunk_repo.bulk_create(
            [ActChunk(reference_id=act.id, text=chunk) for chunk in chunks]
        )

        # 4. Aktualizuje embeddingi dla zapisanych chunków
        self.update_missing_embeddings()

        # 5. Generuje podsumowanie dla aktu prawnego
        self.cluster_orchestrator.generate_act_summary(act.id)

        # 6. Przetwarza relacje aktu z innymi aktami
        self._process_act_relationships(act.id, act_dto)

        return ActProcessedDTO.model_validate(act)

    def _process_act_relationships(self, act_id: int, act_api: ActApiDTO) -> None:
        """
        Przetwarza relacje aktu z innymi aktami.

        Dla każdej listy aktów powiązanych (zmieniających i zmienianych):
        1. Sprawdza, które z nich istnieją już w bazie danych
        2. Tworzy powiązania między aktualnym aktem a znalezionymi aktami

        :param act_id: ID aktu prawnego
        :param act_api: Obiekt ActApiDTO z krotkami identyfikatorów aktów powiązanych
        """
        changing_identifiers = act_api.changing_acts or []
        changed_identifiers = act_api.changed_acts or []

        changing_act_ids = {}
        changed_act_ids = {}
        change_links = []

        # Pobierz istniejące akty z bazy danych
        if changing_identifiers:
            existing_changing = self.act_repo.bulk_get_by_identifier(changing_identifiers)
            # Mapuj istniejące akty na ich ID
            for identifier, act in existing_changing.items():
                if act and act.id:
                    changing_act_ids[identifier] = act.id

        if changed_identifiers:
            existing_changed = self.act_repo.bulk_get_by_identifier(changed_identifiers)
            # Mapuj istniejące akty na ich ID
            for identifier, act in existing_changed.items():
                if act and act.id:
                    changed_act_ids[identifier] = act.id

        # Tworzy relację relacji akt zmieniający -> bieżący akt
        for identifier, changing_id in changing_act_ids.items():
            if changing_id:
                change_links.append(ActChangeLink(
                    changing_act_id=changing_id,
                    changed_act_id=act_id
                ))

        # Tworzy relację bieżący akt -> akt zmieniany
        for identifier, changed_id in changed_act_ids.items():
            if changed_id:
                change_links.append(ActChangeLink(
                    changing_act_id=act_id,
                    changed_act_id=changed_id
                ))

        self.act_change_link_repo.bulk_create(change_links)
