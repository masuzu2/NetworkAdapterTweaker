cmake_minimum_required(VERSION 3.15)
project(NetworkAdapterTweaker LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

add_executable(NetworkAdapterTweaker WIN32
    src/main.cpp
    src/gui.cpp
    src/adapter.cpp
)

target_include_directories(NetworkAdapterTweaker PRIVATE src)
target_link_libraries(NetworkAdapterTweaker PRIVATE
    comctl32 gdi32 user32 advapi32 ole32 oleaut32 wbemuuid shell32
)

# UTF-8 source
if(MSVC)
    target_compile_options(NetworkAdapterTweaker PRIVATE /utf-8)
endif()
