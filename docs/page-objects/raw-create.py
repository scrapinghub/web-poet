foo_page = FooPage(
    response=HttpResponse(
        "https://example.com",
        b"<!DOCTYPE html>\n<title>Foo</title>",
    ),
)
