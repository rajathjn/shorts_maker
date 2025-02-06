from ShortsMaker import abbreviation_replacer, has_alpha_and_digit, split_alpha_and_digit


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


def test_has_alpha_and_digit_with_alphanumeric_input():
    assert has_alpha_and_digit("a1") is True


def test_has_alpha_and_digit_with_only_alpha_input():
    assert has_alpha_and_digit("abc") is False


def test_has_alpha_and_digit_with_only_digit_input():
    assert has_alpha_and_digit("1234") is False


def test_has_alpha_and_digit_with_empty_string():
    assert has_alpha_and_digit("") is False


def test_has_alpha_and_digit_with_special_characters():
    assert has_alpha_and_digit("a@1") is True


def test_has_alpha_and_digit_with_whitespace():
    assert has_alpha_and_digit("a1 ") is True


def test_has_alpha_and_digit_with_uppercase_letters():
    assert has_alpha_and_digit("A1") is True


def test_split_alpha_and_digit_with_alphanumeric_word():
    result = split_alpha_and_digit("abc123")
    assert result == "abc 123"


def test_split_alpha_and_digit_with_digits_and_letters_interleaved():
    result = split_alpha_and_digit("a1b2c3")
    assert result == "a 1 b 2 c 3"


def test_split_alpha_and_digit_with_only_letters():
    result = split_alpha_and_digit("abcdef")
    assert result == "abcdef"


def test_split_alpha_and_digit_with_only_digits():
    result = split_alpha_and_digit("123456")
    assert result == "123456"


def test_split_alpha_and_digit_with_empty_string():
    result = split_alpha_and_digit("")
    assert result == ""


def test_split_alpha_and_digit_with_special_characters():
    result = split_alpha_and_digit("a1!b2@")
    assert result == "a 1! b 2@"


def test_split_alpha_and_digit_with_spaces_and_tabs():
    result = split_alpha_and_digit("a1 b2\tc3")
    assert result == "a 1  b 2\t c 3"


def test_split_alpha_and_digit_with_uppercase_and_numbers():
    result = split_alpha_and_digit("ABC123")
    assert result == "ABC 123"
