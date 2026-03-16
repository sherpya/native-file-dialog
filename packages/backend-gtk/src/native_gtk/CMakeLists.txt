# GTK4/libadwaita file dialog extension (Linux only).
cmake_minimum_required(VERSION 3.16)
project(native_gtk LANGUAGES C)

set(CMAKE_C_STANDARD 11)

find_package(PkgConfig REQUIRED)
# GtkFileDialog requires GTK 4.10+
pkg_check_modules(GTK4 REQUIRED gtk4>=4.10)
pkg_check_modules(ADW REQUIRED libadwaita-1)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

# Build shared module _native_gtk.so (Python C API extension)
add_library(_native_gtk MODULE ${CMAKE_CURRENT_SOURCE_DIR}/src/native_gtk.c)
target_compile_definitions(_native_gtk PRIVATE NFD_USE_GTK4)
target_include_directories(_native_gtk PRIVATE
  ${GTK4_INCLUDE_DIRS}
  ${ADW_INCLUDE_DIRS}
  ${Python3_INCLUDE_DIRS}
)
target_link_libraries(_native_gtk PRIVATE
  ${GTK4_LIBRARIES}
  ${ADW_LIBRARIES}
  Python3::Python
)
target_compile_options(_native_gtk PRIVATE ${GTK4_CFLAGS_OTHER} ${ADW_CFLAGS_OTHER})

set_target_properties(_native_gtk PROPERTIES
  PREFIX ""
  OUTPUT_NAME "_native_gtk"
  SUFFIX "${CMAKE_SHARED_MODULE_SUFFIX}"
)
install(TARGETS _native_gtk LIBRARY DESTINATION native_file_dialog_gtk)
install(FILES
  "${CMAKE_SOURCE_DIR}/src/native_file_dialog_gtk/__init__.py"
  "${CMAKE_SOURCE_DIR}/src/native_file_dialog_gtk/_native_gtk.pyi"
  "${CMAKE_SOURCE_DIR}/src/native_file_dialog_gtk/py.typed"
  DESTINATION native_file_dialog_gtk)
