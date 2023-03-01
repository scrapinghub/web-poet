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
    └── my_project.pages.MyItemPage
        ├── test-1
        │   ├── inputs
            │   ├── HttpClient.exists
        │   │   ├── HttpResponse-body.html
        │   │   ├── HttpResponse-info.json
        │   │   └── ResponseUrl.txt
        │   ├── meta.json
        │   └── output.json
        └─── test-2
            ├── inputs
            │   ├── HttpClient.exists
            │   ├── HttpClient-0-HttpRequest.info.json
            │   ├── HttpClient-0-HttpResponse.body.html
            │   ├── HttpClient-0-HttpResponse.info.json
            │   ├── HttpClient-1-HttpRequest.body.txt
            │   ├── HttpClient-1-HttpRequest.info.json
            │   ├── HttpClient-1-HttpResponse.body.html
            │   ├── HttpClient-1-HttpResponse.info.json
            │   ├── HttpResponse-body.html
            │   ├── HttpResponse-info.json
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

.. _web-poet-testing-pytest:

Running tests
=============

The provided ``pytest`` plugin is automatically registered when ``web-poet`` is
installed, and running ``python -m pytest`` in a directory containing fixtures
will discover them and run tests for them.

By default, the plugin generates:

* a test which checks that ``to_item()`` doesn't raise an exception
  (i.e. it can be executed),
* a test per each output attribute of the item,
* an additional test to check that there are no extra attributes in the output.

For example, if your item has 5 attributes, and you created 2 fixtures, pytest
will run (5+1+1)*2 = 14 tests. This allows to report failures for individual
fields separately.

If ``to_item`` raises an error, there is no point in running other tests,
so they're skipped in this case.

If you prefer less granular test failure reporting, you can use pytest with
the ``--web-poet-test-per-item`` option::

    python -m pytest --web-poet-test-per-item

In this case there is going to be a single test per fixture: if the result
is not fully correct, the test fails. So, following the previous example,
it'd be 2 tests instead of 14.

.. _web-poet-testing-tdd:

Test-Driven Development
=======================

You can follow TDD (Test-Driven Development) approach to develop your
page objects. To do so,

1. Generate a fixture (see :ref:`web-poet-testing-scrapy-poet`).
2. Populate ``output.json`` with the correct expected output.
3. Run the tests (see :ref:`web-poet-testing-pytest`) and update the code
   until all tests pass. It's convenient to use web-poet :ref:`fields`,
   and implement extraction field-by-field, because you'll be getting
   an additional test passing after each field is implemented.

This approach allows a fast feedback loop: there is no need to download page
multiple times, and you have a clear progress indication for your work
(number of failing tests remaining). Also, in the end you get
a regression test, which can be helpful later.

Sometimes it may be awkward to set the correct value in JSON before starting
the development, especially if a value is large or has a complex structure.
For example, this could be the case for e-commerce product description field,
which can be hard to copy-paste from the website, and which may have various
whitespace normalization rules which you need to apply.

In this case, it may be more convenient to implement the extraction first,
and only then populate the ``output.json`` file with the correct value.

You can use ``python -m web-poet.testing rerun <fixture_path>`` command
in this case, to re-run the page object using the inputs saved in a fixture.
This command prints output of the page object, as JSON; you can then copy-paste
relevant parts to the ``output.json`` file. It's also possible to make
the command print only some of the fields. For example, you might run the
following command after implementing extraction for "description" and
"descriptionHtml" fields in ``my_project.pages.MyItemPage``::

    python -m web-poet.testing rerun \
        fixtures/my_project.pages.MyItemPage/test-1 \
        --fields description,descriptionHtml

It may output something like this::

    {
        "description": "..description of the product..",
        "descriptionHtml": "<p>...</p>"
    }

If these values look good, you can update
``fixtures/my_project.pages.MyItemPage/test-1/output.json`` file
with these values.

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

There is an additional limitation which we plan to fix in future versions. The
time is set to the ``frozen_time`` value when the test generation (if using the
``scrapy-poet`` command) or the test run starts, but it ticks during the
generation/run itself, so if it takes more than 1 second (which is quite
possible even in simple cases) the time fields will have values several seconds
later than ``frozen_time``. For now we recommend to work around this problem by
manually editing the ``output.json`` file to put the value equal to
``frozen_time`` in these fields, as running the test shoudn't take more than 1
second.

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

.. _web-poet-testing-additional-requests:

Additional requests support
===========================

If the page object uses the :class:`~.HttpClient` dependency to make
:ref:`additional requests <additional-requests>`, the generated fixtures will
contain these requests and their responses. When the test runs,
:class:`~.HttpClient` will return the saved responses without doing actual
requests.

Currently requests are compared by their URL, method, headers and body, so if a
page object makes requests that differ between runs, the test won't be able to
find a saved response and will fail.

Test coverage
=============

The coverage for page object code is reported correctly if tools such as
`coverage`_ are used when running web-poet tests.

.. _coverage: https://coverage.readthedocs.io/
