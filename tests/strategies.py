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
    'propname',
    'propnames',
    'jsonproperties',
    'jsonpointer_regex',
    'jsonpointer',
    'jsonpointer_key',
    'interdependent_keywords',
]

jsontype = hs.sampled_from([
    "null",
    "boolean",
    "number",
    "integer",
    "string",
    "array",
    "object",
])
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
jsonarray = hs.lists(json, max_size=10)
jsonobject = hs.dictionaries(jsonstring, json, max_size=10)

propname = hs.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
propnames = hs.lists(propname, unique=True, max_size=10)
jsonproperties = hs.dictionaries(propname, json, max_size=10)

jsonpointer_regex = r'^(/([^~/]|(~[01]))*)*$'
jsonpointer = hs.from_regex(jsonpointer_regex, fullmatch=True)
jsonpointer_key = hs.text() | hs.sampled_from(['~', '/', '-'])

interdependent_keywords = hs.lists(hs.sampled_from([
    "properties",
    "patternProperties",
    "additionalProperties",
    "unevaluatedProperties",
    "items",
    "additionalItems",
    "unevaluatedItems",
    "contains",
    "maxContains",
    "minContains",
    "if",
    "then",
    "else",
    "dependentSchemas",
    "allOf",
    "anyOf",
    "oneOf",
    "not",
]), unique=True)
