def test_fix_text_basic(shorts_maker):
    source_txt = "This is a te st sentence."
    expected_output = "This is a test sentence."
    assert shorts_maker.fix_text(source_txt) == expected_output


def test_fix_text_with_escape_characters(shorts_maker):
    source_txt = "This is a\t test sentence.\nThis is another test sentence.\r"
    expected_output = "This is a test sentence. This is another test sentence."
    assert shorts_maker.fix_text(source_txt) == expected_output


def test_fix_text_with_punctuations(shorts_maker):
    source_txt = "Helllo!! How are you? I'm fine."
    expected_output = "Hello!! How are you? I'm fine."
    assert shorts_maker.fix_text(source_txt) == expected_output


def test_fix_text_with_unicode(shorts_maker):
    source_txt = "Café is a Frnch word."
    expected_output = "Café is a French word."
    assert shorts_maker.fix_text(source_txt) == expected_output


def test_fix_text_with_multiple_spaces(shorts_maker):
    source_txt = "This  is   a    test."
    expected_output = "This is a test."
    assert shorts_maker.fix_text(source_txt) == expected_output
