# wersja: chet-theia
from concurrent.futures import as_completed, ThreadPoolExecutor
from typing import List, Tuple, Any, Dict, Callable


class BatchProcessor:
    def __init__(self, process_func: Callable, max_workers: int = 40):
        """
        :param process_func: Funkcja do przetwarzania pojedynczych elementów
        :param max_workers: Maksymalna liczba wątków roboczych
        """
        self.process_func = process_func
        self.max_workers = max_workers
        self.executor = None

    def __enter__(self):
        """
        Metoda wywoływana przy wejściu do bloku 'with'.
        Uruchamia procesor i zwraca jego instancję.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Metoda wywoływana przy wyjściu z bloku 'with'.
        Zatrzymuje procesor niezależnie od tego, czy wystąpił wyjątek.
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
        """
        if self.executor is None:
            raise RuntimeError
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
        Przetwarza wiele elementów i zwraca słownik wyników.

        :param items_with_ids: Lista krotek (identyfikator, element), gdzie element jest przekazywany do process_func
        :return: Słownik mapujący identyfikatory na wyniki przetwarzania
        """
        # Zwraca błąd, jeżeli procesor nie został uruchomiony (w bloku 'with')
        if self.executor is None:
            raise RuntimeError

        futures = {}
        for identifier, item in items_with_ids:
            future = self.submit(item)
            futures[future] = identifier

        results = {}
        for future in as_completed(futures):
            identifier = futures[future]
            results[identifier] = future.result()

        return results
