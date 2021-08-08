# Change log

## v0.7.0 (2021-08-08)
### Features
* Top-level catalogue initialization function
* Session id-based schema caching
### Breaking changes
* Removed the Catalogue.create_default_catalogue method
### Documentation
* Added sections on getting started and running the tests
* Improved JSONSchema and Catalogue usage docs

## v0.6.0 (2021-06-10)
### Features
* Detailed and verbose output format options
### Breaking changes
* JSONSchema.validate() now returns a Scope result object
### Bug fixes
* Fixed the instance location (shown in output) for object keys evaluated by "propertyNames"
### Miscellaneous
* Failing schema nodes no longer have error messages, and are excluded from basic output
* A Scope.passed property indicates a scope's assertion result, while Scope.valid indicates its
  validation result (these can only differ for an "if" keyword subscope)
* Improved the API (used by keywords) and internal structure of the Scope class
* Dropped the Annotation and Error classes

## v0.5.0 (2021-06-01)
### Features
* An output method on Scope, providing output formatting
### Breaking changes
* Dropped the Evaluator class
### Miscellaneous
* Moved Metaschema, Vocabulary and Keyword into the vocabulary subpackage

## v0.4.0 (2021-05-21)
### Bug fixes
* Fixed error and annotation collection for array items (#8)
### Miscellaneous
* Improved and better encapsulated the Scope class's internal logic
* Added `doc` dependencies to setup.py
* Support testing with Python 3.10

## v0.3.0 (2021-05-15)
### Features
* Evaluator class providing output formatting
* Multiple Catalogue instances now supported; with an optional default catalogue
### Bug fixes
* Fixed percent-encoding of the URI fragment form of JSON pointers
### Documentation
* Created user guides and API reference documentation; published to Read the Docs
### Miscellaneous
* Improvements to base URI-directory mapping and file loading in the Catalogue
* Tweaks to annotation and error collection in the Scope class affecting output generation
* Auto-generated schema URIs are now formatted as `'urn:uuid:<uuid>'`

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
