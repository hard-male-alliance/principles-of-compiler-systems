cmake_minimum_required(VERSION 3.25)

# 本项目只编排外部编译阶段，不让 CMake 隐式选择宿主 ABI。
# This project orchestrates explicit compiler stages and avoids an implicit host ABI.
project(compiler_preflight LANGUAGES NONE)

include(CTest)
find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)
find_program(CLANG_EXECUTABLE NAMES clang REQUIRED)
find_program(RISCV_GCC_EXECUTABLE NAMES riscv64-linux-gnu-gcc)
find_program(QEMU_RISCV64_EXECUTABLE NAMES qemu-riscv64)

set(ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/..")
set(SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/src/compiler_tour.sy")
set(BUILTIN_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/include/sysy_builtin.h")
set(HAND_IR "${CMAKE_CURRENT_SOURCE_DIR}/ir/compiler_tour.ll")
set(HAND_ASM "${CMAKE_CURRENT_SOURCE_DIR}/asm/compiler_tour_rv64gc.s")
set(GENERATED "${CMAKE_CURRENT_BINARY_DIR}/generated")
set(RISCV_FLAGS --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d)

file(MAKE_DIRECTORY "${GENERATED}")

add_custom_command(
  OUTPUT "${GENERATED}/compiler_tour.i"
  COMMAND "${CLANG_EXECUTABLE}" -E -x c -include "${BUILTIN_HEADER}" "${SOURCE}"
          -o "${GENERATED}/compiler_tour.i"
  DEPENDS "${SOURCE}" "${BUILTIN_HEADER}"
  COMMENT "Preprocessing SysY-compatible source / 预处理 SysY 兼容源码"
  VERBATIM)

add_custom_command(
  OUTPUT "${GENERATED}/compiler_tour.ast.json"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/capture.py"
          --output "${GENERATED}/compiler_tour.ast.json" --
          "${CLANG_EXECUTABLE}" -x c -include "${BUILTIN_HEADER}" -Xclang -ast-dump=json
          -fsyntax-only "${SOURCE}"
  DEPENDS "${SOURCE}" "${BUILTIN_HEADER}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/capture.py"
  COMMENT "Dumping Clang AST / 导出 Clang AST"
  VERBATIM)

add_custom_command(
  OUTPUT "${GENERATED}/compiler_tour.from-source.ll"
  COMMAND "${CLANG_EXECUTABLE}" -x c -include "${BUILTIN_HEADER}" -S -emit-llvm -O0
          "${SOURCE}" -o "${GENERATED}/compiler_tour.from-source.ll"
  DEPENDS "${SOURCE}" "${BUILTIN_HEADER}"
  COMMENT "Emitting LLVM IR / 生成 LLVM IR"
  VERBATIM)

add_custom_command(
  OUTPUT "${GENERATED}/compiler_tour.from-source.s"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -x c -include "${BUILTIN_HEADER}" -S -O0
          "${SOURCE}" -o "${GENERATED}/compiler_tour.from-source.s"
  DEPENDS "${SOURCE}" "${BUILTIN_HEADER}"
  COMMENT "Lowering source to RV64GC assembly / 将源码降低为 RV64GC 汇编"
  VERBATIM)

add_custom_command(
  OUTPUT "${GENERATED}/compiler_tour.from-source.o"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -x c -include "${BUILTIN_HEADER}" -c -O0
          "${SOURCE}" -o "${GENERATED}/compiler_tour.from-source.o"
  DEPENDS "${SOURCE}" "${BUILTIN_HEADER}"
  COMMENT "Assembling compiler-generated assembly / 汇编编译器生成的汇编"
  VERBATIM)

add_custom_command(
  OUTPUT "${GENERATED}/compiler_tour.from-ir.o"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -c "${HAND_IR}"
          -o "${GENERATED}/compiler_tour.from-ir.o"
  DEPENDS "${HAND_IR}"
  COMMENT "Compiling handwritten LLVM IR / 编译手写 LLVM IR"
  VERBATIM)

add_custom_command(
  OUTPUT "${GENERATED}/compiler_tour.from-asm.o"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -c "${HAND_ASM}"
          -o "${GENERATED}/compiler_tour.from-asm.o"
  DEPENDS "${HAND_ASM}"
  COMMENT "Assembling handwritten RV64GC / 汇编手写 RV64GC"
  VERBATIM)

set(PIPELINE_OUTPUTS
  "${GENERATED}/compiler_tour.i"
  "${GENERATED}/compiler_tour.ast.json"
  "${GENERATED}/compiler_tour.from-source.ll"
  "${GENERATED}/compiler_tour.from-source.s"
  "${GENERATED}/compiler_tour.from-source.o"
  "${GENERATED}/compiler_tour.from-ir.o"
  "${GENERATED}/compiler_tour.from-asm.o")

add_custom_target(pipeline DEPENDS ${PIPELINE_OUTPUTS})
add_custom_target(
  check_pipeline
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_artifacts.py"
          --preprocessed "${GENERATED}/compiler_tour.i"
          --ast "${GENERATED}/compiler_tour.ast.json"
          --llvm "${GENERATED}/compiler_tour.from-source.ll"
          --assembly "${GENERATED}/compiler_tour.from-source.s"
          --object "${GENERATED}/compiler_tour.from-source.o"
          --object "${GENERATED}/compiler_tour.from-ir.o"
          --object "${GENERATED}/compiler_tour.from-asm.o"
  DEPENDS pipeline "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_artifacts.py"
  COMMENT "Checking stage artifacts / 检查各阶段产物"
  VERBATIM)

add_custom_target(
  check_advanced
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_advanced.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/advanced/add.mlir"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/advanced/add.mlir"
          "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_advanced.py"
  COMMENT "Checking static AscendNPU IR evidence / 检查 AscendNPU IR 静态证据"
  VERBATIM)

add_test(NAME pipeline_artifacts
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_artifacts.py"
          --preprocessed "${GENERATED}/compiler_tour.i"
          --ast "${GENERATED}/compiler_tour.ast.json"
          --llvm "${GENERATED}/compiler_tour.from-source.ll"
          --assembly "${GENERATED}/compiler_tour.from-source.s"
          --object "${GENERATED}/compiler_tour.from-source.o"
          --object "${GENERATED}/compiler_tour.from-ir.o"
          --object "${GENERATED}/compiler_tour.from-asm.o")
set_tests_properties(pipeline_artifacts PROPERTIES REQUIRED_FILES "${GENERATED}/compiler_tour.from-asm.o")
add_test(NAME advanced_structure
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_advanced.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/advanced/add.mlir")

# 宿主执行只在 POSIX 上启用，因为课程运行时依赖 sys/time.h。
# Native execution is POSIX-only because the course runtime depends on sys/time.h.
if(UNIX)
  add_custom_command(
    OUTPUT "${GENERATED}/runtime.native.o"
    COMMAND "${CLANG_EXECUTABLE}" -std=c11 -c "${ROOT_DIR}/lib/sylib.c"
            -o "${GENERATED}/runtime.native.o"
    DEPENDS "${ROOT_DIR}/lib/sylib.c" "${ROOT_DIR}/lib/sylib.h"
    VERBATIM)
  add_custom_command(
    OUTPUT "${GENERATED}/source.native.o"
    COMMAND "${CLANG_EXECUTABLE}" -x c -include "${BUILTIN_HEADER}" -std=c11 -c "${SOURCE}"
            -o "${GENERATED}/source.native.o"
    DEPENDS "${SOURCE}" "${BUILTIN_HEADER}"
    VERBATIM)
  add_custom_command(
    OUTPUT "${GENERATED}/source.native" "${GENERATED}/ir.native"
    COMMAND "${CLANG_EXECUTABLE}" "${GENERATED}/source.native.o" "${GENERATED}/runtime.native.o"
            -o "${GENERATED}/source.native"
    COMMAND "${CLANG_EXECUTABLE}" "${HAND_IR}" "${GENERATED}/runtime.native.o"
            -o "${GENERATED}/ir.native"
    DEPENDS "${GENERATED}/source.native.o" "${GENERATED}/runtime.native.o" "${HAND_IR}"
    VERBATIM)
  add_custom_target(
    native_verify
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/verify_programs.py"
            --program "${GENERATED}/source.native"
            --program "${GENERATED}/ir.native"
    DEPENDS "${GENERATED}/source.native" "${GENERATED}/ir.native"
    COMMENT "Comparing source and LLVM IR behavior / 比较源码与 LLVM IR 行为"
    VERBATIM)
  add_test(NAME native_equivalence
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/verify_programs.py"
            --program "${GENERATED}/source.native"
            --program "${GENERATED}/ir.native")
  set_tests_properties(native_equivalence PROPERTIES REQUIRED_FILES "${GENERATED}/ir.native")
endif()

if(RISCV_GCC_EXECUTABLE)
  # 预编译归档的 libc 来源不可证明；从仓库源码按当前 Linux ABI 重建。
  # The prebuilt archive's libc provenance is unknown; rebuild from repository source for this Linux ABI.
  add_custom_command(
    OUTPUT "${GENERATED}/runtime.rv64.o"
    COMMAND "${RISCV_GCC_EXECUTABLE}" -march=rv64gc -mabi=lp64d -std=c11
            -c "${ROOT_DIR}/lib/sylib.c" -o "${GENERATED}/runtime.rv64.o"
    DEPENDS "${ROOT_DIR}/lib/sylib.c" "${ROOT_DIR}/lib/sylib.h"
    COMMENT "Rebuilding the SysY runtime for RV64 Linux / 为 RV64 Linux 重建 SysY 运行时"
    VERBATIM)
  foreach(form IN ITEMS source ir asm)
    set(input "${GENERATED}/compiler_tour.from-${form}.o")
    add_custom_command(
      OUTPUT "${GENERATED}/${form}.rv64"
      COMMAND "${RISCV_GCC_EXECUTABLE}" -march=rv64gc -mabi=lp64d -static -no-pie "${input}"
              "${GENERATED}/runtime.rv64.o" -o "${GENERATED}/${form}.rv64"
      DEPENDS "${input}" "${GENERATED}/runtime.rv64.o"
      COMMENT "Linking ${form} with the SysY RV64 runtime / 链接 ${form} 与 SysY RV64 运行时"
      VERBATIM)
  endforeach()
  add_custom_target(riscv_link
    DEPENDS "${GENERATED}/source.rv64" "${GENERATED}/ir.rv64" "${GENERATED}/asm.rv64")
  if(QEMU_RISCV64_EXECUTABLE)
    add_custom_target(
      riscv_verify
      COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/verify_programs.py"
              --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/source.rv64"
              --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/ir.rv64"
              --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/asm.rv64"
      DEPENDS riscv_link
      COMMENT "Executing all RV64GC forms with QEMU / 使用 QEMU 执行全部 RV64GC 表示"
      VERBATIM)
    add_test(NAME riscv_equivalence
      COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/verify_programs.py"
              --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/source.rv64"
              --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/ir.rv64"
              --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/asm.rv64")
    set_tests_properties(riscv_equivalence PROPERTIES REQUIRED_FILES "${GENERATED}/asm.rv64")
  endif()
endif()

add_custom_target(verify DEPENDS check_pipeline check_advanced)
if(TARGET native_verify)
  add_dependencies(verify native_verify)
endif()
if(TARGET riscv_verify)
  add_dependencies(verify riscv_verify)
elseif(TARGET riscv_link)
  add_dependencies(verify riscv_link)
endif()

message(STATUS "Clang: ${CLANG_EXECUTABLE}")
message(STATUS "RISC-V GCC: ${RISCV_GCC_EXECUTABLE}")
message(STATUS "QEMU RISC-V: ${QEMU_RISCV64_EXECUTABLE}")
