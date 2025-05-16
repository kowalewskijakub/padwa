from typing import List, Optional

import regex
from scipy.spatial import distance

from src.common.logging_configurator import get_logger
from src.core.dtos.act_dto import ActChangeAnalysisDTO
from src.core.models.act import ActChunk, ActChangeAnalysis
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository
from src.infrastructure.repository.functional.act_change_analysis_repo import ActChangeAnalysisRepository
from src.infrastructure.repository.functional.act_change_link_repo import ActChangeLinkRepository

_logger = get_logger()


class ActComparisonsService:
    def __init__(
            self,
            act_chunk_repo: ActChunkRepository,
            act_change_link_repo: ActChangeLinkRepository,
            act_change_analysis_repo: ActChangeAnalysisRepository
    ):
        """
        Inicjalizuje serwis porównywania aktów prawnych.

        :param act_chunk_repo: Repozytorium fragmentów aktów
        :param act_change_link_repo: Repozytorium relacji zmian aktów
        :param act_change_analysis_repo: Repozytorium analiz zmian
        """
        self.act_chunk_repo = act_chunk_repo
        self.act_change_link_repo = act_change_link_repo
        self.act_change_analysis_repo = act_change_analysis_repo

    @staticmethod
    def extract_article_number(text: str) -> Optional[str]:
        """
        Wyodrębnia numer artykułu z tekstu chunka za pomocą wzorca regex.

        :param text: Tekst chunka
        :return: Numer artykułu (np. "Art. 1.") lub None, jeśli nie znaleziono
        """
        match = regex.match(r"Art\. \d+(\w{0,4})(\s+\(\w*\)\s+)?\.", text)
        return match.group(0) if match else None

    def compare_acts(self, changing_act_id: int, changed_act_id: int, similarity_threshold: float = 0.985) -> List[
        ActChangeAnalysisDTO]:
        """
        Porównuje dwa akty prawne na podstawie numerów artykułów i zwraca różnice.

        :param changing_act_id: ID aktu zmieniającego
        :param changed_act_id: ID aktu zmienianego
        :param similarity_threshold: Próg podobieństwa dla uznania artykułów za zmodyfikowane (domyślnie 0.95)
        :return: Lista wyników analizy zmian w formacie DTO
        """
        existing_analysis = self.act_change_analysis_repo.get_by_act_pair(changing_act_id, changed_act_id)
        if existing_analysis:
            return self._enrich_analysis_with_text(existing_analysis)

        changing_chunks = self.act_chunk_repo.get_for_act(changing_act_id)
        changed_chunks = self.act_chunk_repo.get_for_act(changed_act_id)

        analysis_results = self._analyze_changes(changing_act_id, changed_act_id, changing_chunks, changed_chunks,
                                                 similarity_threshold)
        saved_analysis = self.act_change_analysis_repo.bulk_create(analysis_results)

        return self._enrich_analysis_with_text(saved_analysis)

    def _analyze_changes(self, changing_act_id: int, changed_act_id: int, changing_chunks: List[ActChunk],
                         changed_chunks: List[ActChunk], similarity_threshold: float) -> List[ActChangeAnalysis]:
        """
        Analizuje zmiany między fragmentami dwóch aktów prawnych na podstawie numerów artykułów i embeddingów.

        :param changing_act_id: ID aktu zmieniającego
        :param changed_act_id: ID aktu zmienianego
        :param changing_chunks: Lista fragmentów aktu zmieniającego
        :param changed_chunks: Lista fragmentów aktu zmienianego
        :param similarity_threshold: Próg podobieństwa dla uznania artykułów za zmodyfikowane
        :return: Lista wyników analizy zmian
        """
        results = []

        changing_map = {}
        for chunk in changing_chunks:
            art_num = self.extract_article_number(chunk.text)
            if art_num:
                changing_map[art_num] = chunk
            else:
                _logger.warning(f"Chunk bez numeru artykułu w akcie zmieniającym {changing_act_id}: {chunk.id}")

        changed_map = {}
        for chunk in changed_chunks:
            art_num = self.extract_article_number(chunk.text)
            if art_num:
                changed_map[art_num] = chunk
            else:
                _logger.warning(f"Chunk bez numeru artykułu w akcie zmienianym {changed_act_id}: {chunk.id}")

        changing_arts = set(changing_map.keys())
        changed_arts = set(changed_map.keys())

        common_arts = changing_arts.intersection(changed_arts)
        for art in common_arts:
            changing_chunk = changing_map[art]
            changed_chunk = changed_map[art]
            if changing_chunk.text != changed_chunk.text:
                similarity = 1 - distance.cosine(changing_chunk.embedding, changed_chunk.embedding)
                if similarity < similarity_threshold:
                    results.append(ActChangeAnalysis(
                        changing_act_id=changing_act_id,
                        changed_act_id=changed_act_id,
                        changing_chunk_id=changing_chunk.id,
                        changed_chunk_id=changed_chunk.id,
                        change_type="modified"
                    ))
                else:
                    _logger.info(f"Artykuły {art} trochę różnią się między sobą ({similarity:.2f}), ale"
                                 f"nie zostają oznaczone jako 'modified'.")

        appended_arts = changing_arts - changed_arts
        for art in appended_arts:
            changing_chunk = changing_map[art]
            results.append(ActChangeAnalysis(
                changing_act_id=changing_act_id,
                changed_act_id=changed_act_id,
                changing_chunk_id=changing_chunk.id,
                changed_chunk_id=None,
                change_type="appended"
            ))

        removed_arts = changed_arts - changing_arts
        for art in removed_arts:
            changed_chunk = changed_map[art]
            results.append(ActChangeAnalysis(
                changing_act_id=changing_act_id,
                changed_act_id=changed_act_id,
                changing_chunk_id=None,
                changed_chunk_id=changed_chunk.id,
                change_type="removed"
            ))

        return results

    def _enrich_analysis_with_text(self, analysis: List[ActChangeAnalysis]) -> List[ActChangeAnalysisDTO]:
        """
        Wzbogaca wyniki analizy o tekst fragmentów.

        :param analysis: Lista analiz zmian
        :return: Lista DTO z dodanym tekstem fragmentów
        """
        all_chunk_ids = set(a.changing_chunk_id for a in analysis if a.changing_chunk_id) | \
                        set(a.changed_chunk_id for a in analysis if a.changed_chunk_id)

        chunks = self.act_chunk_repo.bulk_get_by_ids(list(all_chunk_ids))
        chunk_dict = {c.id: c.text for c in chunks}

        return [
            ActChangeAnalysisDTO(
                id=a.id,
                changing_act_id=a.changing_act_id,
                changed_act_id=a.changed_act_id,
                changing_chunk_id=a.changing_chunk_id,
                changed_chunk_id=a.changed_chunk_id,
                change_type=a.change_type,
                relevancy=a.relevancy,
                justification=a.justification,
                changing_chunk_text=chunk_dict.get(a.changing_chunk_id) if a.changing_chunk_id else None,
                changed_chunk_text=chunk_dict.get(a.changed_chunk_id) if a.changed_chunk_id else None
            )
            for a in analysis
        ]
