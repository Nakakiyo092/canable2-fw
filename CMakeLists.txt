# No operating system
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_SYSTEM_VERSION 1)
cmake_minimum_required(VERSION 3.21)

set(COMMAND_GIT_DESCRIBE "git describe --abbrev=7 --dirty --always --tags")
set(COMMAND_GIT_CONFIG "git config --get remote.origin.url | sed 's/^.*github/github/'")
execute_process(
    COMMAND bash -c "${COMMAND_GIT_DESCRIBE}"
    OUTPUT_VARIABLE GIT_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
    COMMAND bash -c "${COMMAND_GIT_CONFIG}"
    OUTPUT_VARIABLE GIT_REMOTE
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT GIT_VERSION OR NOT GIT_REMOTE)
    message(STATUS "GIT_VERSION or GIT_REMOTE is empty or undefined.")
    set(GIT_VERSION "1234567")
    set(GIT_REMOTE "1234567")
else ()
    
endif()

set(TARGET canable2-${GIT_VERSION})

message(STATUS "TARGET name: ${TARGET}")

set(MAIN_CMAKETXT_PATH ${CMAKE_CURRENT_SOURCE_DIR})

# specify cross compilers and tools
set(COMPIL_PATH "C:/Program Files (x86)/GNU Arm Embedded Toolchain/10 2021.10/bin/")
set(COMPIL_PREFIX "arm-none-eabi-")
set(CMAKE_C_COMPILER ${COMPIL_PATH}${COMPIL_PREFIX}gcc.exe)
set(CMAKE_CXX_COMPILER ${COMPIL_PATH}${COMPIL_PREFIX}g++.exe)
set(CMAKE_ASM_COMPILER ${COMPIL_PATH}${COMPIL_PREFIX}gcc.exe)
set(CMAKE_AR ${COMPIL_PATH}${COMPIL_PREFIX}ar.exe)
set(CMAKE_OBJCOPY ${COMPIL_PATH}${COMPIL_PREFIX}objcopy.exe)
set(CMAKE_OBJDUMP ${COMPIL_PATH}${COMPIL_PREFIX}objdump.exe)
set(SIZE ${COMPIL_PATH}${COMPIL_PREFIX}size.exe)
# skip compiler checks
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(CMAKE_FIND_ROOT_PATH "C:/Program Files (x86)/GNU Arm Embedded Toolchain/10 2021.10/")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

project(${TARGET} C CXX ASM)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_STANDARD 11)

add_compile_options(-mcpu=cortex-m4 -mthumb -mthumb-interwork)
add_compile_options(-ffunction-sections -fdata-sections -fno-common -fmessage-length=0)

# uncomment to mitigate c++17 absolute addresses warnings
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-register")

# Enable assembler files preprocessing
add_compile_options($<$<COMPILE_LANGUAGE:ASM>:-x$<SEMICOLON>assembler-with-cpp>)

if ("${CMAKE_BUILD_TYPE}" STREQUAL "Release")
    message(STATUS "Maximum optimization for speed")
    add_compile_options(-Ofast)
elseif ("${CMAKE_BUILD_TYPE}" STREQUAL "RelWithDebInfo")
    message(STATUS "Maximum optimization for speed, debug info included")
    add_compile_options(-Ofast -g)
elseif ("${CMAKE_BUILD_TYPE}" STREQUAL "MinSizeRel")
    message(STATUS "Maximum optimization for size")
    add_compile_options(-Os)
else ()
    message(STATUS "Minimal optimization, debug info included")
    add_compile_options(-Og -g)
endif ()

set(CMSIS_PATH ${CMAKE_CURRENT_SOURCE_DIR}/Drivers/CMSIS)
set(CMSIS_DEVICE_PATH ${CMSIS_PATH}/Device/ST/STM32G4xx)
set(DRIVER_PATH ${CMAKE_CURRENT_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver)
set(USB_INCLUDES 
    ${CMAKE_CURRENT_SOURCE_DIR}/Middlewares/ST/STM32_USB_Device_Library/Core/Inc
    ${CMAKE_CURRENT_SOURCE_DIR}/Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc
)
list(
    APPEND INCLUDE_PATH
    ${CMSIS_PATH}/Include
    ${CMSIS_DEVICE_PATH}/Include
    ${DRIVER_PATH}/Inc
    ${CMAKE_CURRENT_SOURCE_DIR}/inc
    ${USB_INCLUDES}
    ${USER_INCLUDES}
)

include_directories(
    ${INCLUDE_PATH}
)

aux_source_directory(${MAIN_CMAKETXT_PATH}/drivers/STM32G4xx_HAL_Driver/Src HAL_DRIVER)
aux_source_directory(${MAIN_CMAKETXT_PATH}/src MAIN)
set(USB_MID_PATH "${MAIN_CMAKETXT_PATH}/Middlewares/ST/STM32_USB_Device_Library")
list(
    APPEND USB_MID
    ${USB_MID_PATH}/Core/Src/usbd_ctlreq.c
    ${USB_MID_PATH}/Core/Src/usbd_ioreq.c
    ${USB_MID_PATH}/Core/Src/usbd_core.c
    ${USB_MID_PATH}/Class/CDC/Src/usbd_cdc.c
)

add_library(stm32cube STATIC ${HAL_DRIVER})

set(STARTUP       ${MAIN_CMAKETXT_PATH}/src/startup_stm32g431xx.s)
set(LINKER_SCRIPT ${MAIN_CMAKETXT_PATH}/STM32G431CBTx_FLASH.ld)
message(STATUS "STARTUP name: ${STARTUP}")
message(STATUS "LINKER_SCRIPT name: ${LINKER_SCRIPT}")

add_definitions(-DGIT_VERSION=\"${GIT_VERSION}\" -DGIT_REMOTE=\"${GIT_REMOTE}\" -DSTM32G431xx -DHSI48_VALUE=48000000 -DHSE_VALUE=25000000 -DINTERNAL_OSCILLATOR)

add_compile_options(-DHSI48_VALUE=48000000 -DHSE_VALUE=25000000)
add_compile_options(-Wall -g -gdwarf-2 -fno-exceptions -ffunction-sections -fdata-sections -Wl,--gc-sections)

add_link_options(-Wl,-gc-sections,--print-memory-usage,-Map=${PROJECT_BINARY_DIR}/${PROJECT_NAME}.map)
add_link_options(-mcpu=cortex-m4 -mthumb)
add_link_options(-T ${LINKER_SCRIPT})
add_link_options(-lc -lm -lnosys)
add_link_options(-Wimplicit-function-declaration -Wcpp)

add_executable(${PROJECT_NAME}.elf ${SYSTEM} ${USB_MID} ${MAIN} ${STARTUP} ${LINKER_SCRIPT})

target_link_libraries(${PROJECT_NAME}.elf stm32cube)

set(HEX_FILE ${PROJECT_BINARY_DIR}/${PROJECT_NAME}.hex)
set(BIN_FILE ${PROJECT_BINARY_DIR}/${PROJECT_NAME}.bin)

add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
        COMMAND ${CMAKE_OBJCOPY} -Oihex $<TARGET_FILE:${PROJECT_NAME}.elf> ${HEX_FILE}
        COMMAND ${CMAKE_OBJCOPY} -Obinary $<TARGET_FILE:${PROJECT_NAME}.elf> ${BIN_FILE}
        COMMENT "Building ${HEX_FILE}
Building ${BIN_FILE}")

add_custom_target(upload
    COMMAND scp ${CMAKE_BINARY_DIR}/example_program user@remote.server.com:/home/user/bin/
    DEPENDS example_program
    COMMENT "Uploading example_program to remote.server.com"
)