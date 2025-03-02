from ShortsMaker import COLORS_DICT


def test_colors_dict_structure():
    # Test that COLORS_DICT is a dictionary
    assert isinstance(COLORS_DICT, dict)

    # Test that all values are RGBA tuples
    for color_value in COLORS_DICT.values():
        assert isinstance(color_value, tuple)
        assert len(color_value) == 4
        for component in color_value:
            assert isinstance(component, int)
            assert 0 <= component <= 255


def test_common_colors_present():
    # Test that some common colors are present
    assert "white" in COLORS_DICT
    assert "black" not in COLORS_DICT
    assert "red" in COLORS_DICT
    assert "blue" in COLORS_DICT
    assert "yellow" in COLORS_DICT


def test_color_values():
    # Test specific color values
    assert COLORS_DICT["white"] == (255, 255, 255, 255)
    assert COLORS_DICT["yellow"] == (255, 255, 0, 255)
    assert COLORS_DICT["cyan"] == (0, 255, 255, 255)
    assert COLORS_DICT["magenta"] == (255, 0, 255, 255)
