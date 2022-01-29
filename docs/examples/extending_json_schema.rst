Extending JSON Schema
=====================
In this example, we define a custom keyword -- ``"enumRef"`` -- that provides
us with the capability to validate JSON string instances against enumerations
(which may consist of many thousands of terms) that we have obtained and cached
from remote terminology services.

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
