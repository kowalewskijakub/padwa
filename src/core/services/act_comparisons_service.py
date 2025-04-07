from typing import List
import numpy as np
from src.core.dtos.act_dto import ActChangeAnalysisDTO
from src.core.models.act import ActChunk, ActChangeAnalysis
from src.infrastructure.repository.functional.act_change_link_repo import ActChangeLinkRepository
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository
from src.infrastructure.repository.functional.act_change_analysis_repo import ActChangeAnalysisRepository

MIN_SIMILARITY_THRESHOLD = 0.95
MAX_SIMILARITY_THRESHOLD = 0.85

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

    def compare_acts(self, changing_act_id: int, changed_act_id: int) -> List[ActChangeAnalysisDTO]:
        """
        Porównuje dwa akty prawne i zwraca różnice między nimi.

        :param changing_act_id: ID aktu zmieniającego
        :param changed_act_id: ID aktu zmienianego
        :return: Lista wyników analizy zmian
        """
        related_acts = self.act_change_link_repo.get_changed_acts(changing_act_id)
        if changed_act_id not in related_acts:
            raise ValueError("Te akty nie są powiązane")

        existing_analysis = self.act_change_analysis_repo.get_by_act_pair(changing_act_id, changed_act_id)
        if existing_analysis:
            return self._enrich_analysis_with_text(existing_analysis)

        changing_chunks = self.act_chunk_repo.get_for_act(changing_act_id)
        changed_chunks = self.act_chunk_repo.get_for_act(changed_act_id)

        analysis_results = self._analyze_changes(changing_act_id, changed_act_id, changing_chunks, changed_chunks)
        saved_analysis = self.act_change_analysis_repo.bulk_create(analysis_results)

        return self._enrich_analysis_with_text(saved_analysis)

    def _analyze_changes(self, changing_act_id: int, changed_act_id: int, changing_chunks: List[ActChunk],
                         changed_chunks: List[ActChunk]) -> List[ActChangeAnalysis]:
        """
        Analizuje zmiany między fragmentami dwóch aktów prawnych.

        :param changing_act_id: ID aktu zmieniającego
        :param changed_act_id: ID aktu zmienianego
        :param changing_chunks: Lista fragmentów aktu zmieniającego
        :param changed_chunks: Lista fragmentów aktu zmienianego
        :return: Lista wyników analizy
        """
        results = []

        changing_embeddings = np.array([c.embedding for c in changing_chunks if c.embedding is not None])
        changed_embeddings = np.array([c.embedding for c in changed_chunks if c.embedding is not None])

        matched_changed = set()
        for i, changing_chunk in enumerate(changing_chunks):
            similarities = np.dot(changing_embeddings[i], changed_embeddings.T) / (
                    np.linalg.norm(changing_embeddings[i]) * np.linalg.norm(changed_embeddings, axis=1)
            )
            max_similarity_idx = np.argmax(similarities)
            max_similarity = similarities[max_similarity_idx]

            if max_similarity >= MIN_SIMILARITY_THRESHOLD:
                continue
            elif max_similarity >= MAX_SIMILARITY_THRESHOLD:
                changed_chunk = changed_chunks[max_similarity_idx]
                matched_changed.add(max_similarity_idx)

                if changing_chunk.text != changed_chunk.text:
                    results.append(ActChangeAnalysis(
                        changing_act_id=changing_act_id,
                        changed_act_id=changed_act_id,
                        changing_chunk_id=changing_chunk.id,
                        changed_chunk_id=changed_chunk.id,
                        change_type="modified"
                    ))
            else:
                results.append(ActChangeAnalysis(
                    changing_act_id=changing_act_id,
                    changed_act_id=changed_act_id,
                    changing_chunk_id=changing_chunk.id,
                    changed_chunk_id=None,
                    change_type="appended"
                ))

        for i, changed_chunk in enumerate(changed_chunks):
            if i not in matched_changed:
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
        :return: Lista DTO z dodanym tekstem
        """
        all_chunk_ids = set(a.changing_chunk_id for a in analysis) | \
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