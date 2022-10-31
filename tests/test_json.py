import json as jsonlib
import pathlib
import tempfile
from copy import deepcopy
from random import randint

import pytest
from hypothesis import assume, given, strategies as hs
from pytest_httpserver import HTTPServer

from jschon import JSON, JSONCompatible, JSONError, JSONPatch, JSONPointer
from jschon.json import false, null, true
from jschon.utils import json_loadf
from tests.strategies import json, jsonflatarray, jsonflatobject, jsonleaf, jsonnumber, jsonstring
from tests.test_jsonpointer import generate_jsonpointers, jsonpointer_escape
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
def test_json_create(value):
    instance = JSON(value)
    assert_json_node(instance, value)


@given(json)
def test_json_loads(value):
    s = jsonlib.dumps(value)
    instance = JSON.loads(s)
    assert_json_node(instance, value)


@given(json)
def test_json_loadf(value):
    s = jsonlib.dumps(value)
    with tempfile.NamedTemporaryFile() as f:
        f.write(s.encode())
        f.flush()
        instance = JSON.loadf(f.name)
    assert_json_node(instance, value)


@given(json)
def test_json_loadr(value):
    with HTTPServer() as httpserver:
        httpserver.expect_request('/load.json').respond_with_json(value)
        instance = JSON.loadr(httpserver.url_for('/load.json'))
    assert_json_node(instance, value)


@given(json)
def test_json_dumps(value):
    instance = JSON(value)
    s = instance.dumps()
    obj = jsonlib.loads(s)
    assert isequal(obj, value)


@given(json)
def test_json_dumpf(value):
    instance = JSON(value)
    with tempfile.TemporaryDirectory() as tmpdir:
        instance.dumpf(tmpfile := f'{tmpdir}/dump.json')
        with open(tmpfile) as f:
            obj = jsonlib.load(f)
    assert isequal(obj, value)


@given(json, json)
def test_json_eq(value1, value2):
    assert isequal(value1, value2) is (value1 == JSON(value2)) is (JSON(value1) == JSON(value2)) is (JSON(value1) == value2)


@given(jsonnumber, jsonnumber)
def test_json_number(value1, value2):
    assert (value1 < value2) is (value1 < JSON(value2)) is (JSON(value1) < JSON(value2)) is (JSON(value1) < value2)
    assert (value1 <= value2) is (value1 <= JSON(value2)) is (JSON(value1) <= JSON(value2)) is (JSON(value1) <= value2)
    assert (value1 >= value2) is (value1 >= JSON(value2)) is (JSON(value1) >= JSON(value2)) is (JSON(value1) >= value2)
    assert (value1 > value2) is (value1 > JSON(value2)) is (JSON(value1) > JSON(value2)) is (JSON(value1) > value2)


@given(jsonstring, jsonstring)
def test_json_string(value1, value2):
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
def test_json_insert(doc, val, data):
    def _insert_values(node, jnode):
        nonlocal inserted

        if isinstance(node, list):
            for i in range(len(node)):
                _insert_values(node[i], jnode[i])

            index = data.draw(hs.integers(min_value=0, max_value=len(node)))
            ins_val = data.draw(hs.sampled_from((val, JSON(val))))
            node.insert(index, val)
            jnode.insert(index, ins_val)
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
def test_json_setitem(doc, val, data):
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

            set_val = data.draw(hs.sampled_from((val, JSON(val))))
            node[index] = val
            jnode[index] = set_val
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
def test_json_delitem(doc, data):
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


def pytest_generate_tests(metafunc):
    if metafunc.definition.name == 'test_json_patch_example':
        argnames = ('document', 'patch', 'result')
        argvalues = []
        testids = []
        example_file = pathlib.Path(__file__).parent / 'data' / 'jsonpatch.json'
        examples = json_loadf(example_file)
        for example in examples:
            argvalues += [pytest.param(
                example['document'],
                example['patch'],
                example['result'],
            )]
            testids += [example['description']]
        metafunc.parametrize(argnames, argvalues, ids=testids)


def test_json_patch_example(document, patch, result):
    jsondoc = JSON(document)
    jsonpatch = JSONPatch(*patch)

    op = jsonpatch[0]
    original_value = deepcopy(op.value)
    path = op.path if randint(0, 1) else JSONPointer(op.path)
    value = op.value if randint(0, 1) else JSON(op.value)

    if op.op == 'add':
        if result is not None:
            jsondoc.add(path, value)
            assert_json_node(jsondoc, result)
        else:
            with pytest.raises(JSONError):
                jsondoc.add(path, value)

    elif op.op == 'remove':
        jsondoc.remove(path)
        assert_json_node(jsondoc, result)

    elif op.op == 'replace':
        jsondoc.replace(path, value)
        assert_json_node(jsondoc, result)

    assert op.value == original_value


@given(
    doc=json.filter(lambda x: isinstance(x, (list, dict))),
    val=jsonleaf | jsonflatarray | jsonflatobject,
    data=hs.data(),
)
def test_json_add(doc, val, data):
    _cache_json(jdoc := JSON(doc))

    # select a JSON node (jnode) on which to call add
    generate_jsonpointers(nodes := {}, doc)
    node_path = data.draw(hs.sampled_from(list(nodes.keys())))
    jnode = JSONPointer(node_path).evaluate(jdoc)

    # select a target (add_ptr) relative to jnode
    generate_jsonpointers(targets := {}, jnode.value)
    add_path = data.draw(hs.sampled_from(list(targets.keys())))
    add_ptr = JSONPointer(add_path)
    add_val = data.draw(hs.sampled_from((val, JSON(val))))

    # the target relative to root
    target_ptr = JSONPointer(node_path + add_path)

    if not target_ptr:
        # replace the whole doc with val
        add_ptr = data.draw(hs.sampled_from((add_path, add_ptr)))
        jnode.add(add_ptr, add_val)
        assert_json_node(jdoc, val)
        return

    target_parent = target_ptr[:-1].evaluate(doc)
    target_key = target_ptr[-1]

    if isinstance(target_parent, list):
        if not add_ptr:
            # replace the target item with val
            target_parent[int(target_key)] = val
        else:
            if data.draw(hs.booleans()):
                # insert val at the selected index
                target_idx = int(target_key)
            else:
                # append val
                target_idx = len(target_parent)
                add_ptr = add_ptr[:-1] / '-'

            target_parent.insert(target_idx, val)

    elif isinstance(target_parent, dict):
        if add_ptr:
            if data.draw(hs.booleans()):
                # add a new key
                target_key = data.draw(hs.text())
                add_ptr = add_ptr[:-1] / target_key

        target_parent[target_key] = val

    else:
        assert False

    add_ptr = data.draw(hs.sampled_from((add_ptr, str(add_ptr))))
    jnode.add(add_ptr, add_val)
    assert_json_node(jdoc, doc)


@given(
    doc=json.filter(lambda x: isinstance(x, (list, dict))),
    data=hs.data(),
)
def test_json_remove(doc, data):
    _cache_json(jdoc := JSON(doc))

    # select a JSON node (jnode) on which to call remove
    generate_jsonpointers(nodes := {}, doc)
    node_path = data.draw(hs.sampled_from(list(nodes.keys())))
    jnode = JSONPointer(node_path).evaluate(jdoc)

    # select a target (rmv_ptr) relative to jnode
    generate_jsonpointers(targets := {}, jnode.value)
    rmv_path = data.draw(hs.sampled_from(list(targets.keys())))
    rmv_ptr = data.draw(hs.sampled_from((rmv_path, JSONPointer(rmv_path))))

    # the target relative to root
    target_ptr = JSONPointer(node_path + rmv_path)

    if not target_ptr:
        # replace the whole doc with null
        jnode.remove(rmv_ptr)
        assert_json_node(jdoc, None)
        return

    target_parent = target_ptr[:-1].evaluate(doc)
    target_key = target_ptr[-1]

    if isinstance(target_parent, list):
        if not rmv_ptr:
            # replace target with null
            target_parent[int(target_key)] = None
        else:
            del target_parent[int(target_key)]

    elif isinstance(target_parent, dict):
        if not rmv_ptr:
            # replace target with null
            target_parent[target_key] = None
        else:
            del target_parent[target_key]

    else:
        assert False

    jnode.remove(rmv_ptr)
    assert_json_node(jdoc, doc)


@given(
    doc=json.filter(lambda x: isinstance(x, (list, dict))),
    val=jsonleaf | jsonflatarray | jsonflatobject,
    data=hs.data(),
)
def test_json_replace(doc, val, data):
    _cache_json(jdoc := JSON(doc))
    _cache_json(jdoc_1 := JSON(doc))  # test the equivalent remove + add

    # select a JSON node (jnode) on which to call replace
    generate_jsonpointers(nodes := {}, doc)
    node_path = data.draw(hs.sampled_from(list(nodes.keys())))
    jnode = JSONPointer(node_path).evaluate(jdoc)
    jnode_1 = JSONPointer(node_path).evaluate(jdoc_1)

    # select a target (repl_ptr) relative to jnode
    generate_jsonpointers(targets := {}, jnode.value)
    repl_path = data.draw(hs.sampled_from(list(targets.keys())))
    repl_ptr = data.draw(hs.sampled_from((repl_path, JSONPointer(repl_path))))
    repl_val = data.draw(hs.sampled_from((val, JSON(val))))

    # the target relative to root
    target_ptr = JSONPointer(node_path + repl_path)

    if not target_ptr:
        # replace the whole doc with val
        jnode.replace(repl_ptr, repl_val)
        assert_json_node(jdoc, val)

        jnode_1.remove(repl_ptr)
        jnode_1.add(repl_ptr, repl_val)
        assert jdoc_1 == jdoc

        return

    target_parent = target_ptr[:-1].evaluate(doc)
    target_key = target_ptr[-1]

    if isinstance(target_parent, list):
        target_parent[int(target_key)] = val

    elif isinstance(target_parent, dict):
        target_parent[target_key] = val

    else:
        assert False

    jnode.replace(repl_ptr, repl_val)
    assert_json_node(jdoc, doc)

    jnode_1.remove(repl_ptr)
    jnode_1.add(repl_ptr, repl_val)
    assert jdoc_1 == jdoc


def test_json_literals():
    doc = JSON({
        "foo": null,
        "bar": true,
        "baz": false
    })
    assert_json_node(doc, {
        "foo": None,
        "bar": True,
        "baz": False
    })
