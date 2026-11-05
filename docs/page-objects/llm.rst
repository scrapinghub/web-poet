.. _llm:

========================
Parsing text with an LLM
========================

Some data only exists as prose. A shipping policy reads "Ships in 3 to 5
business days, free on orders over $50", and no selector gets the number of
days or the free shipping threshold out of it.

You can extract that prose as is and make sense of it later, in
post-processing, or you can parse it into structured data as part of the
page object, with :class:`~web_poet.llm.LLMClient`, so that its output is
final. You can also do both, and keep the raw text next to the parsed data:

.. code-block:: python

    import attrs
    from web_poet import WebPage, field
    from web_poet.llm import LLMClient


    @attrs.define
    class Shipping:
        days: int | None
        """Upper bound of business days until delivery."""

        free_over: float | None
        """Order total from which shipping is free."""


    @attrs.define
    class ProductPage(WebPage):
        llm: LLMClient

        @field
        async def shipping(self) -> Shipping:
            text = " ".join(self.css(".shipping *::text").getall())
            return await self.llm.parse(text, Shipping)

The field types and docstrings of the item class become the schema that the
model fills in, so write them for the model. Pass only the relevant text, as
the whole page costs far more tokens and parses worse.

:class:`~web_poet.llm.LLMClient` is an :ref:`input <inputs>` that your
framework provides, like any other :ref:`custom input <custom-inputs>`. To
build one, install the ``llm`` extra:

.. code-block:: bash

    pip install web-poet[llm]

Then wrap an asynchronous instructor_ client:

.. _instructor: https://python.useinstructor.com/

.. code-block:: python

    import instructor
    from instructor.cache import DiskCache
    from web_poet.llm import LLMClient

    llm = LLMClient(
        instructor.from_provider("anthropic/claude-opus-5", async_client=True),
        cache=DiskCache(".llm-cache"),
    )

With a cache, parsing the same text into the same item class again is free,
so a site that shows the same shipping policy on every product page costs a
single request. Without one, the client still merges concurrent calls with
the same text into a single request.
