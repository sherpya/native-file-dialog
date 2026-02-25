# Qt6-based file dialog extension (Linux only). No KF6.
cmake_minimum_required(VERSION 3.16)
project(native_qt LANGUAGES CXX)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
  find_package(pybind11 REQUIRED)
endif()

pybind11_add_module(_native_qt MODULE ${CMAKE_CURRENT_SOURCE_DIR}/src/native_qt.cpp)
target_link_libraries(_native_qt PRIVATE Qt6::Core Qt6::Gui Qt6::Widgets)

set_target_properties(_native_qt PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY "${NFD_PACKAGE_DIR}"
  RUNTIME_OUTPUT_DIRECTORY "${NFD_PACKAGE_DIR}"
  PREFIX ""
  OUTPUT_NAME "_native_qt"
)
install(TARGETS _native_qt LIBRARY DESTINATION .)
