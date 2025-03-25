# wersja: chet-theia
from dependency_injector import containers, providers
from infrastructure.api.eli_api_client import ELIApiClient
from infrastructure.database.database_manager import DatabaseManager
from infrastructure.processing.embedding.embedding_handler import EmbeddingHandler
from infrastructure.processing.embedding.embedding_semantic_clusterer import EmbeddingSemanticClusterer
from infrastructure.processing.llm.llm_handler import LLMHandler
from infrastructure.processing.llm.llm_iterative_summarizer import LLMIterativeSummarizer
from infrastructure.repository.core.act_repository import ActRepository
from infrastructure.repository.core.doc_repository import DocRepository
from infrastructure.repository.embeddable.act_chunk_cluster_repository import ActChunkClusterRepository
from infrastructure.repository.embeddable.act_chunk_repository import ActChunkRepository
from infrastructure.repository.embeddable.doc_chunk_repository import DocChunkRepository
from infrastructure.repository.functional.act_change_link_repo import ActChangeLinkRepository

from src.application.services.acts_service import ActsService
from src.application.services.clusters_service import ClustersService
from src.application.services.dictionaries_service import DictionariesService
from src.application.services.docs_service import DocsService
from src.application.services.statistics_service import StatisticsService
from src.presentation.app_config import AppConfig


class Container(containers.DeclarativeContainer):
    """
    Kontener IoC (Inversion of Control) dla aplikacji.

    Definiuje i konfiguruje wszystkie zależności aplikacji,
    zapewniając ich poprawną inicjalizację i wstrzykiwanie.
    """

    config = providers.Singleton(
        AppConfig.load
    )

    # Infrastruktura - API
    api_client = providers.Singleton(
        ELIApiClient,
        base_url=config.provided.eli_api_base_url
    )

    # Infrastruktura – baza danych
    db_manager = providers.Singleton(
        DatabaseManager
    )

    # Infrastruktura - repozytoria (core)
    act_repository = providers.Singleton(
        ActRepository,
        db_manager=db_manager
    )

    doc_repository = providers.Singleton(
        DocRepository,
        db_manager=db_manager
    )

    # Infrastruktura - repozytoria (embeddable)
    act_chunk_repository = providers.Singleton(
        ActChunkRepository,
        db_manager=db_manager
    )

    act_chunk_cluster_repository = providers.Singleton(
        ActChunkClusterRepository,
        db_manager=db_manager
    )

    doc_chunk_repository = providers.Singleton(
        DocChunkRepository,
        db_manager=db_manager
    )

    # Infrastruktura - repozytoria (functional)
    act_change_link_repository = providers.Singleton(
        ActChangeLinkRepository,
        db_manager=db_manager
    )

    # Domena - embeddingi
    embedding_handler = providers.Singleton(
        EmbeddingHandler,
        act_chunk_repo=act_chunk_repository,
        model_name=config.provided.embedding_model,
        vector_size=config.provided.embedding_vector_size
    )

    embedding_semantic_clusterer = providers.Singleton(
        EmbeddingSemanticClusterer,
        act_chunk_repo=act_chunk_repository,
        embedding_handler=embedding_handler
    )

    # Domena - LLM
    llm_handler = providers.Singleton(
        LLMHandler,
        model_name=config.provided.llm_model
    )

    llm_iterative_summarizer = providers.Singleton(
        LLMIterativeSummarizer,
        llm_handler=llm_handler,
        semantic_clusterer=embedding_semantic_clusterer
    )

    # Aplikacja – serwisy
    clusters_service = providers.Singleton(
        ClustersService,
        act_repo=act_repository,
        act_chunk_repo=act_chunk_repository,
        act_chunk_cluster_repo=act_chunk_cluster_repository,
        embedding_handler=embedding_handler,
        llm_iterative_summarizer=llm_iterative_summarizer
    )

    acts_service = providers.Singleton(
        ActsService,
        api_client=api_client,
        act_repo=act_repository,
        act_chunk_repo=act_chunk_repository,
        act_change_link_repo=act_change_link_repository,
        embedding_handler=embedding_handler,
        embedding_semantic_clusterer=embedding_semantic_clusterer,
        cluster_orchestrator=clusters_service
    )

    docs_service = providers.Singleton(
        DocsService,
        doc_repo=doc_repository,
        doc_chunk_repo=doc_chunk_repository,
        llm_handler=llm_handler,
        embedding_handler=embedding_handler
    )

    statistics_service = providers.Singleton(
        StatisticsService,
        act_repo=act_repository,
        act_chunk_repo=act_chunk_repository,
        doc_repo=doc_repository,
        doc_chunk_repo=doc_chunk_repository
    )

    dictionaries_service = providers.Singleton(
        DictionariesService,
        db_manager=db_manager,
        api_client=api_client
    )
