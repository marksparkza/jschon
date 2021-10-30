import json as jsonlib
import tempfile
from decimal import Decimal
from typing import Optional

import pytest
from hypothesis import given

from jschon import JSON, JSONPointer
from jschon.json import JSONCompatible
from tests.strategies import json, json_nodecimal
from tests.test_jsonpointer import jsonpointer_escape
from tests.test_validators import isequal


def assert_json_node(
        inst: JSON,
        val: JSONCompatible,
        parent: Optional[JSON],
        key: Optional[str],
        ptr: str,
):
    assert inst.data == (Decimal(f'{val}') if isinstance(val, float) else val)
    assert inst.parent == parent
    assert inst.key == key
    assert inst.path == JSONPointer(ptr)
    assert isequal(inst.value, val)

    if val is None:
        assert inst.type == "null"
    elif isinstance(val, bool):
        assert inst.type == "boolean"
    elif isinstance(val, (int, float, Decimal)):
        assert inst.type == "number"
    elif isinstance(val, str):
        assert inst.type == "string"
    elif isinstance(val, list):
        assert inst.type == "array"
        for i, el in enumerate(val):
            assert_json_node(inst[i], el, inst, str(i), f'{inst.path}/{i}')
    elif isinstance(val, dict):
        assert inst.type == "object"
        for k, v in val.items():
            assert_json_node(inst[k], v, inst, k, f'{inst.path}/{jsonpointer_escape(k)}')
    else:
        assert False

    assert bool(inst) == bool(val)

    if isinstance(val, (str, list, dict)):
        assert len(inst) == len(val)
    else:
        with pytest.raises(TypeError):
            len(inst)

    if not isinstance(val, (list, dict)):
        with pytest.raises(TypeError):
            iter(inst)

    if not isinstance(val, list):
        with pytest.raises(TypeError):
            _ = inst[0]

    if not isinstance(val, dict):
        with pytest.raises(TypeError):
            _ = inst['']


@given(json)
def test_create_json(value):
    instance = JSON(value)
    assert_json_node(instance, value, None, None, '')


@given(json_nodecimal)
def test_load_json_from_string(value):
    s = jsonlib.dumps(value)
    instance = JSON.loads(s)
    assert_json_node(instance, value, None, None, '')


@given(json_nodecimal)
def test_load_json_from_file(value):
    s = jsonlib.dumps(value)
    with tempfile.NamedTemporaryFile() as f:
        f.write(s.encode())
        f.flush()
        instance = JSON.loadf(f.name)
    assert_json_node(instance, value, None, None, '')
