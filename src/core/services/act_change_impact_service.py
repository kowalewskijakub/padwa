from typing import List

from src.common.batch_processor import BatchProcessor
from src.core.dtos.act_dto import ActChangeAnalysisDTO, ActChangeImpactAnalysisDTO
from src.core.models.act import ActChangeImpactAnalysis, ActChangeAnalysis
from src.infrastructure.processing.embedding.embedding_handler import EmbeddingHandler
from src.infrastructure.processing.llm.llm_handler import LLMHandler
from src.infrastructure.processing.llm.llm_response_models import ImpactAssessmentResponse
from src.infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository
from src.infrastructure.repository.embeddable.doc_chunk_repository import DocChunkRepository
from src.infrastructure.repository.functional.act_change_analysis_repo import ActChangeAnalysisRepository
from src.infrastructure.repository.functional.act_change_impact_analysis_repo import ActChangeImpactAnalysisRepository


class ActChangeImpactService:
    """
    Serwis odpowiedzialny za analizę wpływu zmian w aktach prawnych na fragmenty dokumentów.
    """

    def __init__(
            self,
            act_change_analysis_repo: ActChangeAnalysisRepository,
            act_chunk_repo: ActChunkRepository,
            doc_chunk_repo: DocChunkRepository,
            act_change_impact_analysis_repo: ActChangeImpactAnalysisRepository,
            embedding_handler: EmbeddingHandler,
            llm_handler: LLMHandler
    ):
        """
        Inicjalizuje serwis analizy wpływu.

        :param act_change_analysis_repo: Repozytorium dla analiz zmian
        :param act_chunk_repo: Repozytorium dla fragmentów aktów
        :param doc_chunk_repo: Repozytorium dla fragmentów dokumentów
        :param act_change_impact_analysis_repo: Repozytorium dla analiz wpływu
        :param embedding_handler: Obsługa osadzania (embeddingów)
        :param llm_handler: Obsługa modeli językowych
        """
        self.act_change_analysis_repo = act_change_analysis_repo
        self.act_chunk_repo = act_chunk_repo
        self.doc_chunk_repo = doc_chunk_repo
        self.act_change_impact_analysis_repo = act_change_impact_analysis_repo
        self.embedding_handler = embedding_handler
        self.llm_handler = llm_handler

    def analyze_impact(self, changing_act_id: int, changed_act_id: int) -> List[ActChangeAnalysisDTO]:
        """
        Analizuje wpływ zmian w akcie prawnym na fragmenty dokumentów, zwracając istniejące wyniki, jeśli są dostępne,
        w przeciwnym razie obliczając je przy użyciu przetwarzania wsadowego.

        :param changing_act_id: ID aktu zmieniającego
        :param changed_act_id: ID aktu zmienianego
        :return: Lista DTO zawierających analizy zmian z wynikami wpływu
        """
        analyses = self.act_change_analysis_repo.get_by_act_pair_with_texts(changing_act_id, changed_act_id)
        if not analyses:
            return []

        # Sprawdza, czy istnieją zapisane analizy wpływu
        existing_impacts = self.act_change_impact_analysis_repo.get_by_act_pair(changing_act_id, changed_act_id)
        if existing_impacts:
            return self._enrich_analysis_with_impacts(analyses, existing_impacts)

        items_with_ids = []
        for analysis in analyses:
            if analysis.change_type in ["modified", "appended", "removed"]:
                chunk_id = analysis.changing_chunk_id or analysis.changed_chunk_id
                chunk = self.act_chunk_repo.get_by_id(chunk_id)
                similar_doc_chunks = self.doc_chunk_repo.get_top_n_similar(chunk.embedding, n=5)
                for doc_chunk in similar_doc_chunks:
                    input_dict = {
                        "change_type": analysis.change_type,
                        "changed_text": analysis.changed_chunk_text,
                        "changing_text": analysis.changing_chunk_text,
                        "doc_text": doc_chunk.text,
                    }
                    identifier = (analysis.id, doc_chunk.id)
                    items_with_ids.append((identifier, input_dict))

        process_func = lambda input_dict: self.llm_handler.invoke(ImpactAssessmentResponse, input_dict)
        with BatchProcessor(process_func=process_func) as processor:
            results = processor.process_batch(items_with_ids)

        impact_analyses = []
        for identifier, response in results.items():
            analysis_id, doc_chunk_id = identifier
            impact_analyses.append(ActChangeImpactAnalysis(
                changing_act_id=changing_act_id,
                changed_act_id=changed_act_id,
                change_analysis_id=analysis_id,
                doc_chunk_id=doc_chunk_id,
                relevancy=response.relevancy,
                justification=response.justification
            ))

        if impact_analyses:
            self.act_change_impact_analysis_repo.bulk_create(impact_analyses)

        return self._enrich_analysis_with_impacts(analyses, impact_analyses)

    def _enrich_analysis_with_impacts(self, analyses: List[ActChangeAnalysis],
                                      impacts: List[ActChangeImpactAnalysis]) -> List[ActChangeAnalysisDTO]:
        """
        Wzbogaca analizy zmian o wyniki analizy wpływu i teksty fragmentów.

        :param analyses: Lista analiz zmian z tekstami fragmentów
        :param impacts: Lista analiz wpływu
        :return: Lista wzbogaconych DTO z wynikami wpływu
        """
        impact_dict = {}
        for impact in impacts:
            if impact.change_analysis_id not in impact_dict:
                impact_dict[impact.change_analysis_id] = []
            impact_dict[impact.change_analysis_id].append(impact)

        all_doc_chunk_ids = set(impact.doc_chunk_id for impact in impacts)
        doc_chunks = self.doc_chunk_repo.bulk_get_by_ids(list(all_doc_chunk_ids))
        doc_chunk_dict = {c.id: c.text for c in doc_chunks}

        enriched_analyses = []
        for a in analyses:
            impacts_for_analysis = impact_dict.get(a.id, [])
            impact_dtos = [
                ActChangeImpactAnalysisDTO(
                    id=impact.id,
                    change_analysis_id=impact.change_analysis_id,
                    doc_chunk_id=impact.doc_chunk_id,
                    relevancy=impact.relevancy,
                    justification=impact.justification,
                    doc_chunk_text=doc_chunk_dict.get(impact.doc_chunk_id)
                ) for impact in impacts_for_analysis
            ]
            enriched_analyses.append(
                ActChangeAnalysisDTO(
                    id=a.id,
                    changing_act_id=a.changing_act_id,
                    changed_act_id=a.changed_act_id,
                    changing_chunk_id=a.changing_chunk_id,
                    changed_chunk_id=a.changed_chunk_id,
                    change_type=a.change_type,
                    relevancy=a.relevancy,
                    justification=a.justification,
                    changing_chunk_text=a.changing_chunk_text,
                    changed_chunk_text=a.changed_chunk_text,
                    impacts=impact_dtos
                )
            )
        return enriched_analyses