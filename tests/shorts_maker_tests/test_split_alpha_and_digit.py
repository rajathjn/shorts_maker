from ShortsMaker import split_alpha_and_digit


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
