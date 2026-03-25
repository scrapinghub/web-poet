cmake_minimum_required(VERSION 3.15)
project(SphinxDocs VERSION 1.0.0 LANGUAGES NONE)

include(FetchContent)
FetchContent_Declare(
  sphinx_cmake_modules
  GIT_REPOSITORY https://github.com/jdillard/sphinx-cmake-modules.git
  GIT_TAG        main
)
FetchContent_MakeAvailable(sphinx_cmake_modules)
list(APPEND CMAKE_MODULE_PATH "${sphinx_cmake_modules_SOURCE_DIR}/cmake/modules")

add_subdirectory(docs)
