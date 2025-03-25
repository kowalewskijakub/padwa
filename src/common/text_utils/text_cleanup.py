# wersja: chet-theia

from regex import regex


def clean_stamps(text: str):
    """
    Usuwa z tekstu publikowanego przez Kancelarię Sejmu oznaczenia i inne elementy dekoracyjne.

    :param text: Tekst do przetworzenia (głównie: akt prawny o randze ustawowej)
    :return: Tekst po usunięciu oznaczeń
    """
    patterns = [
        {'pattern': r'©Kancelaria Sejmu', 'replacement': ''},
        {'pattern': r's\.\s*\d+\/\d+', 'replacement': ''},
        {'pattern': r'\d{4}-\d{2}-\d{2}', 'replacement': ''},
        {'pattern': r'Prezydent Rzeczypospolitej Polskiej:.*', 'replacement': ''},
        {'pattern': r'Dziennik Ustaw.*Poz\. \d{1,4}', 'replacement': ''},
        {'pattern': r'^\n', 'replacement': ''},
    ]

    for pattern_dict in patterns:
        pattern = pattern_dict['pattern']
        replacement = pattern_dict['replacement']
        text = regex.sub(pattern, replacement, text, flags=regex.MULTILINE)

    return text


def clean_hyphenation(text: str):
    """
    Usuwa dewizy używane przy przenoszeniu wyrazów między liniami.

    :param text: Tekst do przetworzenia
    :return: Tekst po usunięciu dewizów
    """
    pattern = r'(\b\w+)-\s+(\w+\b)'
    return regex.sub(pattern, r'\1\2', text, flags=regex.UNICODE)
