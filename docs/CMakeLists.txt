include(SphinxUtils)

setup_sphinx_environment()

set(SPHINX_SOURCE ${CMAKE_CURRENT_SOURCE_DIR})

add_sphinx_builder(html)
add_sphinx_builder(markdown)
add_sphinx_builder(singlemarkdown)
