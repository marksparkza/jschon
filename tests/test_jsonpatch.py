import pathlib

import pytest

from jschon.exceptions import JSONPatchError
from jschon.jsonpatch import JSONPatch
from jschon.utils import json_loadf

# Examples taken from https://datatracker.ietf.org/doc/html/rfc6902#appendix-A
example_file = pathlib.Path(__file__).parent / 'jsonpatch_examples.json'


def pytest_generate_tests(metafunc):
    argnames = ('document', 'patch', 'result')
    argvalues = []
    testids = []
    examples = json_loadf(example_file)
    for example in examples:
        argvalues += [pytest.param(example['document'], example['patch'], example['result'])]
        testids += [example['description']]
    metafunc.parametrize(argnames, argvalues, ids=testids)


def test_example(document, patch, result):
    if result is not None:
        assert JSONPatch(*patch).evaluate(document) == result
    else:
        with pytest.raises(JSONPatchError):
            JSONPatch(*patch).evaluate(document)
