from flask_admin import tools


def test_encode_decode():
    assert tools.iterdecode(tools.iterencode([1, 2, 3])) == (u'1', u'2', u'3')

    assert tools.iterdecode(tools.iterencode([',', ',', ','])) == (u',', u',', u',')

    assert tools.iterdecode(tools.iterencode(['.hello.,', ',', ','])) == (u'.hello.,', u',', u',')

    assert tools.iterdecode(tools.iterencode(['.....,,,.,,..,.,,.,'])) == (u'.....,,,.,,..,.,,.,',)

    assert tools.iterdecode(tools.iterencode([])) == tuple()

    # Malformed inputs should not crash
    assert tools.iterdecode('.')
    assert tools.iterdecode(',') == (u'', u'')
