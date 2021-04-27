import json
import pathlib
import tempfile

import pytest

from jschon import Catalogue, CatalogueError, URI, JSONPointer
from tests import example_schema, metaschema_uri_2020_12

json_example = {"foo": "bar"}


@pytest.fixture
def new_catalogue():
    return Catalogue()


def test_new_catalogue(new_catalogue):
    assert not new_catalogue._directories
    assert not new_catalogue._vocabularies
    assert not new_catalogue._format_validators
    assert not new_catalogue._schema_cache


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
def test_add_directory_and_load_json(base_uri, setup_tmpdir, new_catalogue):
    tmpdir_path, subdir_name, jsonfile_name = setup_tmpdir
    new_catalogue.add_directory(URI(base_uri), pathlib.Path(tmpdir_path))
    json_doc = new_catalogue.load_json(URI(f'{base_uri}{subdir_name}/{jsonfile_name}'))
    assert json_doc == json_example
    # incorrect base URI
    with pytest.raises(CatalogueError):
        new_catalogue.load_json(URI(f'http://example.net/{subdir_name}/{jsonfile_name}'))
    # incorrect file name
    with pytest.raises(CatalogueError):
        new_catalogue.load_json(URI(f'{base_uri}{subdir_name}/baz'))


@pytest.mark.parametrize('base_uri', [
    '//example.com/foo/bar/',  # no scheme
    'http://Example.com/foo/bar/',  # not normalized
    'http://example.com/foo/#',  # contains empty fragment
    'http://example.com/foo/#bar',  # contains non-empty fragment
    'http://example.com/foo/bar',  # does not end with '/'
])
def test_add_directory_invalid_uri(base_uri, setup_tmpdir, new_catalogue):
    tmpdir_path, subdir_name, jsonfile_name = setup_tmpdir
    with pytest.raises(CatalogueError):
        new_catalogue.add_directory(URI(base_uri), pathlib.Path(tmpdir_path))


def test_add_directory_invalid_dir(setup_tmpdir, new_catalogue):
    tmpdir_path, subdir_name, jsonfile_name = setup_tmpdir
    # base_dir is a file
    with pytest.raises(CatalogueError):
        new_catalogue.add_directory(URI('http://example.com/'), pathlib.Path(tmpdir_path) / subdir_name / jsonfile_name)
    # base_dir does not exist
    with pytest.raises(CatalogueError):
        new_catalogue.add_directory(URI('http://example.com/'), pathlib.Path(tmpdir_path) / 'foo')


@pytest.mark.parametrize('uri', [
    '//example.com/foo/bar/file.json',  # no scheme
    'http://Example.com/foo/bar/file.json',  # not normalized
    'http://example.com/foo/file.json#',  # contains empty fragment
    'http://example.com/foo/file.json#bar',  # contains non-empty fragment
])
def test_load_json_invalid_uri(uri, new_catalogue):
    with pytest.raises(CatalogueError):
        new_catalogue.load_json(URI(uri))


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
def test_get_vocabulary(uri, is_known, catalogue):
    if is_known:
        vocabulary = catalogue.get_vocabulary(URI(uri))
        assert vocabulary.uri == uri
    else:
        with pytest.raises(CatalogueError):
            catalogue.get_vocabulary(URI(uri))


@pytest.fixture
def example_schema_uri(catalogue):
    schema = catalogue.create_schema(example_schema, metaschema_uri=metaschema_uri_2020_12)
    return schema.uri


@pytest.mark.parametrize('ptr, is_schema', [
    ("", True),
    ("/$id", False),
    ("/$defs", False),
    ("/if", True),
    ("/then", True),
    ("/else", True),
])
def test_get_schema(example_schema_uri, ptr, is_schema, catalogue):
    uri = example_schema_uri.copy(fragment=ptr)
    if is_schema:
        subschema = catalogue.get_schema(uri)
        assert JSONPointer(ptr).evaluate(example_schema) == subschema
    else:
        with pytest.raises(CatalogueError):
            catalogue.get_schema(uri)
