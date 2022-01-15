import json as jsonlib
import tempfile
from decimal import Decimal
from typing import Optional

from hypothesis import given

from jschon import JSON, JSONPointer
from jschon.json import JSONCompatible
from tests.strategies import json, json_nodecimal, jsonnumber, jsonstring
from tests.test_jsonpointer import jsonpointer_escape
from tests.test_validators import isequal


def assert_json_node(
        # actual:
        inst: JSON,

        # expected:
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
            # test __getitem__
            assert_json_node(inst[i], el, inst, str(i), f'{ptr}/{i}')
        # test __iter__
        for n, item in enumerate(inst):
            assert_json_node(item, val[n], inst, str(n), f'{ptr}/{n}')

    elif isinstance(val, dict):
        assert inst.type == "object"
        for k, v in val.items():
            # test __getitem__
            assert_json_node(inst[k], v, inst, k, f'{ptr}/{jsonpointer_escape(k)}')
        # test __iter__
        for key, item in inst.items():
            assert_json_node(item, val[key], inst, key, f'{ptr}/{jsonpointer_escape(key)}')

    else:
        assert False

    assert bool(inst) == bool(val)

    if isinstance(val, (str, list, dict)):
        assert len(inst) == len(val)


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


@given(json, json)
def test_json_equality(value1, value2):
    assert isequal(value1, value2) is (value1 == JSON(value2)) is (JSON(value1) == JSON(value2)) is (JSON(value1) == value2)


@given(jsonnumber, jsonnumber)
def test_jsonnumber_inequality(value1, value2):
    assert (value1 < value2) is (value1 < JSON(value2)) is (JSON(value1) < JSON(value2)) is (JSON(value1) < value2)
    assert (value1 <= value2) is (value1 <= JSON(value2)) is (JSON(value1) <= JSON(value2)) is (JSON(value1) <= value2)
    assert (value1 >= value2) is (value1 >= JSON(value2)) is (JSON(value1) >= JSON(value2)) is (JSON(value1) >= value2)
    assert (value1 > value2) is (value1 > JSON(value2)) is (JSON(value1) > JSON(value2)) is (JSON(value1) > value2)


@given(jsonstring, jsonstring)
def test_jsonstring_inequality(value1, value2):
    assert (value1 < value2) is (value1 < JSON(value2)) is (JSON(value1) < JSON(value2)) is (JSON(value1) < value2)
    assert (value1 <= value2) is (value1 <= JSON(value2)) is (JSON(value1) <= JSON(value2)) is (JSON(value1) <= value2)
    assert (value1 >= value2) is (value1 >= JSON(value2)) is (JSON(value1) >= JSON(value2)) is (JSON(value1) >= value2)
    assert (value1 > value2) is (value1 > JSON(value2)) is (JSON(value1) > JSON(value2)) is (JSON(value1) > value2)
