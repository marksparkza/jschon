import pytest

from jschon import JSONSchemaError, URI, create_catalog
from jschon.vocabulary import Metaschema
from tests import (
    metaschema_uri_2020_12,
    core_vocab_uri_2019_09, core_vocab_uri_2020_12, core_vocab_uri_next,
)

@pytest.mark.parametrize('vocab_data', [
    None,
    {
        'https://example.com/whatever': True,
    },
    {
        str(core_vocab_uri_2020_12): True,
        str(core_vocab_uri_next): True,
    },
])
def test_metaschema_no_core(vocab_data):
    catalog = create_catalog('2019-09', '2020-12', 'next')

    metaschema_id = 'https://example.com/no-core'
    metaschema_data = {
        '$schema': str(metaschema_uri_2020_12),
        '$id': metaschema_id,
    }
    if vocab_data:
        metaschema_data['$vocabulary'] = vocab_data
        for vocab in vocab_data:
            catalog.create_vocabulary(URI(vocab))

    with pytest.raises(JSONSchemaError):
        Metaschema(catalog, metaschema_data, uri=URI(metaschema_id))

def test_detect_core(catalog):
    metaschema_id = 'https://example.com/meta'
    metaschema_uri = URI(metaschema_id)
    metaschema_data = {
        '$schema': str(metaschema_uri_2020_12),
        '$id': metaschema_id,
        '$vocabulary': {
            str(core_vocab_uri_2020_12): True,
        },
    }
    m = Metaschema(catalog, metaschema_data, uri=metaschema_uri)

    m1 = catalog._schema_cache['__meta__'][metaschema_uri]
    m2 = catalog.get_metaschema(metaschema_uri)

    assert m1 is m
    assert m2 is m

def test_default_core(catalog):
    metaschema_id = 'https://example.com/meta'
    metaschema_uri = URI(metaschema_id)
    metaschema_data = {
        '$schema': str(metaschema_uri_2020_12),
        '$id': metaschema_id,
    }
    core = catalog.get_vocabulary(core_vocab_uri_2020_12)
    m = Metaschema(
        catalog,
        metaschema_data,
        core,
        uri=metaschema_uri,
    )
    assert m.core_vocabulary is core
