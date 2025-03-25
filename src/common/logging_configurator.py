# wersja: chet-theia
import logging
import os.path
from pathlib import Path


class LoggingConfigurator():
    _instance = None
    _initialized = False

    def __new__(cls):
        """
        Implementacja wzorca Singleton, aby zapewnić pojedynczą instancję konfiguratora.

        :return: Pojedyncza instancja Logger
        """
        if cls._instance is None:
            cls._instance = super(LoggingConfigurator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Konfiguruje ustawienia logowania.
        """
        if not self._initialized:
            root_dir = Path(__file__).parent.parent.parent
            logging.basicConfig(
                filename=os.path.join(str(root_dir), 'app.log'),
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s"
            )
            self._initialized = True


def get_logger() -> logging.Logger:
    """
    Zwraca instancję skonfigurowanego obiektu Logger.

    :return: Skonfigurowany obiekt Logger
    """
    # Zapewnienie, że konfiguracja logowania jest zainicjowana
    LoggingConfigurator()

    return logging.getLogger()
