import pathlib
from copy import deepcopy

import pytest

from jschon.exceptions import JSONPatchError
from jschon.jsonpatch import JSONPatch, JSONPatchOperation
from jschon.utils import json_loadf

# Examples taken from https://datatracker.ietf.org/doc/html/rfc6902#appendix-A
example_file = pathlib.Path(__file__).parent / 'data' / 'jsonpatch.json'


def pytest_generate_tests(metafunc):
    if metafunc.definition.name == 'test_example':
        argnames = ('document', 'patch', 'result')
        argvalues = []
        testids = []
        examples = json_loadf(example_file)
        for example in examples:
            argvalues += [pytest.param(example['document'], example['patch'], example['result'])]
            testids += [example['description']]
        metafunc.parametrize(argnames, argvalues, ids=testids)


def test_example(document, patch, result):
    json_patch_ops = [JSONPatchOperation(**op) for op in patch]
    json_patch = JSONPatch(*patch)
    assert json_patch == JSONPatch(*json_patch_ops)

    original_doc = deepcopy(document)
    if result is not None:
        assert json_patch.evaluate(document) == result
    else:
        with pytest.raises(JSONPatchError):
            json_patch.evaluate(document)

    assert document == original_doc
