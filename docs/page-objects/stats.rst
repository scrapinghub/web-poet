.. _stats:

=====
Stats
=====

During parsing, storing some data about the parsing itself can be useful for
debugging, monitoring, and reporting. The :class:`~.Stats` page input allows
storing such data.

For example, you can use stats to track which parsing code is actually used, so
that you can remove code once it is no longer necessary due to upstream
changes:

.. code-block:: python

    from attrs import define
    from web_poet import field, Stats, WebPage


    @attrs.define
    class MyPage(WebPage):
        stats: Stats

        @field
        def title(self):
            if title := self.css("h1::text").get():
                self.stats.inc("MyPage/field-src/title/h1")
            elif title := self.css("h2::text").get():
                self.stats.inc("MyPage/field-src/title/h2")
            return title
