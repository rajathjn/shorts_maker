from ShortsMaker import abbreviation_replacer


def test_abbreviation_replacer_basic_replacement():
    text = "This is an example ABB."
    abbreviation = "ABB"
    replacement = "abbreviation"
    result = abbreviation_replacer(text, abbreviation, replacement)
    assert result == "This is an example abbreviation."


def test_abbreviation_replacer_replacement_with_padding():
    text = "This is an example ABB."
    abbreviation = "ABB"
    replacement = "abbreviation"
    padding = "."
    result = abbreviation_replacer(text, abbreviation, replacement, padding=padding)
    assert result == "This is an example abbreviation"


def test_abbreviation_replacer_multiple_occurrences():
    text = "ABB is an ABBbreviation ABB."
    abbreviation = "ABB"
    replacement = "abbreviation"
    result = abbreviation_replacer(text, abbreviation, replacement)
    assert result == "abbreviation is an abbreviationbreviation abbreviation."


def test_abbreviation_replacer_no_match():
    text = "No match here."
    abbreviation = "XYZ"
    replacement = "something"
    result = abbreviation_replacer(text, abbreviation, replacement)
    assert result == text


def test_abbreviation_replacer_empty_string():
    text = ""
    abbreviation = "ABB"
    replacement = "abbreviation"
    result = abbreviation_replacer(text, abbreviation, replacement)
    assert result == ""
