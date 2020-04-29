import hypothesis.strategies as hs

__all__ = [
    'jsontype',
    'jsontypes',
    'jsonnull',
    'jsonboolean',
    'jsonnumber',
    'jsoninteger',
    'jsonstring',
    'json',
    'jsonarray',
    'jsonobject',
    'jsonpointer_regex',
    'jsonpointer',
]

jsontype = hs.sampled_from(["null", "boolean", "number", "integer", "string", "array", "object"])
jsontypes = hs.lists(jsontype, unique=True)

jsonnull = hs.none()
jsonboolean = hs.booleans()
jsonnumber = hs.integers() | hs.floats(allow_infinity=False, allow_nan=False)
jsoninteger = hs.integers()
jsonstring = hs.text()

json = hs.recursive(
    base=jsonnull | jsonboolean | jsonnumber | jsonstring,
    extend=lambda children: hs.lists(children) | hs.dictionaries(jsonstring, children),
    max_leaves=10,
)
jsonarray = hs.lists(json)
jsonobject = hs.dictionaries(jsonstring, json)

jsonpointer_regex = r'^(/([^~/]|(~[01]))*)*$'
jsonpointer = hs.from_regex(jsonpointer_regex, fullmatch=True)
