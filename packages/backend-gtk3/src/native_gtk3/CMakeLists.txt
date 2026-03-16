# GTK3 file dialog extension (Linux only).
# Shared C source with backend-gtk; built without NFD_USE_GTK4.
cmake_minimum_required(VERSION 3.16)
project(native_gtk3 LANGUAGES C)

set(CMAKE_C_STANDARD 11)

# Path to the shared C source in the sibling backend-gtk package.
set(NFD_SHARED_SRC "${CMAKE_CURRENT_SOURCE_DIR}/../../../backend-gtk/src/native_gtk/src/native_gtk.c")

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTK3 REQUIRED gtk+-3.0>=3.20)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

add_library(_native_gtk3 MODULE ${NFD_SHARED_SRC})
target_include_directories(_native_gtk3 PRIVATE
  ${GTK3_INCLUDE_DIRS}
  ${Python3_INCLUDE_DIRS}
)
target_link_libraries(_native_gtk3 PRIVATE
  ${GTK3_LIBRARIES}
  Python3::Python
)
target_compile_options(_native_gtk3 PRIVATE ${GTK3_CFLAGS_OTHER})

set_target_properties(_native_gtk3 PROPERTIES
  PREFIX ""
  OUTPUT_NAME "_native_gtk3"
  SUFFIX "${CMAKE_SHARED_MODULE_SUFFIX}"
)
install(TARGETS _native_gtk3 LIBRARY DESTINATION native_file_dialog_gtk3)
install(FILES
  "${CMAKE_SOURCE_DIR}/src/native_file_dialog_gtk3/__init__.py"
  "${CMAKE_SOURCE_DIR}/src/native_file_dialog_gtk3/_native_gtk3.pyi"
  "${CMAKE_SOURCE_DIR}/src/native_file_dialog_gtk3/py.typed"
  DESTINATION native_file_dialog_gtk3)
