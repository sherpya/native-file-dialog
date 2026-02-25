cmake_minimum_required(VERSION 3.16)
project(native-file-dialog LANGUAGES C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
  find_package(pybind11 REQUIRED)
endif()

# Linux-only: build Qt and GTK native extensions.
# On Windows/macOS, Python uses PyWin32/osascript and tkinter only.
if(UNIX AND NOT APPLE)
  set(NFD_PACKAGE_DIR "${SKBUILD_PLATLIB_DIR}/native_file_dialog" CACHE PATH "Install dir for native_file_dialog extensions")
  add_subdirectory(src/native_qt)
  add_subdirectory(src/native_gtk)
endif()

# Copy pure Python package into platlib so wheel contains it.
# scikit-build-core handles wheel.packages; we only need to install extensions here.
if(UNIX AND NOT APPLE)
  install(CODE "
    message(STATUS \"Native extensions will be installed to ${NFD_PACKAGE_DIR}\")
  ")
endif()
