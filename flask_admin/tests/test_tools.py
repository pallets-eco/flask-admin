from flask_admin import tools


def test_encode_decode():
    assert tools.iterdecode(tools.iterencode([1, 2, 3])) == ("1", "2", "3")

    assert tools.iterdecode(tools.iterencode([",", ",", ","])) == (",", ",", ",")

    assert tools.iterdecode(tools.iterencode([".hello.,", ",", ","])) == (
        ".hello.,",
        ",",
        ",",
    )

    assert tools.iterdecode(tools.iterencode([".....,,,.,,..,.,,.,"])) == (
        ".....,,,.,,..,.,,.,",
    )

    assert tools.iterdecode(tools.iterencode([])) == tuple()

    # Malformed inputs should not crash
    assert tools.iterdecode(".")
    assert tools.iterdecode(",") == ("", "")
