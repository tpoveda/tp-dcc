cmake_minimum_required(VERSION 3.0)
project(tpDccMayaPlugins)

# Cmake custom finders
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/tp/maya/plugins/cmake")

add_subdirectory(tp/maya/plugins/helloworld)