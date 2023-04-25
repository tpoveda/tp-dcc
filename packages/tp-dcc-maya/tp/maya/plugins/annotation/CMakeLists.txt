# Source
set(PLUGIN_SOURCES_DIR ${CMAKE_CURRENT_LIST_DIR}/source)
set(PLUGIN_HEADERS_DIR ${CMAKE_CURRENT_LIST_DIR}/include)

file(GLOB_RECURSE PLUGIN_SOURCES ${PLUGIN_SOURCES_DIR}/*.c ${PLUGIN_SOURCES_DIR}/*.cpp)
file(GLOB_RECURSE PLUGIN_HEADERS ${PLUGIN_HEADERS_DIR}/*.h ${PLUGIN_HEADERS_DIR}/*.hpp)

# List of supported Maya versions
set(MAYA_VERSIONS "2022" "2023")

foreach(VERSION_FOUND IN LISTS MAYA_VERSIONS)
    
    set(Maya_FIND_VERSION_EXACT 1)
	set(Maya_FIND_VERSION ${VERSION_FOUND})
    find_package(Maya REQUIRED)

    # OpenGL is required
    find_package(OpenGL REQUIRED)

    # Plugin Name and folder
    set(PLUGIN_NAME tpAnnotation_maya${MAYA_VERSION})
    set(PLUGINS_FOLDER Plugins/Maya/${MAYA_VERSION})

    # Setup Plugin project
    add_library(${PLUGIN_NAME} SHARED ${PLUGIN_SOURCES})
    set_target_properties(${PLUGIN_NAME} PROPERTIES FOLDER ${PLUGINS_FOLDER})
    target_include_directories(${PLUGIN_NAME} PRIVATE include)
    target_include_directories(${PLUGIN_NAME} PUBLIC ${MAYA_INCLUDE_DIRS})
    target_link_directories(${PLUGIN_NAME} PRIVATE ${MAYA_LIBRARIES})
    target_link_libraries(${PLUGIN_NAME} PRIVATE ${MAYA_LIBRARIES})
    target_include_directories(${PLUGIN_NAME} PUBLIC ${OPENGL_INCLUDE_DIRS})
    target_link_libraries(${PLUGIN_NAME} PRIVATE ${OPENGL_LIBRARIES})


    # this is a macro defined in FindMaya that sets up our plugin with standard Maya build settings
    MAYA_SET_PLUGIN_PROPERTIES(${PLUGIN_NAME})
    #install(TARGETS ${PLUGIN_NAME} ${MAYA_TARGET_TYPE} DESTINATION plug-ins)
endforeach()

source_group("Include" FILES ${PLUGIN_HEADERS})
source_group("Source" FILES ${PLUGIN_SOURCES})
set_property(GLOBAL PROPERTY USE_FOLDERS ON)
