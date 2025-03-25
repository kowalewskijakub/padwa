from regex import regex


def chunk_by_articles(text: str) -> list[str]:
    """
    Wyodrębnia artykuły z zadanego tekstu.

    :param text: Tekst do przetworzenia (głównie: akt prawny o randze ustawowej)
    :return: Lista artykułów
    """
    articles = []
    article_pattern = r"Art\. \d{1,}(\w{0,4})(\p{No}{0,2})\."
    ustawa_pattern = r"USTAWA z dnia \d{1,2} \w* \d{4} r."

    # Pomiń wszystko, co znajduje się przed nazwą ustawy
    match = regex.search(ustawa_pattern, text, flags=regex.DOTALL)
    if match:
        text = text[match.start():]

    # Zacznij od 1. artykułu
    match = regex.search(article_pattern, text, flags=regex.DOTALL)
    if match:
        text = text[match.start():]

    lines = text.splitlines()

    current_article = ''
    current_article += lines[0]

    # Przetwarzaj kolejne linie i wyodrębniaj artykuły
    for line in lines[1:]:
        if regex.match(article_pattern, line):
            articles.append(current_article)
            current_article = '\n' + line
        elif line.strip():  # Pomijaj puste linie
            current_article += '\n' + line

    articles.append(current_article)

    return articles
