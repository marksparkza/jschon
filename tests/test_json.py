import json as jsonlib
import tempfile
from random import randint

from hypothesis import assume, given, strategies as hs
from pytest_httpserver import HTTPServer

from jschon import JSON, JSONPointer
from jschon.json import JSONCompatible
from tests.strategies import json, jsonflatarray, jsonflatobject, jsonleaf, jsonnumber, jsonstring
from tests.test_jsonpointer import jsonpointer_escape
from tests.test_validators import isequal


def assert_json_node(
        # actual:
        inst: JSON,

        # expected:
        val: JSONCompatible,
        parent: JSON = None,
        key: str = None,
        ptr: str = '',
):
    assert inst.data == val
    assert inst.parent == parent
    assert inst.key == key
    assert inst.path == JSONPointer(ptr)
    assert isequal(inst.value, val)

    if val is None:
        assert inst.type == "null"
    elif isinstance(val, bool):
        assert inst.type == "boolean"
    elif isinstance(val, (int, float)):
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
    assert_json_node(instance, value)


@given(json)
def test_load_json_from_string(value):
    s = jsonlib.dumps(value)
    instance = JSON.loads(s)
    assert_json_node(instance, value)


@given(json)
def test_load_json_from_file(value):
    s = jsonlib.dumps(value)
    with tempfile.NamedTemporaryFile() as f:
        f.write(s.encode())
        f.flush()
        instance = JSON.loadf(f.name)
    assert_json_node(instance, value)


@given(json)
def test_load_json_from_url(value):
    with HTTPServer() as httpserver:
        httpserver.expect_request('/load.json').respond_with_json(value)
        instance = JSON.loadr(httpserver.url_for('/load.json'))
    assert_json_node(instance, value)


@given(json)
def test_dump_json_to_string(value):
    instance = JSON(value)
    s = instance.dumps()
    obj = jsonlib.loads(s)
    assert isequal(obj, value)


@given(json)
def test_dump_json_to_file(value):
    instance = JSON(value)
    with tempfile.TemporaryDirectory() as tmpdir:
        instance.dumpf(tmpfile := f'{tmpdir}/dump.json')
        with open(tmpfile) as f:
            obj = jsonlib.load(f)
    assert isequal(obj, value)


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


def _cache_json(node):
    node.value
    node.path
    if node.type == 'array':
        for item in node:
            _cache_json(item)
    elif node.type == 'object':
        for item in node.values():
            _cache_json(item)


@given(
    doc=json.filter(lambda x: isinstance(x, (list, dict))),
    val=jsonleaf | jsonflatarray | jsonflatobject,
    data=hs.data(),
)
def test_insert_json(doc, val, data):
    def _insert_values(node, jnode):
        nonlocal inserted

        if isinstance(node, list):
            for i in range(len(node)):
                _insert_values(node[i], jnode[i])
            index = data.draw(hs.integers(min_value=0, max_value=len(node)))
            node.insert(index, val)
            jnode.insert(index, val if randint(0, 1) else JSON(val))
            inserted = True

        elif isinstance(node, dict):
            for k in node:
                _insert_values(node[k], jnode[k])

    inserted = False

    _cache_json(jdoc := JSON(doc))
    _insert_values(doc, jdoc)

    assume(inserted)
    assert_json_node(jdoc, doc)


@given(
    doc=json.filter(lambda x: isinstance(x, (list, dict))),
    val=jsonleaf | jsonflatarray | jsonflatobject,
    data=hs.data(),
)
def test_set_json(doc, val, data):
    def _set_values(node, jnode):
        nonlocal updated

        if isinstance(node, (list, dict)) and node:
            if isinstance(node, list):
                for i in range(len(node)):
                    _set_values(node[i], jnode[i])
                index = data.draw(hs.integers(min_value=0, max_value=len(node) - 1))

            elif isinstance(node, dict):
                for k in node:
                    _set_values(node[k], jnode[k])
                index = data.draw(hs.sampled_from(tuple(node.keys())))

            node[index] = val
            jnode[index] = val if randint(0, 1) else JSON(val)
            updated = True

    updated = False

    _cache_json(jdoc := JSON(doc))
    _set_values(doc, jdoc)

    assume(updated)
    assert_json_node(jdoc, doc)


@given(
    doc=json.filter(lambda x: isinstance(x, (list, dict))),
    data=hs.data(),
)
def test_del_json(doc, data):
    def _del_values(node, jnode):
        nonlocal deleted

        if isinstance(node, (list, dict)) and node:
            if isinstance(node, list):
                for i in range(len(node)):
                    _del_values(node[i], jnode[i])
                index = data.draw(hs.integers(min_value=0, max_value=len(node) - 1))

            elif isinstance(node, dict):
                for k in node:
                    _del_values(node[k], jnode[k])
                index = data.draw(hs.sampled_from(tuple(node.keys())))

            del node[index]
            del jnode[index]
            deleted = True

    deleted = False

    _cache_json(jdoc := JSON(doc))
    _del_values(doc, jdoc)

    assume(deleted)
    assert_json_node(jdoc, doc)
