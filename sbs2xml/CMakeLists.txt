cmake_minimum_required(VERSION 3.0)

find_package(BISON)
find_package(FLEX 2.5.35)

BISON_TARGET(Parser parser.y ${CMAKE_CURRENT_BINARY_DIR}/parser.cpp)
FLEX_TARGET(Scanner lexer.l  ${CMAKE_CURRENT_BINARY_DIR}/lexer.cpp)
ADD_FLEX_BISON_DEPENDENCY(Scanner Parser)

#add_definitions(-DYYDEBUG=1)
add_definitions(-DYY_BUF_SIZE=32768)

include_directories(${CMAKE_CURRENT_BINARY_DIR})
add_executable(sbs2xml
    main.cpp
    ${BISON_Parser_OUTPUTS}
    ${FLEX_Scanner_OUTPUTS}
)
