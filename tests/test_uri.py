from hypothesis import given, provisional as hp

from jschon.uri import URI


@given(hp.urls())
def test_create_uri(value):
    uri = URI(value)
    assert str(uri) == value
    assert eval(repr(uri)) == uri
