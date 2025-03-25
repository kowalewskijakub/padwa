# wersja: chet-theia
import xml.etree.ElementTree as ET


class LLMPromptsRetriever:
    _instance = None
    _initialized = False

    def __new__(cls):
        """
        Implementacja wzorca Singleton, aby zapewnić pojedynczą instancję menedżera promptów.
        """
        if cls._instance is None:
            cls._instance = super(LLMPromptsRetriever, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Inicjalizuje menedżera promptów i wczytuje szablony z pliku XML.
        """
        if not self._initialized:
            self.prompts = {}
            self.prompts_file = "assets/prompts.xml"
            self._load_prompts()
            self._initialized = True

    def _load_prompts(self) -> None:
        """
        Wczytuje szablony promptów z pliku XML.
        """
        try:
            tree = ET.parse(self.prompts_file)
            root = tree.getroot()

            for prompt_elem in root.findall("prompt"):
                prompt_id = prompt_elem.get("id")
                if prompt_id:
                    template_elem = prompt_elem.find("template")
                    if template_elem is not None and template_elem.text is not None:
                        # Usuń białe znaki na początku i końcu, ale zachowaj wcięcia
                        template = template_elem.text.strip()
                        self.prompts[prompt_id] = template
        except Exception as e:
            raise ValueError(f"Błąd podczas wczytywania promptów z {self.prompts_file}: {e}")

    def get_prompt(self, prompt_id: str) -> str:
        """
        Pobiera szablon promptu o określonym ID.

        :param prompt_id: Identyfikator promptu
        :return: Szablon promptu
        """
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt o ID '{prompt_id}' nie istnieje")
        return self.prompts[prompt_id]


def get_llm_prompt_retriever():
    """
    Zwraca instancję menedżera promptów.

    :return: Instancja LLMPromptsRetriever
    """
    return LLMPromptsRetriever()
