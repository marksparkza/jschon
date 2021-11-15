import json
import pathlib
import tempfile
import uuid

import pytest

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
from tests import example_schema, metaschema_uri_2020_12

json_example = {"foo": "bar"}


@pytest.fixture
def new_catalog() -> Catalog:
    return Catalog(name=str(uuid.uuid4()))


def test_new_catalog(new_catalog):
    assert not new_catalog._uri_sources
    assert not new_catalog._vocabularies
    assert not new_catalog._format_validators
    assert not new_catalog._schema_cache


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


@pytest.fixture
def example_schema_uri():
    schema = JSONSchema(example_schema, metaschema_uri=metaschema_uri_2020_12)
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


def sessioned_schema(uri, schema, session):
    kwargs = {'uri': uri, 'metaschema_uri': metaschema_uri_2020_12}
    if session is not None:
        kwargs['session'] = session
    return JSONSchema(schema, **kwargs)


def test_session_independence(catalog):
    uri = URI("http://example.com")
    sessioned_schema(uri, {"const": 0}, None)  # 'default' session
    sessioned_schema(uri, {"const": 1}, 'one')
    sessioned_schema(uri, {"const": 2}, 'two')
    assert catalog.get_schema(uri)["const"] == 0
    assert catalog.get_schema(uri, session='default')["const"] == 0
    assert catalog.get_schema(uri, session='one')["const"] == 1
    assert catalog.get_schema(uri, session='two')["const"] == 2


def test_metaschema_isolation():
    new_catalog = create_catalog('2019-09', '2020-12', name=str(uuid.uuid4()))
    assert new_catalog._schema_cache.keys() == {'__meta__'}

    # mask the metaschema with a boolean false schema, in the fubar session
    sessioned_schema(metaschema_uri_2020_12, False, 'fubar')
    uri = URI("http://example.com")
    fubar_schema = sessioned_schema(uri, {"$ref": str(metaschema_uri_2020_12)}, 'fubar')
    assert fubar_schema.evaluate(JSON(True)).valid is False

    # masking the metaschema has no impact on other sessions
    okay_schema = sessioned_schema(uri, {"$ref": str(metaschema_uri_2020_12)}, 'okay')
    assert okay_schema.evaluate(JSON(True)).valid is True
    okay_schema = sessioned_schema(uri, {"$ref": str(metaschema_uri_2020_12)}, None)
    assert okay_schema.evaluate(JSON(True)).valid is True
