Maintaining
===========

How to release a new version
----------------------------

Make sure to install bump2version_, a maintained fork of bumpversion_:

.. code-block:: shell

    pip install --upgrade bump2version

Then follow this checklist:

* Update changelog in a separate commit
* Execute the ``bumpversion`` command
* Push latest changes including tags

The changelog is kept under the ``CHANGES.rst`` file.
It should be updated in a separate commit to master.

After changelog is merged to master, you can check which changes are needed
to update the version executing:

.. code-block:: shell

    bumpversion minor --dry-run --verbose

When you're ready, you can remove the flags and execute:

.. code-block:: shell

    bumpversion minor

In this example, we're bumping our minor version, but you may use any of the
following:

* patch (for bug fixes)
* minor (new features that keep compatibility)
* major (introduces breaking changes)

Finally, you can push the changes to the remote repository.
Make sure to include git tags.

.. code-block:: shell

    git push origin `git describe --tags`

The PyPI release will be handled by Travis CI.

.. _bump2version: https://github.com/c4urself/bump2version
.. _bumpversion: https://github.com/peritus/bumpversion
