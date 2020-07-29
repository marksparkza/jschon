from hypothesis import given

from jschon.json import *
from jschon.jsonpointer import JSONPointer
from tests.strategies import json
from tests.test_jsonpointer import jsonpointer_escape


@given(json)
def test_create_json(value):

    def assert_node(inst, val, loc):
        assert inst.value == val
        assert inst.location == JSONPointer(loc)
        if val is None:
            assert type(inst) is JSONNull
        elif isinstance(val, bool):
            assert type(inst) is JSONBoolean
        elif isinstance(val, int):
            assert type(inst) is JSONInteger
        elif isinstance(val, float):
            assert type(inst) is JSONNumber
        elif isinstance(val, str):
            assert type(inst) is JSONString
        elif isinstance(val, list):
            assert type(inst) is JSONArray
            for i, el in enumerate(val):
                assert_node(inst[i], el, f'{inst.location}/{i}')
        elif isinstance(val, dict):
            assert type(inst) is JSONObject
            for k, v in val.items():
                assert_node(inst[k], v, f'{inst.location}/{jsonpointer_escape(k)}')
        else:
            assert False

    instance = JSON(value)
    assert_node(instance, value, '')