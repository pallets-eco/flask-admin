from nose.tools import eq_, ok_

from flask_admin import tools


def test_encode_decode():
    eq_(tools.iterdecode(tools.iterencode([1, 2, 3])), (u'1', u'2', u'3'))

    eq_(tools.iterdecode(tools.iterencode([',', ',', ','])), (u',', u',', u','))

    eq_(tools.iterdecode(tools.iterencode(['.hello.,', ',', ','])), (u'.hello.,', u',', u','))

    eq_(tools.iterdecode(tools.iterencode(['.....,,,.,,..,.,,.,'])), (u'.....,,,.,,..,.,,.,',))

    eq_(tools.iterdecode(tools.iterencode([])), tuple())

    # Malformed inputs should not crash
    ok_(tools.iterdecode('.'))
    eq_(tools.iterdecode(','), (u'', u''))
