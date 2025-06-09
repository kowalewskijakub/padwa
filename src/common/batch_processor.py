"""
Procesor do przetwarzania równoległego.

Umożliwia przetwarzanie dużych ilości danych w trybie równoległym
z wykorzystaniem ThreadPoolExecutor. Obsługuje wzorzec context manager.
"""
# wersja: chet-theia
from concurrent.futures import as_completed, ThreadPoolExecutor
from typing import List, Tuple, Any, Dict, Callable


class BatchProcessor:
    """
    Procesor do równoległego przetwarzania elementów.
    
    Wykorzystuje ThreadPoolExecutor do wykonywania operacji w wielu wątkach.
    Implementuje wzorzec context manager dla bezpiecznego zarządzania zasobami.
    """

    def __init__(self, process_func: Callable, max_workers: int = 40):
        """
        Inicjalizuje procesor.
        
        :param process_func: Funkcja do przetwarzania pojedynczych elementów
        :param max_workers: Maksymalna liczba wątków roboczych (domyślnie 40)
        """
        self.process_func = process_func
        self.max_workers = max_workers
        self.executor = None

    def __enter__(self):
        """
        Metoda wywoływana przy wejściu do bloku 'with'.
        
        Uruchamia procesor i zwraca jego instancję.
        
        :return: Instancja BatchProcessor
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Metoda wywoływana przy wyjściu z bloku 'with'.
        
        Zatrzymuje procesor niezależnie od tego, czy wystąpił wyjątek.
        
        :param exc_type: Typ wyjątku (jeśli wystąpił)
        :param exc_val: Wartość wyjątku (jeśli wystąpił)
        :param exc_tb: Traceback wyjątku (jeśli wystąpił)
        :return: False (nie tłumi wyjątków)
        """
        self.stop()
        return False

    def start(self):
        """
        Uruchamia procesor.
        """
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def submit(self, item):
        """
        Przesyła element do przetworzenia.

        :param item: Element do przetworzenia
        :return: Future reprezentujący przyszły wynik
        :raises RuntimeError: Gdy procesor nie został uruchomiony
        """
        if self.executor is None:
            raise RuntimeError("Procesor nie został uruchomiony. Użyj w bloku 'with' lub wywołaj start().")
        return self.executor.submit(self.process_func, item)

    def stop(self):
        """
        Zatrzymuje procesor i czeka na zakończenie wszystkich zadań.
        """
        if self.executor is not None:
            self.executor.shutdown(wait=True)
            self.executor = None

    def process_batch(self, items_with_ids: List[Tuple[Any, Any]]) -> Dict[Any, Any]:
        """
        Przetwarza wiele elementów równolegle i zwraca słownik wyników.

        :param items_with_ids: Lista krotek (identyfikator, element), gdzie element jest przekazywany do process_func
        :return: Słownik mapujący identyfikatory na wyniki przetwarzania
        :raises RuntimeError: Gdy procesor nie został uruchomiony
        """
        if self.executor is None:
            raise RuntimeError("Procesor nie został uruchomiony. Użyj w bloku 'with' lub wywołaj start().")

        futures = {}
        for identifier, item in items_with_ids:
            future = self.submit(item)
            futures[future] = identifier

        results = {}
        for future in as_completed(futures):
            identifier = futures[future]
            results[identifier] = future.result()

        return results
