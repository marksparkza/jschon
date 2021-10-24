Extending JSON Schema
=====================
Consider the following scenario:

You're working on data validation for a project that uses enumerations
consisting of thousands of codes, obtained and cached from remote terminology
services. Your validation schema -- and any error output it produces -- cannot
list all the possible values for an enumeration, but should rather reference
an enumeration by its id.

In the following example, we solve this problem by defining a custom keyword --
``"enumRef"`` -- that can retrieve an enumeration given its URI and decide
whether a given string instance is valid.

First, we create a vocabulary that describes the syntax of our new keyword.
This is a JSON meta-schema that we'll save to ``data/enumRef-vocabulary.json``:

.. literalinclude:: ../../examples/data/enumRef-vocabulary.json

Next, we create an extension to the JSON Schema 2020-12 meta-schema that
includes our new vocabulary. We'll save this to ``data/enumRef-metaschema.json``:

.. literalinclude:: ../../examples/data/enumRef-metaschema.json

Finally, we implement the ``"enumRef"`` keyword by defining an
:class:`EnumRefKeyword` class. The following script includes an example
implementation using a simple local cache, a few lines of boilerplate code
to compile the meta-schema and vocabulary definition files, and an example
schema that we use to evaluate both valid and invalid sample JSON instances:

.. literalinclude:: ../../examples/custom_keyword.py

The script produces the following output:

.. literalinclude:: ../../examples/output/custom_keyword.txt
