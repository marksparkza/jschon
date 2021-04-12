import urllib.parse

import pytest
from hypothesis import given, provisional as hp

from jschon import URI


@given(hp.urls())
def test_create_uri(value):
    uri = URI(value)
    assert urllib.parse.unquote(str(uri)) == urllib.parse.unquote(value)
    assert eval(repr(uri)) == uri


example = 'http://example.com/foo?bar#baz'


def test_uri_parts():
    uri = URI(example)
    assert uri.scheme == 'http'
    assert uri.authority == 'example.com'
    assert uri.path == '/foo'
    assert uri.query == 'bar'
    assert uri.fragment == 'baz'


@pytest.mark.parametrize('kwargs, result', [
    (dict(), example),
    (dict(scheme=False, authority=False, path=False, query=False, fragment=False), ''),
    (dict(scheme=True, authority=False, path=True, query=False, fragment=True), 'http:/foo#baz'),
    (dict(authority=False, query=False), 'http:/foo#baz'),
    (dict(authority=None, query=None), 'http:/foo#baz'),
    (dict(scheme=False, authority=True, path=False, query=True, fragment=False), '//example.com?bar'),
    (dict(scheme=False, path=False, fragment=False), '//example.com?bar'),
    (dict(scheme=None, path=None, fragment=None), '//example.com?bar'),
    (dict(scheme='https', fragment=''), 'https://example.com/foo?bar#'),
    (dict(authority='elpmaxe.com', path='', query=''), 'http://elpmaxe.com?#baz'),
])
def test_copy_uri(kwargs, result):
    assert URI(example).copy(**kwargs) == URI(result)
