# - Maya finder module
# This module searches for a valid Maya instalation, including its devkit,
# libraries, executables and related paths (scripts).
#
# Useful environment variables:
#  MAYA_LOCATION          If defined in the shell environment, the contents
#                         of this variable will be used as the first search
#                         path for the Maya installation.
#
# Output variables:
#  MAYA_FOUND             Defined if a Maya installation has been detected
#  MAYA_EXECUTABLE        Path to Maya's executable
#  MAYA_VERSION           Version of Maya determined from MAYA_EXECUTABLE (20xx)
#  MAYA_LIBRARIES         List of all Maya libraries that are found
#  MAYA_<lib>_FOUND       Defined if <lib> has been found
#  MAYA_<lib>_LIBRARY     Path to <lib> library
#  MAYA_INCLUDE_DIRS      Path to the devkit's include directories
#  MAYA_LIBRARY_DIRS      Path to the library directory
#  MAYA_PLUGIN_SUFFIX     File extension for the maya plugin
#  MAYA_QT_VERSION_SHORT  Version of Qt used by Maya (e.g. 4.7)
#  MAYA_QT_VERSION_LONG   Full version of Qt used by Maya (e.g. 4.7.1)
#
# Deprecated output variables:
#  MAYA_LIBRARY_DIR       Superseded by MAYA_LIBRARY_DIRS
#  MAYA_INCLUDE_DIR       Superseded by MAYA_INCLUDE_DIRS
#
# Macros provided:
#  MAYA_SET_PLUGIN_PROPERTIES  Passed the target name, this sets up typical
#                              plugin properties like macro defines, prefixes,
#                              and suffixes.
#
# Naming conventions:
#  Local variables of the form _maya_foo
#  Input variables from CMake of the form Maya_FOO
#  Output variables of the form MAYA_FOO
#

# OS variables
SET( _WINDOWS FALSE )
IF( "${CMAKE_SYSTEM_NAME}" MATCHES "Windows" )
  SET( _WINDOWS TRUE )
ENDIF()

SET( _DARWIN FALSE )
IF( "${CMAKE_SYSTEM_NAME}" MATCHES "Darwin" )
  SET( _DARWIN TRUE )
  IF( ${CMAKE_SYSTEM_VERSION} MATCHES "13." )
       ADD_DEFINITIONS( "-std=c++11" )
  ENDIF()
ENDIF()

SET( _LINUX FALSE )
IF( "${CMAKE_SYSTEM_NAME}" MATCHES "Linux" )
  SET( _LINUX TRUE )
ENDIF()


#=============================================================================
# Macros
#=============================================================================

# Macro for setting up typical plugin properties. These include:
#  - OS-specific plugin suffix (.mll, .so, .bundle)
#  - Removal of 'lib' prefix on osx/linux
#  - OS-specific defines
#  - Post-commnad for correcting Qt library linking on osx
#  - Windows link flags for exporting initializePlugin/uninitializePlugin
macro(MAYA_SET_PLUGIN_PROPERTIES target)

    if(APPLE)
        set(MAYA_EXTENSION ".bundle")
        set(MAYA_COMPILE_DEFINITIONS AW_NEW_IOSTREAMS REQUIRE_IOSTREAM _BOOL _DARWIN MAC_PLUGIN
            OSMac_ OSMac_MachO OSMacOSX_ CC_GNU_ _LANGUAGE_C_PLUS_PLUS)
        set(MAYA_COMPILE_FLAGS
          "-fno-gnu-keywords -include ${MAYA_INCLUDE_PATH}/maya/OpenMayaMac.h" )

        set(MAYA_LINK_FLAGS
          #"-dynamic -g -fPIC "
          #"-shared -g -fPIC "
          "-fno-gnu-keywords -framework System  -framework SystemConfiguration -framework CoreServices -framework Carbon -framework Cocoa -framework ApplicationServices -framework Quicktime -framework IOKit -bundle -fPIC -L${ALEMBIC_MAYA_LIB_ROOT} -Wl,-executable_path,${ALEMBIC_MAYA_LIB_ROOT}" )

        if(QT_LIBRARIES)
            set(_changes "")
            foreach(_lib ${QT_LIBRARIES})
                if("${_lib}" MATCHES ".*framework.*")
                    get_filename_component(_shortname ${_lib} NAME)
                    string(REPLACE ".framework" "" _shortname ${_shortname})
                    # FIXME: QT_LIBRARIES does not provide the entire path to the lib.
                    #  it provides /usr/local/qt/4.7.2/lib/QtGui.framework
                    #  but we need /usr/local/qt/4.7.2/lib/QtGui.framework/Versions/4/QtGui
                    # below is a hack, likely to break on other configurations
                    set(_changes ${_changes} "-change" "${_lib}/Versions/4/${_shortname}" "@executable_path/${_shortname}")
                endif()
            endforeach()

            add_custom_command(TARGET ${target}
                POST_BUILD
                COMMAND install_name_tool ${_changes} $<TARGET_FILE:${target}>)
        endif()

    elseif(WIN32)
        set(MAYA_EXTENSION ".mll")
        set(MAYA_COMPILE_DEFINITIONS REQUIRE_IOSTREAM _BOOL _AFXDLL _MBCS NT_PLUGIN)
        set(MAYA_LINK_FLAGS "/export:initializePlugin /export:uninitializePlugin")
        set( MAYA_COMPILE_FLAGS "/MD")
    else()
        set(MAYA_EXTENSION ".so")
        set(MAYA_COMPILE_DEFINITIONS REQUIRE_IOSTREAM _BOOL LINUX _LINUX LINUX_64)
        set(MAYA_COMPILE_FLAGS
          "-m64 -g -pthread -pipe -fPIC -Wno-deprecated -fno-gnu-keywords" )

        set(MAYA_LINK_FLAGS
          "-shared -m64 -g -pthread -pipe -fPIC -Wno-deprecated -fno-gnu-keywords -Wl,-Bsymbolic" )
    endif()

    set_target_properties( ${target} PROPERTIES
        COMPILE_DEFINITIONS "${MAYA_COMPILE_DEFINITIONS}"
        COMPILE_FLAGS "${MAYA_COMPILE_FLAGS}"
        LINK_FLAGS "${MAYA_LINK_FLAGS}"
        PREFIX ""
        SUFFIX ${MAYA_EXTENSION}
    )

endmacro(MAYA_SET_PLUGIN_PROPERTIES)


set(_maya_TEST_VERSIONS)
set(_maya_KNOWN_VERSIONS "2008" "2009" "2010" "2011" "2012" "2013" "2014" "2015" "2016" "2017" "2018" "2019" "2020")

if(APPLE)
    set(MAYA_PLUGIN_SUFFIX ".bundle")
elseif(WIN32)
    set(MAYA_PLUGIN_SUFFIX ".mll")
else() #LINUX
    set(MAYA_PLUGIN_SUFFIX ".so")
endif()

# generate list of versions to test
if(Maya_FIND_VERSION_EXACT)
    list(APPEND _maya_TEST_VERSIONS "${Maya_FIND_VERSION}")
else()
    # exact version not requested. we have some wiggle room
    if(Maya_FIND_VERSION)
        # loop through known versions and find anything >= requested
        foreach(version ${_maya_KNOWN_VERSIONS})
            if(NOT "${version}" VERSION_LESS "${Maya_FIND_VERSION}")
                list(APPEND _maya_TEST_VERSIONS "${version}")
            endif()
        endforeach()
    else()
        # no version specified: test everything
        set(_maya_TEST_VERSIONS ${_maya_KNOWN_VERSIONS})
    endif()
endif()

# create empty list
set(_maya_TEST_PATHS)

# from version list, generate list of paths to test based on canonical locations
foreach(version ${_maya_TEST_VERSIONS})
    if(APPLE)
        list(APPEND _maya_TEST_PATHS "/Applications/Autodesk/maya${version}/Maya.app/Contents")
    elseif(WIN32)
        set(_maya_TEST_PATHS ${_maya_TEST_PATHS}
            "$ENV{PROGRAMFILES}/Autodesk/Maya${version}-x64"
            "$ENV{PROGRAMFILES}/Autodesk/Maya${version}"
            "C:/Program Files/Autodesk/Maya${version}-x64"
            "C:/Program Files/Autodesk/Maya${version}"
            "C:/Program Files (x86)/Autodesk/Maya${version}")
    else() #Linux
        set(_maya_TEST_PATHS ${_maya_TEST_PATHS}
            "/usr/autodesk/maya${version}-x64"
            "/usr/autodesk/maya${version}")
    endif()
endforeach(version)

# search for maya executable within the MAYA_LOCATION and PATH env vars and test paths

if(Maya_FIND_VERSION_EXACT)
    find_program(MAYA_EXECUTABLE_${Maya_FIND_VERSION} maya
        PATHS ${_maya_TEST_PATHS}
        PATH_SUFFIXES bin
        DOC "Maya's executable path")

    set(MAYA_EXECUTABLE ${MAYA_EXECUTABLE_${Maya_FIND_VERSION}})
else()
    find_program(MAYA_EXECUTABLE maya
        PATHS ${_maya_TEST_PATHS}
        PATH_SUFFIXES bin
        DOC "Maya's executable path")
endif()

if(MAYA_EXECUTABLE)
    # TODO: use GET_FILENAME_COMPONENT here
    # derive MAYA_LOCATION from MAYA_EXECUTABLE
    string(REGEX REPLACE "/bin/maya.*" "" MAYA_LOCATION "${MAYA_EXECUTABLE}")

    string(REGEX MATCH "20[0-9][0-9]" MAYA_VERSION "${MAYA_LOCATION}")

    if(Maya_FIND_VERSION)
        # test that we've found a valid version
        list(FIND _maya_TEST_VERSIONS ${MAYA_VERSION} _maya_FOUND_INDEX)
        if(${_maya_FOUND_INDEX} EQUAL -1)
            message(STATUS "Found Maya version ${MAYA_VERSION}, but requested at least ${Maya_FIND_VERSION}. Re-searching without environment variables...")
            set(MAYA_LOCATION NOTFOUND)
            # search again, but don't use environment variables
            # (these should be only paths we constructed based on requested version)
            find_path(MAYA_LOCATION maya
                PATHS ${_maya_TEST_PATHS}
                PATH_SUFFIXES bin
                DOC "Maya's Base Directory"
                NO_SYSTEM_ENVIRONMENT_PATH)
            set(MAYA_EXECUTABLE "${MAYA_LOCATION}/bin/maya"
                CACHE PATH "Maya's executable path")
            string(REGEX MATCH "20[0-9][0-9]" MAYA_VERSION "${MAYA_LOCATION}")
        #ELSE: error?
        endif()
    endif()
endif()

# Qt Versions
if(${MAYA_VERSION} STREQUAL "2011")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "4.5")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "4.5.3")
elseif(${MAYA_VERSION} STREQUAL "2012")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "4.7")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "4.7.1")
elseif(${MAYA_VERSION} STREQUAL "2013")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "4.7")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "4.7.1")
elseif(${MAYA_VERSION} STREQUAL "2014")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "4.8")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "4.8.2")
elseif(${MAYA_VERSION} STREQUAL "2015")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "4.8")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "4.8.5")
elseif(${MAYA_VERSION} STREQUAL "2016")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "4.8")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "4.8.6")
elseif(${MAYA_VERSION} STREQUAL "2017")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "5.6")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "5.6.1")
elseif(${MAYA_VERSION} STREQUAL "2018")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "5.6")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "5.6.1")
elseif(${MAYA_VERSION} STREQUAL "2019")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "5.6")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "5.6.1")
elseif(${MAYA_VERSION} STREQUAL "2020")
    set(MAYA_QT_VERSION_SHORT CACHE STRING "5.12")
    set(MAYA_QT_VERSION_LONG  CACHE STRING "5.12.5")
endif()

# NOTE: the MAYA_LOCATION environment variable is often misunderstood.  On every OS it is expected to point
# directly above bin/maya. Relative paths from $MAYA_LOCATION to include, lib, and devkit directories vary depending on OS.

# We don't use environment variables below this point to lessen the risk of finding incompatible versions of
# libraries and includes (it could happen with highly non-standard configurations; i.e. maya libs in /usr/local/lib or on
# CMAKE_LIBRARY_PATH, CMAKE_INCLUDE_PATH, CMAKE_PREFIX_PATH).
# - If the maya executable is found in a standard location, or in $MAYA_LOCATION/bin or $PATH, and the
#   includes and libs are in standard locations relative to the binary, they will be found

message(STATUS "Maya location: ${MAYA_LOCATION}")

if(Maya_FIND_VERSION_EXACT)
    find_path(MAYA_INCLUDE_DIRS_${Maya_FIND_VERSION} maya/MFn.h
        HINTS ${MAYA_LOCATION}
        PATH_SUFFIXES
            include               # linux and windows
            ../../devkit/include  # osx
        DOC "Maya's include path")
    set(MAYA_INCLUDE_DIRS ${MAYA_INCLUDE_DIRS_${Maya_FIND_VERSION}})
else()
    find_path(MAYA_INCLUDE_DIRS maya/MFn.h
        HINTS ${MAYA_LOCATION}
        PATH_SUFFIXES
            include               # linux and windows
            ../../devkit/include  # osx
        DOC "Maya's include path")
endif()

if(Maya_FIND_VERSION_EXACT)
    find_path(MAYA_LIBRARY_DIRS_${Maya_FIND_VERSION} libOpenMaya.dylib libOpenMaya.so OpenMaya.lib
        HINTS ${MAYA_LOCATION}
        PATH_SUFFIXES
            lib    # linux and windows
            MacOS  # osx
        DOC "Maya's library path")
    set(MAYA_LIBRARY_DIRS ${MAYA_LIBRARY_DIRS_${Maya_FIND_VERSION}})
else()
    find_path(MAYA_LIBRARY_DIRS libOpenMaya.dylib libOpenMaya.so OpenMaya.lib
        HINTS ${MAYA_LOCATION}
        PATH_SUFFIXES
            lib    # linux and windows
            MacOS  # osx
        DOC "Maya's library path")
endif()

# Set deprecated variables to avoid compatibility breaks
set(MAYA_INCLUDE_DIR ${MAYA_INCLUDE_DIRS})
set(MAYA_LIBRARY_DIR ${MAYA_LIBRARY_DIRS})

foreach(_maya_lib
    OpenMaya
    OpenMayaAnim
    OpenMayaFX
    OpenMayaRender
    OpenMayaUI
    Image
    Foundation
#    IMFbase  # not available in Maya 2020
    tbb)
#   cg
#   cgGL
    # HINTS is searched before PATHS, so preference is given to MAYA_LOCATION
    # (set via MAYA_EXECUTABLE)

    if(Maya_FIND_VERSION_EXACT)
        if(APPLE)
            find_library(MAYA_${_maya_lib}_LIBRARY_${Maya_FIND_VERSION} ${_maya_lib}
                HINTS ${MAYA_LOCATION}
                PATHS ${_maya_TEST_PATHS}
                PATH_SUFFIXES MacOS
                # This must be used or else Foundation.framework will be found instead of libFoundation
                NO_CMAKE_SYSTEM_PATH
                DOC "Maya's ${MAYA_LIB} library path")
        else()
            find_library(MAYA_${_maya_lib}_LIBRARY_${Maya_FIND_VERSION} ${_maya_lib}
                HINTS ${MAYA_LOCATION}
                PATHS ${_maya_TEST_PATHS}
                PATH_SUFFIXES lib # linux and windows
                DOC "Maya's ${MAYA_LIB} library path")
        endif()
        list(APPEND MAYA_LIBRARIES_${Maya_FIND_VERSION} ${MAYA_${_maya_lib}_LIBRARY_${Maya_FIND_VERSION}})
    else()
        if(APPLE)
            find_library(MAYA_${_maya_lib}_LIBRARY ${_maya_lib}
                HINTS ${MAYA_LOCATION}
                PATHS ${_maya_TEST_PATHS}
                PATH_SUFFIXES MacOS
                # This must be used or else Foundation.framework will be found instead of libFoundation
                NO_CMAKE_SYSTEM_PATH
                DOC "Maya's ${MAYA_LIB} library path")
        else()
            find_library(MAYA_${_maya_lib}_LIBRARY ${_maya_lib}
                HINTS ${MAYA_LOCATION}
                PATHS ${_maya_TEST_PATHS}
                PATH_SUFFIXES lib # linux and windows
                DOC "Maya's ${MAYA_LIB} library path")
        endif()
        list(APPEND MAYA_LIBRARIES ${MAYA_${_maya_lib}_LIBRARY})
    endif()
endforeach()

if(Maya_FIND_VERSION_EXACT)
    set(MAYA_LIBRARIES ${MAYA_LIBRARIES_${Maya_FIND_VERSION}})
endif()

find_path(MAYA_USER_DIR
    NAMES ${MAYA_VERSION}-x64 ${MAYA_VERSION}
    PATHS
        $ENV{HOME}/Library/Preferences/Autodesk/maya  # osx
        $ENV{USERPROFILE}/Documents/maya              # windows
        $ENV{HOME}/maya                               # linux
    DOC "Maya user home directory"
    NO_SYSTEM_ENVIRONMENT_PATH)

# if (Maya_FOUND)
#     if (NOT Maya_FIND_QUIETLY)
#         message(STATUS "Maya version: ${Maya_MAJOR_VERSION}.${Maya_MINOR_VERSION}.${Maya_SUBMINOR_VERSION}")
#     endif()
#     if (NOT Maya_FIND_QUIETLY)
#         message(STATUS "Found the following Maya libraries:")
#     endif()
#     foreach(COMPONENT ${Maya_FIND_COMPONENTS})
#         string(TOUPPER ${COMPONENT} UPPERCOMPONENT)
#         if(Maya_${UPPERCOMPONENT}_FOUND)
#             if(NOT Maya_FIND_QUIETLY)
#                 message(STATUS "  ${COMPONENT}")
#             endif()
#             set(Maya_LIBRARIES ${Maya_LIBRARIES} ${Maya_${UPPERCOMPONENT}_LIBRARY})
#         endif()
#     endforeach()
# else()
#     if(Maya_FIND_REQUIRED)
#         message(SEND_ERROR "Unable to find the requested Maya libraries.\n${Maya_ERROR_REASON}")
#     endif()
# endif()

# Handles the QUIETLY and REQUIRED arguments and sets MAYA_FOUND to TRUE if
# all passed variables are TRUE
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Maya
    MAYA_LIBRARIES MAYA_EXECUTABLE MAYA_INCLUDE_DIRS
    MAYA_LIBRARY_DIRS MAYA_VERSION MAYA_PLUGIN_SUFFIX
    MAYA_USER_DIR)


#
# Copyright 2012, Chad Dombrova
#
# vfxcmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vfxcmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with vfxcmake.  If not, see <http://www.gnu.org/licenses/>.
#
