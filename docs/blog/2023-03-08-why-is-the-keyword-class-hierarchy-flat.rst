Why is the keyword class hierarchy flat?
========================================
*Wed 08 Mar 2023*

In developing jschon, I’ve drawn a lot of inspiration from two great Python
libraries that I use extensively in my day job: Pydantic and SQLAlchemy.

Applications that use Pydantic or the ORM paradigm in SQLAlchemy are easy to
spot: you’ll find a collection of declarative models, each derived from a
quintessential base class provided by the library - :class:`BaseModel` in Pydantic,
:class:`DeclarativeBase` in SQLAlchemy. A given application might define a model
hierarchy to roll up common behaviours, but that would be private to the
application and, in general, should not affect the relationships between the
declarative models and other foundational entities in the library. One of the
great things about implementing declarative models using these libraries is
that I know that I can just derive from :class:`BaseModel` or :class:`DeclarativeBase`,
I don't have to know which is the most appropriate abstract subclass to use,
and I don't need to be aware of any variance in implementation higher up in the 
hierarchy. Another great thing is that each model is completely self-contained 
and completely self-descriptive.

In jschon, keywords are analogous to declarative models, with :class:`Keyword`
being the quintessential base class. One might argue that declarative
models are conceptually more analogous to schemas, and model fields to
keywords, but I'm looking at things from a programming workflow perspective: as
declarative models are the building blocks of a Pydantic / SQLAlchemy 
application, so keywords are the building blocks of a vocabulary
implementation. Taking the analogy further, a given vocabulary might define a
keyword class hierarchy to roll up common behaviours, but that should be 
private to the module, extension or application that implements the vocabulary, 
and should not affect the underlying relationships between keywords and other 
foundational entities in the jschon library. From the perspective of those 
other entities, a keyword is a keyword is a keyword, and from the perspective 
of the vocabulary, a keyword is self-contained and self-descriptive.

*marksparkza*