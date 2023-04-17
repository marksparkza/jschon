import pytest

from jschon import URIError, JSONSchema

@pytest.mark.parametrize('draft', ('2019-09', '2020-12', 'next'))
def test_non_normalized_id_allowed(draft):
    schema_data = {
        '$schema': f'https://json-schema.org/draft/{draft}/schema',
        '$id': 'http://localhost:1234/foo/bar/../baz',
    }
    schema = JSONSchema(schema_data)
    assert schema['$id'] == schema_data['$id']


@pytest.mark.parametrize('draft', ('2019-09', '2020-12', 'next'))
def test_nonempty_fragment_id_disallowed(draft):
    schema_data = {
        '$schema': f'https://json-schema.org/draft/{draft}/schema',
        '$id': '#foo',
    }
    error = (
        'has a non-empty fragment'
        if draft in ['2019-09', '2020-12']
        else 'has a fragment'
    )
    with pytest.raises(URIError, match=error):
        JSONSchema(schema_data)


@pytest.mark.parametrize('draft', ('2019-09', '2020-12'))
def test_empty_fragment_id_allowed(draft):
    schema_data = {
        '$schema': f'https://json-schema.org/draft/{draft}/schema',
        '$id': '/foo/bar#',
    }
    schema = JSONSchema(schema_data)
    assert schema['$id'] == schema_data['$id']


@pytest.mark.parametrize('draft', ('next',))
def test_empty_fragment_id_disallowed(draft):
    schema_data = {
        '$schema': f'https://json-schema.org/draft/{draft}/schema',
        '$id': '/foo/bar#',
    }
    with pytest.raises(URIError, match='has a fragment'):
        JSONSchema(schema_data)
