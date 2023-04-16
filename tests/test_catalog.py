import json
import pathlib
import tempfile
import uuid
import itertools
import re

import pytest
from unittest.mock import patch

from jschon import (
    Catalog,
    CatalogError,
    URI,
    JSONPointer,
    JSONSchema,
    JSON,
    create_catalog,
    LocalSource,
    RemoteSource,
)
from jschon.vocabulary import Metaschema, Keyword
from tests import example_schema, metaschema_uri_2020_12, core_vocab_uri_2020_12

json_example = {"foo": "bar"}


@pytest.fixture
def local_catalog():
    catalog = create_catalog(
        '2019-09', '2020-12', 'next',
        name='local'
    )
    catalog.add_uri_source(
        URI('https://example.com/'),
        LocalSource(
            pathlib.Path(__file__).parent / 'data',
            suffix='.json',
        ),
    )
    return catalog


@pytest.fixture
def new_catalog() -> Catalog:
    return Catalog(name=str(uuid.uuid4()))


def test_new_catalog(new_catalog):
    assert not new_catalog._uri_sources
    assert not new_catalog._vocabularies
    assert not new_catalog._schema_cache
    assert not new_catalog._enabled_formats


def test_missing_catalog():
    name='some-name'
    with pytest.raises(CatalogError, match=f'"{name}" not found'):
        Catalog.get_catalog(name)


@pytest.fixture
def setup_tmpdir():
    """Create a temp dir hierarchy containing a JSON file.
    
    Yield (tmpdir path, subdir name, file name) and clean up
    afterwards.
    """
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with tempfile.TemporaryDirectory(dir=tmpdir_path) as subdir_path:
            with tempfile.NamedTemporaryFile(dir=subdir_path) as f:
                f.write(json.dumps(json_example).encode())
                f.flush()
                yield tmpdir_path, pathlib.Path(subdir_path).name, pathlib.Path(f.name).name


@pytest.mark.parametrize('base_uri', [
    'http://example.com/',
    'http://example.com/foo/',
    'http://example.com/foo/bar/',
])
def test_local_source(base_uri, setup_tmpdir, new_catalog):
    tmpdir_path, subdir_name, jsonfile_name = setup_tmpdir
    new_catalog.add_uri_source(URI(base_uri), LocalSource(pathlib.Path(tmpdir_path)))
    json_doc = new_catalog.load_json(URI(f'{base_uri}{subdir_name}/{jsonfile_name}'))
    assert json_doc == json_example
    # incorrect base URI
    with pytest.raises(CatalogError):
        new_catalog.load_json(URI(f'http://example.net/{subdir_name}/{jsonfile_name}'))
    # incorrect file name
    with pytest.raises(CatalogError):
        new_catalog.load_json(URI(f'{base_uri}{subdir_name}/baz'))


def test_local_source_file_not_found(local_catalog):
    stem = 'not-there'
    fullname = str(pathlib.Path(__file__).parent / 'data' / f'{stem}.json')
    with pytest.raises(CatalogError, match=f"'{re.escape(fullname)}'$"):
        local_catalog.get_schema(URI(f'https://example.com/{stem}'))


def test_local_source_ioerror_no_file(local_catalog):
    with patch('builtins.open') as m:
        # This plain IOError will have an empty string as the message,
        # without a filename that triggers different exception handling.
        m.side_effect = IOError
        with pytest.raises(CatalogError, match=r'^$'):
            local_catalog.get_schema(URI('https://example.com/does-not-matter'))


@pytest.mark.parametrize('base_uri', [
    'http://example.com/',
    'http://example.com/foo/',
    'http://example.com/foo/bar/',
])
def test_remote_source(base_uri, httpserver, new_catalog):
    new_catalog.add_uri_source(URI(base_uri), RemoteSource(URI(httpserver.url_for(''))))
    httpserver.expect_request('/baz/quux').respond_with_json(json_example)
    json_doc = new_catalog.load_json(URI(f'{base_uri}baz/quux'))
    assert json_doc == json_example
    # incorrect base URI
    with pytest.raises(CatalogError):
        new_catalog.load_json(URI('http://example.net/baz/quux'))
    # incorrect path
    with pytest.raises(CatalogError):
        new_catalog.load_json(URI(f'{base_uri}baz/quuz'))


@pytest.mark.parametrize('base_uri', [
    '//example.com/foo/bar/',  # no scheme
    'http://Example.com/foo/bar/',  # not normalized
    'http://example.com/foo/#',  # contains empty fragment
    'http://example.com/foo/#bar',  # contains non-empty fragment
    'http://example.com/foo/bar',  # does not end with '/'
])
def test_uri_source_invalid_uri(base_uri, new_catalog):
    with pytest.raises(CatalogError):
        new_catalog.add_uri_source(URI(base_uri), LocalSource('/'))


@pytest.mark.parametrize('uri', [
    '//example.com/foo/bar/file.json',  # no scheme
    'http://Example.com/foo/bar/file.json',  # not normalized
    'http://example.com/foo/file.json#',  # contains empty fragment
    'http://example.com/foo/file.json#bar',  # contains non-empty fragment
])
def test_load_json_invalid_uri(uri, new_catalog):
    with pytest.raises(CatalogError):
        new_catalog.load_json(URI(uri))


@pytest.mark.parametrize('uri, is_known', [
    ("https://json-schema.org/draft/2020-12/vocab/core", True),
    ("https://json-schema.org/draft/2020-12/vocab/applicator", True),
    ("https://json-schema.org/draft/2020-12/vocab/unevaluated", True),
    ("https://json-schema.org/draft/2020-12/vocab/validation", True),
    ("https://json-schema.org/draft/2020-12/vocab/meta-data", True),
    ("https://json-schema.org/draft/2020-12/vocab/format-annotation", True),
    ("https://json-schema.org/draft/2020-12/meta/format-assertion", False),
    ("https://json-schema.org/draft/2020-12/vocab/content", True),
])
def test_get_vocabulary(uri, is_known, catalog):
    if is_known:
        vocabulary = catalog.get_vocabulary(URI(uri))
        assert vocabulary.uri == uri
    else:
        with pytest.raises(CatalogError):
            catalog.get_vocabulary(URI(uri))


def test_create_vocabulary(catalog):
    class CustomKeyword(Keyword):
        key = 'custom'

    custom_uri = URI('https://example.com/custom')
    custom_vocab = catalog.create_vocabulary(custom_uri, CustomKeyword)
    assert custom_vocab.uri is custom_uri
    assert custom_vocab.kwclasses == {CustomKeyword.key: CustomKeyword}
    assert catalog.get_vocabulary(custom_uri) is custom_vocab


@pytest.fixture
def example_schema_uri():
    schema = JSONSchema(example_schema)
    return schema.uri


@pytest.mark.parametrize('ptr, is_schema', [
    ("", True),
    ("/$id", False),
    ("/$defs", False),
    ("/if", True),
    ("/then", True),
    ("/else", True),
])
def test_get_schema(example_schema_uri, ptr, is_schema, catalog):
    uri = example_schema_uri.copy(fragment=ptr)
    if is_schema:
        subschema = catalog.get_schema(uri)
        assert JSONPointer(ptr).evaluate(example_schema) == subschema
    else:
        with pytest.raises(CatalogError):
            catalog.get_schema(uri)


def cached_schema(uri, schema, cacheid):
    kwargs = {'uri': uri, 'metaschema_uri': metaschema_uri_2020_12}
    if cacheid is not None:
        kwargs['cacheid'] = cacheid
    return JSONSchema(schema, **kwargs)


def test_cache_independence(catalog):
    uri = URI("http://example.com")
    cached_schema(uri, {"const": 0}, None)  # 'default' cache
    cached_schema(uri, {"const": 1}, 'one')
    cached_schema(uri, {"const": 2}, 'two')
    assert catalog.get_schema(uri)["const"] == 0
    assert catalog.get_schema(uri, cacheid='default')["const"] == 0
    assert catalog.get_schema(uri, cacheid='one')["const"] == 1
    assert catalog.get_schema(uri, cacheid='two')["const"] == 2


def test_enable_formats(catalog):
    assert catalog.is_format_enabled('date') is False
    assert catalog.is_format_enabled('time') is False

    catalog.enable_formats('date', 'time')

    assert catalog.is_format_enabled('date') is True
    assert catalog.is_format_enabled('time') is True


def test_context_manager_with_id(catalog):
    new_id = 'new'
    with catalog.cache(new_id) as cache_id:
        assert cache_id is new_id


def test_context_manager_id_in_use(catalog):
    # Ensure the 'default' cache has at least one schema in it.
    JSONSchema({'$schema': 'https://json-schema.org/draft/2020-12/schema'})

    with pytest.raises(CatalogError, match='already in use'):
        with catalog.cache('default'):
            pass


def test_context_manager_no_id(catalog):
    with catalog.cache() as cache_id:
        assert isinstance(cache_id, uuid.UUID)


def test_del_schema_nonexistent_cache(catalog):
    dne = 'doesnotexist'
    assert dne not in catalog._schema_cache
    assert catalog.del_schema(URI('irrelevant'), cacheid=dne) is None
    assert dne not in catalog._schema_cache


def test_metaschema_isolation():
    # mask the metaschema with a boolean false schema, in the fubar cache
    cached_schema(metaschema_uri_2020_12, False, 'fubar')
    uri = URI("http://example.com")
    fubar_schema = cached_schema(uri, {"$ref": str(metaschema_uri_2020_12)}, 'fubar')
    assert fubar_schema.evaluate(JSON(True)).valid is False

    # masking the metaschema has no impact on other caches
    okay_schema = cached_schema(uri, {"$ref": str(metaschema_uri_2020_12)}, 'okay')
    assert okay_schema.evaluate(JSON(True)).valid is True
    okay_schema = cached_schema(uri, {"$ref": str(metaschema_uri_2020_12)}, None)
    assert okay_schema.evaluate(JSON(True)).valid is True


def test_get_metaschema_detect_core(local_catalog):
    uri = URI('https://example.com/meta_with_core')
    core_vocab = local_catalog.get_vocabulary(core_vocab_uri_2020_12)

    m = local_catalog.get_metaschema(uri)
    assert isinstance(m, Metaschema)
    assert m['$id'].data == str(uri)
    assert m.core_vocabulary is core_vocab
    assert m.kwclasses == core_vocab.kwclasses

    s = local_catalog.get_schema(uri)
    assert isinstance(s, JSONSchema)
    assert s is not m
    assert s == m


def test_get_metaschema_wrong_type(local_catalog):
    uri = URI('https://example.com/meta_with_core')
    non_meta = local_catalog.get_schema(uri)
    local_catalog.add_schema(uri, non_meta, cacheid='__meta__')
    with pytest.raises(CatalogError, match='not a metaschema'):
        local_catalog.get_metaschema(uri)


def test_get_metaschema_invalid(local_catalog):
    uri = URI('https://example.com/meta_invalid')
    with pytest.raises(CatalogError, match='metaschema is invalid'):
        local_catalog.create_metaschema(uri)


def test_create_metaschema_no_vocabs(local_catalog):
    class ExtraKeyword(Keyword):
        key = 'extra'

    uri = URI('https://example.com/meta_no_vocabs')
    core_vocab = local_catalog.get_vocabulary(core_vocab_uri_2020_12)
    applicator_vocab = local_catalog.get_vocabulary(
        URI('https://json-schema.org/draft/2020-12/vocab/applicator')
    )

    extra_vocab = local_catalog.create_vocabulary(
        URI('https://example.com/vocab/whatever'),
        ExtraKeyword,
    )

    m = local_catalog.create_metaschema(
        uri,
        core_vocab.uri,
        applicator_vocab.uri,
        extra_vocab.uri,
    )
    assert isinstance(m, Metaschema)
    assert m['$id'].data == str(uri)
    assert m.core_vocabulary is core_vocab
    assert m.kwclasses.keys() == frozenset(
        itertools.chain.from_iterable([
            v.kwclasses.keys() for v in
            [core_vocab, applicator_vocab, extra_vocab]
        ])
    )
    m1 = local_catalog.get_metaschema(uri)
    assert m1 is m
