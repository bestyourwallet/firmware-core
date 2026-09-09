cmake_minimum_required(VERSION 3.28)

project(UKey C ASM)

find_package(Git QUIET)
if(NOT DEFINED BUILD_COMMIT)
    if(GIT_FOUND)
        execute_process(
            COMMAND ${GIT_EXECUTABLE} rev-parse --short=7 HEAD
            WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
            OUTPUT_VARIABLE BUILD_COMMIT
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
    endif()
endif()
if(NOT BUILD_COMMIT)
    set(BUILD_COMMIT "unknown")
endif()

message(STATUS "BUILD_COMMIT=${BUILD_COMMIT}")

set(REPO_ROOT "${CMAKE_SOURCE_DIR}/..")
set(VERSION_SCRIPT "${REPO_ROOT}/tools/version.sh")

function(read_version_from_header OUT_VAR HEADER_PATH)
    if(EXISTS "${HEADER_PATH}")
        execute_process(
            COMMAND ${VERSION_SCRIPT} ${HEADER_PATH}
            OUTPUT_VARIABLE _VER_RAW
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        if(_VER_RAW)
            set(_VER "${_VER_RAW}")
        else()
            set(_VER "0.0.0")
        endif()
    else()
        set(_VER "0.0.0")
    endif()
    set(${OUT_VAR} "${_VER}" PARENT_SCOPE)
endfunction()

read_version_from_header(BOARD_BUILD_VERSION "${CMAKE_SOURCE_DIR}/embed/boardloader/version.h")
read_version_from_header(BOOT_BUILD_VERSION "${CMAKE_SOURCE_DIR}/embed/bootloader/version.h")
message(STATUS "BOARD_BUILD_VERSION=${BOARD_BUILD_VERSION}")
message(STATUS "BOOT_BUILD_VERSION=${BOOT_BUILD_VERSION}")

option(BUILD_BOARDLOADER "Build boardloader target" ON)
option(BUILD_BOOTLOADER "Build bootloader target" ON)

if(BUILD_BOARDLOADER)
    include(cmake/boardloader.cmake)
endif()

if(BUILD_BOOTLOADER)
    include(cmake/bootloader.cmake)
endif()
