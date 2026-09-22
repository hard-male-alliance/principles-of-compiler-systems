cmake_minimum_required(VERSION 3.25)
project(compiler_preflight LANGUAGES NONE)

# 该工程编排可检查的编译器观测，不把生成的案例误当作宿主程序。
# This project orchestrates inspectable compiler observations; it does not model the case as a host program.
find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)
find_program(PREFLIGHT_CLANG NAMES clang REQUIRED)

set(PREFLIGHT_RISCV "AUTO" CACHE STRING "RV64 validation mode: AUTO, ON, or OFF")
set_property(CACHE PREFLIGHT_RISCV PROPERTY STRINGS AUTO ON OFF)
find_program(PREFLIGHT_RISCV_GCC NAMES riscv64-linux-gnu-gcc)
find_program(PREFLIGHT_QEMU NAMES qemu-riscv64)

if(PREFLIGHT_RISCV STREQUAL "ON")
  if(NOT PREFLIGHT_RISCV_GCC OR NOT PREFLIGHT_QEMU)
    message(FATAL_ERROR "PREFLIGHT_RISCV=ON requires riscv64-linux-gnu-gcc and qemu-riscv64")
  endif()
  set(PREFLIGHT_MODE full)
elseif(PREFLIGHT_RISCV STREQUAL "AUTO" AND CMAKE_HOST_SYSTEM_NAME STREQUAL "Linux"
       AND PREFLIGHT_RISCV_GCC AND PREFLIGHT_QEMU)
  set(PREFLIGHT_MODE full)
elseif(PREFLIGHT_RISCV STREQUAL "OFF" OR PREFLIGHT_RISCV STREQUAL "AUTO")
  set(PREFLIGHT_MODE portable)
else()
  message(FATAL_ERROR "PREFLIGHT_RISCV must be AUTO, ON, or OFF")
endif()

set(PREFLIGHT_OUTPUT "${CMAKE_BINARY_DIR}/artifacts")
set(CAPTURE_COMMAND
    "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/capture.py"
    --root "${CMAKE_CURRENT_SOURCE_DIR}"
    --output "${PREFLIGHT_OUTPUT}"
    --mode "${PREFLIGHT_MODE}"
    --clang "${PREFLIGHT_CLANG}")
set(VERIFY_COMMAND
    "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/verify.py"
    --output "${PREFLIGHT_OUTPUT}"
    --mode "${PREFLIGHT_MODE}")

add_custom_target(artifacts
  COMMAND ${CAPTURE_COMMAND}
  COMMENT "Capturing ${PREFLIGHT_MODE} compiler-pipeline artifacts / 捕获编译流水线产物"
  VERBATIM)

add_custom_target(verify
  COMMAND ${VERIFY_COMMAND}
  DEPENDS artifacts
  COMMENT "Verifying structural and behavioral contracts / 验证结构与行为契约"
  VERBATIM)

enable_testing()
add_test(NAME capture_pipeline COMMAND ${CAPTURE_COMMAND})
add_test(NAME verify_pipeline COMMAND ${VERIFY_COMMAND})
set_tests_properties(verify_pipeline PROPERTIES DEPENDS capture_pipeline)

message(STATUS "Preflight mode: ${PREFLIGHT_MODE}")
message(STATUS "Artifacts: ${PREFLIGHT_OUTPUT}")
