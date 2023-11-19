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
jsonnumber = hs.integers() | hs.floats(allow_nan=False, allow_infinity=False)
jsonnumber_withdecimal = jsonnumber | hs.decimals(allow_nan=False, allow_infinity=False)
jsoninteger = hs.integers()
jsonstring = hs.text()
jsonleaf = jsonnull | jsonboolean | jsonnumber | jsonstring
jsonleaf_withdecimal = jsonnull | jsonboolean | jsonnumber_withdecimal | jsonstring

json = hs.recursive(
    base=jsonleaf,
    extend=lambda children: hs.lists(children) | hs.dictionaries(jsonstring, children),
    max_leaves=10,
)
json_withdecimal = hs.recursive(
    base=jsonleaf_withdecimal,
    extend=lambda children: hs.lists(children) | hs.dictionaries(jsonstring, children),
    max_leaves=10,
)
jsonarray = hs.lists(json, max_size=5)
jsonflatarray = hs.lists(jsonleaf, max_size=20)
jsonobject = hs.dictionaries(jsonstring, json, max_size=5)
jsonflatobject = hs.dictionaries(jsonstring, jsonleaf, max_size=20)

propname = hs.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
propnames = hs.lists(propname, unique=True, max_size=10)
jsonproperties = hs.dictionaries(propname, jsonleaf, max_size=10)

jsonpointer_regex = '(/([^~/]|(~[01]))*)*'
jsonpointer_index = '0|([1-9][0-9]*)'
jsonpointer_index_manip = r'((\+|-)[1-9][0-9]*)?'
jsonpointer = hs.from_regex(jsonpointer_regex, fullmatch=True)
jsonpointer_key = hs.text() | hs.sampled_from(['~', '/', '-']) | hs.from_regex(jsonpointer_index, fullmatch=True)
relative_jsonpointer_regex = (
    f'(?P<up>{jsonpointer_index})'
    f'(?P<over>{jsonpointer_index_manip})'
    f'(?P<ref>#|{jsonpointer_regex})'
)
relative_jsonpointer = hs.from_regex(relative_jsonpointer_regex, fullmatch=True)

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
    "$ref",
    "$recursiveRef",
    "$dynamicRef",
]), unique=True)
