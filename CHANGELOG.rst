Changelog
=========

v0.10.1 (2023-04-11)
--------------------
Miscellaneous:

* Rename submodules `json-schema-spec-2019-09` and `json-schema-spec-2020-12` to
  `json-schema-2019-09` and `json-schema-2020-12`, respectively
  (run ``git submodule init`` to update local git config)
* LocalSource now includes the filename in the CatalogError when the file is not found


v0.10.0 (2023-04-01)
--------------------
Features:

* ``@format_validator`` decorator
* `json-pointer` format validator
* Annotation filtering for `basic` output format (#32)
* JSON ``null``, ``true``, ``false`` literals
* Relative JSON Pointer ``+``/``-`` array index adjustments
* Unknown keywords are collected as annotations
* Automatically create metaschemas as referenced by ``"$schema"``
  on first access of the now-cached ``JSONSchema.metaschema`` property
* Automatically detect the core vocabulary in metaschemas,
  but allow specifying a default to use when none is detectable

Experimental:

* Catalog support for the `next` JSON Schema draft
* `hierarchical` output format
* In-place JSON Patch `add`, `remove` and `replace` operations on ``JSON`` class

Breaking changes:

* ``Catalog.add_format_validators()`` superseded by ``@format_validator`` / ``Catalog.enable_formats()``
* Rename ``Catalog.session()`` context manager to ``Catalog.cache()``
* Rename ``session`` parameter to ``cacheid`` in many places
* Rename public functions in the ``jsonpatch`` module
* Rename ``*Applicator*`` keyword class mixins to ``*Subschema*``

Bug Fixes:

* "$dynamicRef" works with non-plain-name fragment URIs
* Fixed remote anchor ref resolution

Documentation:

* Rename `User Guide` to `Tutorial`
* Restructure the API docs index page
* Blog!

Miscellaneous:

* ``@output_formatter`` decorator now identifies output formats explicitly
* Add ``JSONCompatible`` and ``Result`` classes to the top-level package API
* Remove implicit fall-through to looking up a schema in the `__meta__` cache
  if not found in the parameterized cache, in ``Catalog.get_schema()`` (#40)
* Added ``Catalog.get_metaschema()``, analogous to ``Catalog.get_schema()``
* ``Catalog.create_metaschema()`` and ``Catalog.create_vocabulary()`` return the created instance
* Rename ``core_vocabulary`` and ``core_vocabulary_uri`` parameters for
  ``Metaschema.__init__()`` and ``Catalog.create_metaschema()`` respectively to
  ``default_core_vocabulary`` and ``default_core_vocabulary_uri``
* Improve kwarg-based construction of ``RelativeJSONPointer``
* Rename ``AnnotationKeyword`` to ``_AnnotationKeyword``
* Rename ``vocabularies`` parameter of ``create_catalog()`` to ``versions``
* Allow passthrough of arguments to pytest when invoking tox
* Add pytest command line options ``--testsuite-file`` and ``--testsuite-description``
* Python 3.11 is now tested (no changes were required to support it)
* Pinned ``hypothesis<6.0.4`` to avoid
  `python/cpython#102126 <https://github.com/python/cpython/issues/102126>`_
  in Python 3.10.10 and 3.11.2


v0.9.0 (2022-08-14)
-------------------
Features:

* JSON array/object mutation
* JSON serialization to string/file
* JSON deserialization from remote location

Breaking changes:

* Rename Scope to Result
* Remove JSON support for decimal.Decimal (#31)
* Rename Keyword.types to Keyword.instance_types
* Rename Keyword.depends to Keyword.depends_on
* Move translation vocabulary implementation to its own repo (jschon-translation)

Miscellaneous:

* Allow any JSON-compatible value to be set as an error on a Result node
* Array/object applicator keywords -- additionalProperties, unevaluatedProperties,
  propertyNames, additionalItems, items, prefixItems, unevaluatedItems -- now
  produce an error array of failing child indices
* Register output formatters with a decorator
* Remove JSON type checks for unsupported usage
* Append (rather than replace) the suffix when resolving a LocalSource filepath
* Flatten dict of subresults on Result node
* Provide a useful __str__ method for Result node


v0.8.5 (2022-05-10)
-------------------
Features:

* Added JSONPointer prefix test operators (#29)


v0.8.4 (2022-02-03)
-------------------

Miscellaneous:

* Add PEP-561 py.typed marker to signal to type checkers that
  this library has usable type annotations.


v0.8.3 (2022-01-31)
-------------------

Miscellaneous:

* Include translation vocabulary definition files in the distribution.


v0.8.1 (2022-01-30)
-------------------

Miscellaneous:

* The requests dependency for remote $refs is now an optional install.


v0.8.0 (2022-01-29)
-------------------
Features:

* Added support for remote schema references and, more generally, 'sources' for loading
  URI-identified JSON resources
* Added a JSON Patch implementation
* Added a Relative JSON Pointer implementation
* Added experimental support for a JSON translation vocabulary

Breaking changes:

* Replaced the Catalog.add_directory method with the more general Catalog.add_uri_source

Bug fixes:

* Fixed error messaging for the "required" keyword
* Eliminated extraneous error messages from "additionalProperties" and "items" by reverting
  to the Draft 7 approach for applying these keywords (#17)

Miscellaneous:

* Implemented a Catalog instance registry, replacing the default instance approach
* Moved JSON Schema vocabulary initialization from the Catalog class to the create_catalog function
* Replaced the AnyJSONCompatible type variable with a JSONCompatible type alias
* Removed isinstance type checks that would only fail if type hints were disregarded
* Removed printing of JSON instance values for "enum" and "const" error messages
* Decorated several JSON and JSONSchema properties with @cached_property
* Constrained the Keyword.types and Keyword.depends class attributes to allow tuples only
* Removed unused code supporting instantiation of JSON arrays/objects from collections of JSON
  class instances
* Changed type hints for JSON inequality operators to indicate that they are supported only
  for strings and numbers
* Removed unnecessary type coercion in JSON inequality operators
* Generalized Keyword class mixins to support custom subschema construction by custom
  applicator keywords
* Added a required positional arg `instance` to the Scope constructor
* Removed the `path`, `instpath` and `relpath` Scope constructor args
* Added a `cls` keyword arg to Scope.__call__ supporting custom Scope classes
* Generalized output formatting, to support custom output formats by extensions
* Added a globals property to the root of the Scope tree, for arbitrary evaluation state
* Added a Keyword.static class attribute, obviating the need to override can_evaluate


v0.7.3 (2021-10-24)
-------------------
Documentation:

* Added example of extending JSON Schema with a custom keyword, vocab and meta-schema
* Various improvements to wording and structuring of docs

Miscellaneous:

* The `default` param of create_catalog() now defaults to True
* Allow "$id" and "$schema" to be omitted from meta-schema documents
* Renamed JSON.value to JSON.data; JSON.value now returns the instance data as a
  JSON-compatible Python object (#18)
* Switched to reStructuredText across the board - top-level ``*.rst`` files are now
  included in the docs and in the published package


v0.7.2 (2021-08-28)
-------------------
Bug fixes:

* Fixed "absoluteKeywordLocation" output for "$ref", "$dynamicRef" and "$recursiveRef" nodes (#15)

Documentation:

* Restructured examples; example outputs are now verified by unit tests
* Added examples of loading schemas from files


v0.7.1 (2021-08-08)
-------------------
Breaking changes:

* Renamed Catalogue to Catalog


v0.7.0 (2021-08-08)
-------------------
Features:

* Top-level catalogue initialization function
* Session id-based schema caching

Breaking changes:

* Removed the Catalogue.create_default_catalogue method

Documentation:

* Added sections on getting started and running the tests
* Improved JSONSchema and Catalogue usage docs


v0.6.0 (2021-06-10)
-------------------
Features:

* Detailed and verbose output format options

Breaking changes:

* JSONSchema.validate() now returns a Scope result object

Bug fixes:

* Fixed the instance location (shown in output) for object keys evaluated by "propertyNames"

Miscellaneous:

* Failing schema nodes no longer have error messages, and are excluded from basic output
* A Scope.passed property indicates a scope's assertion result, while Scope.valid indicates its
  validation result (these can only differ for an "if" keyword subscope)
* Improved the API (used by keywords) and internal structure of the Scope class
* Dropped the Annotation and Error classes


v0.5.0 (2021-06-01)
-------------------
Features:

* An output method on Scope, providing output formatting

Breaking changes:

* Dropped the Evaluator class

Miscellaneous:

* Moved Metaschema, Vocabulary and Keyword into the vocabulary subpackage


v0.4.0 (2021-05-21)
-------------------
Bug fixes:

* Fixed error and annotation collection for array items (#8)

Miscellaneous:

* Improved and better encapsulated the Scope class's internal logic
* Added ``doc`` dependencies to setup.py
* Support testing with Python 3.10


v0.3.0 (2021-05-15)
-------------------
Features:

* Evaluator class providing output formatting
* Multiple Catalogue instances now supported; with an optional default catalogue

Bug fixes:

* Fixed percent-encoding of the URI fragment form of JSON pointers

Documentation:

* Created user guides and API reference documentation; published to Read the Docs

Miscellaneous:

* Improvements to base URI-directory mapping and file loading in the Catalogue
* Tweaks to annotation and error collection in the Scope class affecting output generation
* Auto-generated schema URIs are now formatted as ``'urn:uuid:<uuid>'``


v0.2.0 (2021-04-18)
-------------------
Features:

* Class methods for constructing JSON instances from JSON strings/files

Bug fixes:

* Fixed unevaluatedItems-contains interaction

Miscellaneous:

* Top-level package API defined in ``__init.py__``
* Improved handling of floats in JSON constructor input
* Removed mod operator from JSON class
* Added development setup (``pip install -e .[dev]``)
* Added JSON class usage info to the README


v0.1.1 (2021-04-06)
-------------------
Bug fixes:

* Fixed $dynamicRef resolution (#3)


v0.1.0 (2021-03-31)
-------------------
Features:

* JSON class implementing the JSON data model
* JSON Pointer implementation
* JSON Schema implementation, supporting drafts 2019-09 and 2020-12 of the specification
* Catalogue for managing (meta)schemas, vocabularies and format validators
* URI class (wraps rfc3986.URIReference)
