.. _ai:

===========================
AI-assisted code generation
===========================

When using LLMs to write Python code for web scraping, these are the most
reasonable approaches to consider:

:doc:`Scrapy spiders <scrapy:index>`
    **Pros:** Built-in crawling, request request scheduling, retries and many
    utilities.

    **Cons:** Large surface area for AI generation. Spiders mix crawling, error
    handling and extraction, which makes testing extraction in isolation
    difficult.

    **Avoid** generating full spiders with an LLM; prefer generating extraction
    logic separately.

Plain Python functions or classes
    **Pros:** Simple, dependency-free, and easy for LLMs to produce.

    **Cons:** You must define your own conventions and testing practices;
    integration across teams and tools can be ad-hoc.

    **Use when** you need a quick extractor or the logic is small and unlikely
    to be reused.

:ref:`web-poet page objects <overview>`
    **Pros:** Small, standard contract for extraction with field-level
    decomposition, first-class testing support, and framework integration.

    **Cons:** Requires adopting web-poet idioms and a small framework cost,
    which can be unnecessary for trivial scripts.

    **Use when** you want maintainability, testability, and a predictable
    contract that can be used by tools and teams.

    .. note:: :doc:`scrapy-poet <scrapy-poet:index>` provides a great way to
        use web-poet page objects within Scrapy spiders, giving you the
        benefits of both approaches.
