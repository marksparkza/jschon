import hypothesis.strategies as hs

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
jsonnumber = hs.integers() | \
             hs.floats(allow_nan=False, allow_infinity=False) | \
             hs.decimals(allow_nan=False, allow_infinity=False)
jsonnumber_nodecimal = hs.integers() | \
                       hs.floats(allow_nan=False, allow_infinity=False)
jsoninteger = hs.integers()
jsonstring = hs.text()
jsonleaf = jsonnull | jsonboolean | jsonnumber | jsonstring
jsonleaf_nodecimal = jsonnull | jsonboolean | jsonnumber_nodecimal | jsonstring

json = hs.recursive(
    base=jsonleaf,
    extend=lambda children: hs.lists(children) | hs.dictionaries(jsonstring, children),
    max_leaves=10,
)
json_nodecimal = hs.recursive(
    base=jsonleaf_nodecimal,
    extend=lambda children: hs.lists(children) | hs.dictionaries(jsonstring, children),
    max_leaves=10,
)
jsonarray = hs.lists(json, max_size=10)
jsonflatarray = hs.lists(jsonleaf, max_size=20)
jsonobject = hs.dictionaries(jsonstring, json, max_size=10)
jsonflatobject = hs.dictionaries(jsonstring, jsonleaf, max_size=20)

propname = hs.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
propnames = hs.lists(propname, unique=True, max_size=10)
jsonproperties = hs.dictionaries(propname, jsonleaf, max_size=10)

jsonpointer_regex = r'^(/([^~/]|(~[01]))*)*$'
jsonpointer = hs.from_regex(jsonpointer_regex, fullmatch=True)
jsonpointer_key = hs.text() | hs.sampled_from(['~', '/', '-'])

interdependent_keywords = hs.lists(hs.sampled_from([
    "properties",
    "patternProperties",
    "additionalProperties",
    "unevaluatedProperties",
    "prefixItems",
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
    "contentMediaType",
    "contentSchema",
]), unique=True)
