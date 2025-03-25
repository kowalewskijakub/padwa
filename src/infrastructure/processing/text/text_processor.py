import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Callable, Union

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.common.batch_processor import BatchProcessor
from src.common.exceptions import TextProcessingError
from src.common.logging_configurator import get_logger
from src.common.text_utils.text_chunking import chunk_by_articles
from src.common.text_utils.text_cleanup import clean_stamps, clean_hyphenation

_logger = get_logger()


class TextProcessor:
    """
    Klasa do przetwarzania plików PDF.
    Wyodrębnia tekst i dzieli go na fragmenty używając PyMuPDF poprzez LangChain.
    """

    @staticmethod
    def _extract_text_from_pdf(
            pdf_path: str,
            element_processors: List[Callable[[str], str]] = None,
            extract_by_page: bool = False
    ) -> Union[str, List[str]]:
        """
        Wyodrębnia tekst z dokumentu PDF przy użyciu PyMuPDF poprzez LangChain.

        :param pdf_path: Ścieżka do pliku PDF
        :param element_processors: Lista funkcji do przetwarzania indywidualnych elementów tekstu
        :param extract_by_page: Czy wyodrębniać tekst strona po stronie (True) czy cały dokument naraz (False)
        :return: Pełny tekst dokumentu lub lista tekstów stron
        :raises TextProcessingError: Gdy nie udało się wyodrębnić tekstu
        """
        try:
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()

            if extract_by_page:
                result = []
                for doc in documents:
                    page_text = doc.page_content

                    # Zastosowanie procesorów dla pojedynczej strony
                    if element_processors:
                        for processor in element_processors:
                            page_text = processor(page_text)

                    result.append(page_text)
                return result
            else:
                # Połącz cały tekst
                full_text = "\n\n".join(doc.page_content for doc in documents)

                # Zastosowanie procesorów dla całego tekstu
                if element_processors:
                    for processor in element_processors:
                        full_text = processor(full_text)

                return full_text.strip()

        except Exception as e:
            _logger.error(f"Błąd podczas wyodrębniania tekstu z PDF: {str(e)}")
            raise TextProcessingError(f"Nie udało się wyodrębnić tekstu z PDF: {str(e)}")

    @staticmethod
    def process_document(
            document_content: bytes,
            chunking_function: Optional[Callable[[str], List[str]]] = None,
            element_processors: List[Callable[[str], str]] = None
    ) -> Optional[List[str]]:
        """
        Przetwarza dokument i wyodrębnia fragmenty tekstu.
        Jeśli nie podano funkcji podziału, używany jest domyślny mechanizm podziału LangChain.

        :param document_content: Zawartość dokumentu jako bajty
        :param chunking_function: Funkcja dzieląca pełny tekst na fragmenty
        :param element_processors: Lista funkcji przetwarzających pojedyncze elementy tekstu (string → string)
        :return: Lista fragmentów tekstu
        :raises TextProcessingError: Gdy przetwarzanie dokumentu się nie powiedzie
        """
        temp_path = None

        try:
            start = time.time()

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(document_content)
                temp_file.flush()

            full_text = TextProcessor._extract_text_from_pdf(
                str(temp_path),
                element_processors,
                extract_by_page=False
            )

            if chunking_function:  # Jeśli podano funkcję do chunking, użyj jej
                fragments = chunking_function(full_text)
                end = time.time()
                _logger.info(
                    f"Przetwarzanie dokumentu zakończone. Czas: {end - start:.2f}s. "
                    f"Utworzono {len(fragments)} fragmentów.")
                return fragments
            else:
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000)
                fragments = text_splitter.split_text(full_text)
                end = time.time()
                _logger.info(
                    f"Przetwarzanie dokumentu zakończone. Czas: {end - start:.2f}s. "
                    f"Utworzono {len(fragments)} fragmentów domyślnym mechanizmem podziału.")
                return fragments

        except Exception as e:
            _logger.error(f"Błąd podczas przetwarzania dokumentu: {str(e)}")
            raise TextProcessingError(f"Przetwarzanie dokumentu nie zostało ukończone: {str(e)}")
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def bulk_process_documents(
            document_files: List[Tuple[str, bytes]],
            chunking_function: Optional[Callable[[str], List[str]]] = None,
            element_processors: List[Callable[[str], str]] = None
    ) -> Optional[Dict[str, List[str]]]:
        """
        Przetwarza wiele dokumentów równolegle i wyodrębnia fragmenty tekstu z każdego z nich.

        :param document_files: Lista krotek (identyfikator, zawartość pliku jako bajty)
        :param chunking_function: Funkcja dzieląca pełny tekst na fragmenty (string → list of strings)
        :param element_processors: Lista funkcji przetwarzających pojedyncze elementy tekstu (string → string)
        :return: Słownik mapujący identyfikatory na listy fragmentów tekstu
        """
        processor_func = lambda content: TextProcessor.process_document(
            content, chunking_function, element_processors
        )

        with BatchProcessor(processor_func) as processor:
            return processor.process_batch(document_files)


def get_act_processors() -> Tuple[Callable[[str], List[str]], List[Callable[[str], str]]]:
    """
    Zwraca standardowy zestaw procesorów dla aktów prawnych.

    :return: Krotka (funkcja_dzieląca, lista_procesorów_elementów)
    """
    return chunk_by_articles, [clean_hyphenation, clean_stamps]


def get_doc_processors() -> Tuple[None, List[Callable[[str], str]]]:
    """
    Zwraca standardowy zestaw procesorów dla dokumentów.

    :return: Krotka (None, lista_procesorów_elementów)
    """
    return None, [clean_hyphenation]
