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

.. _dep-serialization:

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
it, that contains data for Page Object inputs and output::

    fixtures
    └── my_project.po.MyItemPage
        ├── test-1
        │   ├── inputs
        │   │   ├── HttpResponse-body.html
        │   │   ├── HttpResponse-other.json
        │   │   └── ResponseUrl.txt
        │   ├── meta.json
        │   └── output.json
        └─── test-2
            ├── inputs
            │   ├── HttpResponse-body.html
            │   ├── HttpResponse-other.json
            │   └── ResponseUrl.txt
            ├── meta.json
            └── output.json

:func:`web_poet.testing.Fixture.save` can be used to create a fixture inside a
Page Object directory from an iterable of dependencies, an output item and an
optional metadata dictionary. It can optionally take a name for the fixture
directory. By default it uses incrementing names "test-1", "test-2" etc.

.. note::
    ``output.json`` contains a result of
    ``ItemAdapter(page_object.to_item()).asdict()`` saved as JSON.

After generating a fixture you can edit ``output.json`` to modify expected
field values and add new fields, which is useful when creating tests for code
that isn't written yet or before modifying its behavior.

.. _web-poet-testing-scrapy-poet:

scrapy-poet integration
=======================

Projects that use the `scrapy-poet`_ library can use the :ref:`Scrapy command
<scrapy-poet:testing>` provided by it to generate fixtures in a convenient way.
It's available starting with scrapy-poet 0.8.0.

.. _scrapy-poet: https://github.com/scrapinghub/scrapy-poet

Running tests
=============

The provided ``pytest`` plugin is automatically registered when ``web-poet`` is
installed, and running ``python -m pytest`` in a directory containing fixtures
will discover them and run tests for them.

.. _web-poet-testing-frozen_time:

Handling time fields
====================

Sometimes output of a page object might depend on the current time. For
example, the item may contain the scraping datetime, or a current timestamp may
be used to build some URLs. When a test runs at a different time it will break.
To avoid this the metadata dictionary can contain a ``frozen_time`` field set
to the time value used when generating the test. This will instruct the test
runner to use the same time value so that field comparisons are still correct.

The value can be any string understood by `dateutil`_. If it doesn't include
timezone information, the local time of the machine will be assumed. If it
includes timezone information, on non-Windows systems the test process will be
executed in that timezone, so that output fields that contain local time are
correct. On Windows systems (where changing the process timezone is not
possible) the time value will be converted to the local time of the machine,
and such fields will containt wrong data if these timezones don't match.
Consider an example item::

    import datetime
    from web_poet import WebPage

    class DateItemPage(WebPage):
        async def to_item(self) -> dict:
            # e.g. 2001-01-01 11:00:00 +00
            now = datetime.datetime.now(datetime.timezone.utc)
            return {
                # '2001-01-01T11:00:00Z'
                "time_utc": now.strftime("%Y-%M-%dT%H:%M:%SZ"),
                # if the current timezone is CET, then '2001-01-01T12:00:00+01:00'
                "time_local": now.astimezone().strftime("%Y-%M-%dT%H:%M:%S%z"),
            }

We will assume that the fixture was generated in CET (UTC+1).

* If the fixture doesn't have the ``frozen_time`` metadata field, the item will
  simply contain the current time and the test will always fail.
* If ``frozen_time`` doesn't contain the timezone data (e.g. it is
  ``2001-01-01T11:00:00``), the item will depend on the machine timezone: in
  CET it will contain the expected values, in timezones with a different offset
  ``time_local`` will be different.
* If ``frozen_time`` contains the timezone data and the system is not Windows,
  the ``time_local`` field will contain the date in that timezone, so if the
  timezone in ``frozen_time`` is not UTC+1, the test will fail.
* If the system is Windows, the ``frozen_time`` value will be converted to the
  machine timezone, so the item will depend on that timezone, just like when
  ``frozen_time`` doesn't contain the timezone data, and ``time_local`` will
  similarly be only correct if the machine timezone has the same offset as CET.

This means that most combinations of setups will work if ``frozen_time``
contains the timezone data, except for running tests on Windows, in which case
the machine timezone should match the timezone in ``frozen_time``. Also, if
items do not depend on the machine timezone (e.g. if all datetime-derived data
they contain is in UTC), the tests for them should work everywhere.

.. _dateutil: https://github.com/dateutil/dateutil

.. _git-lfs:

Storing fixtures in Git
=======================

Fixtures can take a lot of disk space, as they usually include page responses
and may include other large files, so we recommend using `Git LFS`_ when
storing them in Git repos to reduce the repo space and get other performance
benefits. Even if your fixtures are currently small, it may be useful to do
this from the beginning, as migrating files to LFS is not easy and requires
rewriting the repo history.

To use Git LFS you need a Git hosting provider that supports it, and major
providers and software (e.g. GitHub, Bitbucket, GitLab) support it. There are
also `implementations`_ for standalone Git servers.

Assuming you store the fixtures in the directory named "fixtures" in the repo
root, the workflow should be as following. Enable normal diffs for LFS files in
this repo::

  git config diff.lfs.textconv cat

Enable LFS for the fixtures directory before committing anything in it::

  git lfs track "fixtures/**"

Commit the ``.gitattributes`` file (which stores the tracking information)::

  git add .gitattributes
  git commit

After generating the fixtures just commit them as usual::

  git add fixtures/test-1
  git commit

After this all usual commands including ``push``, ``pull`` or ``checkout``
should work as expected on these files.

Please also check the official Git LFS documentation for more information.

.. _Git LFS: https://git-lfs.com/
.. _implementations: https://github.com/git-lfs/git-lfs/wiki/Implementations
