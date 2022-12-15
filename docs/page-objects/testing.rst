.. _web-poet-testing:

======================
Tests for Page Objects
======================

Page Objects that inherit from :class:`~.ItemPage` can be tested by saving the
dependencies needed to create one and the result of
:meth:`~web_poet.pages.ItemPage.to_item`, recreating the Page Object from the
dependencies, running its :meth:`~web_poet.pages.ItemPage.to_item` and
comparing the result to the saved one. ``web-poet`` provides the following
tools for this:

* dependency serialization into a Python object and into a set of files;
* recreating Page Objects from the serialized dependencies;
* a high-level function to save a test fixture;
* a ``pytest`` plugin that discovers fixtures and runs tests for them.

Serialization
=============

:func:`web_poet.serialization.serialize` can be used to serialize an iterable
of Page Object dependencies to a Python object.
:func:`web_poet.serialization.deserialize` can be used to recreate a Page
Object from this serialized data.

An instance of :class:`web_poet.serialization.SerializedDataFileStorage` can be
used to write the serialized data to a set of files in a given directory and to
read it back.

.. note::
    We only support serializing dependencies, not Page Object instances,
    because the only universal way to recreate a Page Object is from its
    dependencies, not from some saved internal state.

Each dependency is serialized to one or several ``bytes`` objects, each of
which is saved as a single file. :func:`web_poet.serialization.serialize_leaf`
and :func:`web_poet.serialization.deserialize_leaf` are used to convert between
a dependency and this set of ``bytes`` objects. They are implemented using
:func:`functools.singledispatch` and while the types provided by ``web-poet``
are supported out of the box, user-defined types need a pair of implementation
functions that need to be registered using
:func:`web_poet.serialization.register_serialization`.

Fixtures
========

The provided ``pytest`` plugin expects fixtures in a certain layout. A set of
fixtures for a single Page Object should be contained in a directory named as
that Page Object fully qualified class name. Each fixture is a directory inside
it. Each fixture directory contains a subdirectory named "inputs" that contains
the serialized dependencies and a file named "output.json" that contains the
item which is the result of the Page Object's
:meth:`~web_poet.pages.ItemPage.to_item` method.

:func:`web_poet.testing.save_fixture` can be used to create a fixture inside a
Page Object directory from an iterable of dependencies and an output item. It
can optionally take a name for the fixture directory. By default it uses
incrementing names "test-1", "test-2" etc.

Running tests
=============

The provided ``pytest`` plugin is automatically registered when ``web-poet`` is
installed, and running ``pytest`` in a directory containing fixtures will
discover them and run tests for them.
