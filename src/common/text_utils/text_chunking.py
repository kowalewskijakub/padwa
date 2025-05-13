from regex import regex


def chunk_by_articles(text: str) -> list[str]:
    """
    Wyodrębnia artykuły z zadanego tekstu.

    :param text: Tekst do przetworzenia
    :return: Lista artykułów
    """
    articles = []
    article_pattern = r"Art\. \d+(\w{0,4})(\s+\(\w*\)\s+)?\."
    ustawa_pattern = r"USTAWA.?z.?dnia.?\d{1,2}\s\w*\s\d{4}.r\."

    # Pomiń wszystko, co znajduje się przed nazwą ustawy
    match = regex.search(ustawa_pattern, text, flags=regex.DOTALL)
    if match:
        text = text[match.start():]

    # Znajdź wszystkie dopasowania wzorca artykułów
    matches = list(regex.finditer(article_pattern, text, flags=regex.DOTALL))
    if not matches:
        # Jeśli nie znaleziono artykułów, zwróć cały tekst jako jeden fragment
        return [text.strip()] if text.strip() else []

    # Wyodrębnij artykuły na podstawie pozycji dopasowań
    for i, match in enumerate(matches):
        start = match.start()
        # Koniec bieżącego artykułu to początek następnego lub koniec tekstu
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        article_text = text[start:end].strip()
        if article_text:
            articles.append(article_text)

    return articles
