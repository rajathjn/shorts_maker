from ShortsMaker import has_alpha_and_digit


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
