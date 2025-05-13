import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Callable, Union

import fitz
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
    Wyodrębnia tekst i dzieli go na fragmenty używając PyMuPDF.
    """

    @staticmethod
    def _extract_text_from_pdf(
            pdf_path: str,
            element_processors: List[Callable[[str], str]] = None,
            extract_by_page: bool = False,
            min_font_size: Optional[float] = None
    ) -> Union[str, List[str]]:
        """
        Wyodrębnia tekst z dokumentu PDF przy użyciu PyMuPDF.
        Superscript tekst jest zawsze dołączany i oznaczany nawiasami '()',
        niezależnie od min_font_size, chyba że tekst superscript to samo ")",
        wtedy jest pomijany.

        :param pdf_path: Ścieżka do pliku PDF
        :param element_processors: Lista funkcji do przetwarzania indywidualnych elementów tekstu (spanów)
        :param extract_by_page: Czy wyodrębniać tekst strona po stronie (True) czy cały dokument naraz (False)
        :param min_font_size: Minimalny rozmiar czcionki do uwzględnienia dla tekstu niebędącego superindeksem (opcjonalny)
        :return: Pełny tekst dokumentu lub lista tekstów stron
        :raises TextProcessingError: Gdy nie udało się wyodrębnić tekstu
        """
        if element_processors is None:
            element_processors = []

        try:
            doc = fitz.open(pdf_path)
            result_pages_text = []

            font_is_superscript = 1

            for page_num, page in enumerate(doc):
                blocks = page.get_text("dict", sort=True)["blocks"]
                current_page_lines = []

                for block in blocks:
                    if block["type"] == 0:
                        for line in block["lines"]:
                            processed_span_texts_for_line = []
                            for span in line["spans"]:
                                stripped_processed_text = span["text"].strip()
                                if not stripped_processed_text:
                                    continue

                                is_superscript = (span["flags"] & font_is_superscript) != 0
                                text_to_add = ""

                                if is_superscript:
                                    if ')' in stripped_processed_text:  # Ignoruje superscript, który zawiera zamknięty
                                        # nawias klamrowy – ma to na celu uniknięcie
                                        # traktowania przypisu jako indeksu
                                        text_to_add = ""
                                    else:
                                        text_to_add = f"({stripped_processed_text})"
                                elif min_font_size is None or span["size"] >= min_font_size:
                                    text_to_add = stripped_processed_text

                                if text_to_add:
                                    processed_span_texts_for_line.append(text_to_add)

                            if processed_span_texts_for_line:
                                current_page_lines.append(" ".join(filter(None, processed_span_texts_for_line)))

                page_text_final = "\n".join(filter(None, current_page_lines)).strip()
                result_pages_text.append(page_text_final)

            doc.close()

            if not any(result_pages_text) and doc.page_count > 0:
                _logger.warning(f"Nie wyodrębniono tekstu z PDF '{pdf_path}'. "
                                "Może to być plik obrazowy, cały tekst mógł zostać odfiltrowany, "
                                "lub jest to pusty dokument.")

            # Stosuje przypisane funkcje przetwarzające do każdego elementu tekstu (np. usuwa dewizy)
            for processor in element_processors:
                for i in range(len(result_pages_text)):
                    result_pages_text[i] = processor(result_pages_text[i])

            if extract_by_page:
                return result_pages_text
            else:
                full_text = "\n\n".join(filter(None, result_pages_text)).strip()
                return full_text

        except Exception as e:
            _logger.error(f"Błąd podczas wyodrębniania tekstu z PDF '{pdf_path}': {str(e)}")
            raise TextProcessingError(f"Nie udało się wyodrębnić tekstu z PDF '{pdf_path}': {str(e)}")

    @staticmethod
    def process_document(
            document_content: bytes,
            chunking_function: Optional[Callable[[str], List[str]]] = None,
            element_processors: List[Callable[[str], str]] = None,
            min_font_size: Optional[float] = None
    ) -> Optional[List[str]]:
        """
        Przetwarza dokument i wyodrębnia fragmenty tekstu.
        Jeśli nie podano funkcji podziału, używany jest domyślny mechanizm podziału LangChain.

        :param document_content: Zawartość dokumentu jako bajty
        :param chunking_function: Funkcja dzieląca pełny tekst na fragmenty
        :param element_processors: Lista funkcji przetwarzających pojedyncze elementy tekstu (string → string)
        :param min_font_size: Minimalny rozmiar czcionki do uwzględnienia
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
                extract_by_page=False,
                min_font_size=min_font_size
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
            element_processors: List[Callable[[str], str]] = None,
            min_font_size: Optional[float] = None
    ) -> Optional[Dict[str, List[str]]]:
        """
        Przetwarza wiele dokumentów równolegle i wyodrębnia fragmenty tekstu z każdego z nich.

        :param document_files: Lista krotek (identyfikator, zawartość pliku jako bajty)
        :param chunking_function: Funkcja dzieląca pełny tekst na fragmenty (string → list of strings)
        :param element_processors: Lista funkcji przetwarzających pojedyncze elementy tekstu (string → string)
        :param min_font_size: Minimalny rozmiar czcionki do uwzględnienia
        :return: Słownik mapujący identyfikatory na listy fragmentów tekstu
        """
        processor_func = lambda content: TextProcessor.process_document(
            content, chunking_function, element_processors, min_font_size
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
