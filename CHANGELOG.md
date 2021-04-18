# Change log

## v0.2.0 (2021-04-18)
### Features
* Class methods for constructing JSON instances from JSON strings/files
### Bug fixes
* Fixed unevaluatedItems-contains interaction
### Miscellaneous
* Top-level package API defined in `__init.py__`
* Improved handling of floats in JSON constructor input
* Removed mod operator from JSON class
* Added development setup (`pip install -e .[dev]`)
* Added JSON class usage info to the README

## v0.1.1 (2021-04-06)
### Bug fixes
* Fixed $dynamicRef resolution (#3)

## v0.1.0 (2021-03-31)
### Features
* JSON class implementing the JSON data model
* JSON Pointer implementation
* JSON Schema implementation, supporting drafts 2019-09 and 2020-12 of the specification
* Catalogue for managing (meta)schemas, vocabularies and format validators
* URI class (wraps rfc3986.URIReference)
