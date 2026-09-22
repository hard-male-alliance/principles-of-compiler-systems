cmake_minimum_required(VERSION 3.25)

# 本工程显式编排编译阶段，避免 CMake 隐式选择宿主 ABI。
# This project explicitly orchestrates compiler stages instead of selecting a host ABI.
project(bounded_factorial_preflight LANGUAGES NONE)

include(CTest)
find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)
find_program(CLANG_EXECUTABLE NAMES clang REQUIRED)
find_program(LLVM_READOBJ_EXECUTABLE NAMES llvm-readobj llvm-readobj-22 llvm-readobj-19 llvm-readobj-18 REQUIRED)
find_program(LLVM_OBJDUMP_EXECUTABLE NAMES llvm-objdump llvm-objdump-22 llvm-objdump-19 llvm-objdump-18 REQUIRED)
find_program(RISCV_GCC_EXECUTABLE NAMES riscv64-linux-gnu-gcc)
find_program(QEMU_RISCV64_EXECUTABLE NAMES qemu-riscv64)

set(ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/..")
set(C_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/src/bounded_factorial.c")
set(SYSY_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/src/bounded_factorial.sy")
set(BUILTIN_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/include/sysy_builtin.h")
set(HAND_IR "${CMAKE_CURRENT_SOURCE_DIR}/ir/bounded_factorial.ll")
set(HAND_ASM "${CMAKE_CURRENT_SOURCE_DIR}/asm/bounded_factorial_rv64gc.s")
set(CAPTURE "${CMAKE_CURRENT_SOURCE_DIR}/scripts/capture.py")
set(CHECK "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_artifacts.py")
set(VERIFY_PROGRAMS "${CMAKE_CURRENT_SOURCE_DIR}/scripts/verify_programs.py")
set(GENERATED "${CMAKE_CURRENT_BINARY_DIR}/generated")
set(RISCV_FLAGS --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d)
file(MAKE_DIRECTORY "${GENERATED}")

# 前端边界：同一 C 翻译单元的预处理文本、词法 token 与 AST。
# Frontend boundary: preprocessed text, lexical tokens, and AST from one C translation unit.
add_custom_command(
  OUTPUT "${GENERATED}/bounded_factorial.i"
  COMMAND "${CLANG_EXECUTABLE}" -E -std=c11 "${C_SOURCE}" -o "${GENERATED}/bounded_factorial.i"
  DEPENDS "${C_SOURCE}"
  COMMENT "Preprocessing bounded factorial / 预处理边界化阶乘"
  VERBATIM)
add_custom_command(
  OUTPUT "${GENERATED}/bounded_factorial.tokens.txt"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --stream stderr
          --output "${GENERATED}/bounded_factorial.tokens.txt" --
          "${CLANG_EXECUTABLE}" -std=c11 -fsyntax-only -Xclang -dump-tokens "${C_SOURCE}"
  DEPENDS "${C_SOURCE}" "${CAPTURE}"
  COMMENT "Dumping lexical tokens / 导出词法 token"
  VERBATIM)
add_custom_command(
  OUTPUT "${GENERATED}/bounded_factorial.ast.json"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}"
          --output "${GENERATED}/bounded_factorial.ast.json" --
          "${CLANG_EXECUTABLE}" -std=c11 -fsyntax-only -Xclang -ast-dump=json "${C_SOURCE}"
  DEPENDS "${C_SOURCE}" "${CAPTURE}"
  COMMENT "Dumping Clang AST / 导出 Clang AST"
  VERBATIM)

# 中端与后端：固定 C 源码，唯一变化是优化级别。
# Middle/backend: keep the C source fixed and vary only the optimization level.
foreach(level IN ITEMS O0 O2)
  add_custom_command(
    OUTPUT "${GENERATED}/bounded_factorial.${level}.ll"
    COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -std=c11 -S -emit-llvm -${level} "${C_SOURCE}"
            -o "${GENERATED}/bounded_factorial.${level}.ll"
    DEPENDS "${C_SOURCE}"
    COMMENT "Emitting ${level} LLVM IR / 生成 ${level} LLVM IR"
    VERBATIM)
  add_custom_command(
    OUTPUT "${GENERATED}/bounded_factorial.${level}.s"
    COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -std=c11 -S -${level} "${C_SOURCE}"
            -o "${GENERATED}/bounded_factorial.${level}.s"
    DEPENDS "${C_SOURCE}"
    COMMENT "Emitting ${level} RV64GC assembly / 生成 ${level} RV64GC 汇编"
    VERBATIM)
endforeach()

# 四种等价表示分别形成 RV64 ELF 可重定位对象。
# Four equivalent representations independently form RV64 ELF relocatable objects.
add_custom_command(
  OUTPUT "${GENERATED}/c.rv64.o"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -std=c11 -O0 -c "${C_SOURCE}" -o "${GENERATED}/c.rv64.o"
  DEPENDS "${C_SOURCE}" VERBATIM)
add_custom_command(
  OUTPUT "${GENERATED}/sysy.rv64.o"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -x c -include "${BUILTIN_HEADER}" -O0 -c
          "${SYSY_SOURCE}" -o "${GENERATED}/sysy.rv64.o"
  DEPENDS "${SYSY_SOURCE}" "${BUILTIN_HEADER}" VERBATIM)
add_custom_command(
  OUTPUT "${GENERATED}/ir.rv64.o"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -c "${HAND_IR}" -o "${GENERATED}/ir.rv64.o"
  DEPENDS "${HAND_IR}" VERBATIM)
add_custom_command(
  OUTPUT "${GENERATED}/asm.rv64.o"
  COMMAND "${CLANG_EXECUTABLE}" ${RISCV_FLAGS} -c "${HAND_ASM}" -o "${GENERATED}/asm.rv64.o"
  DEPENDS "${HAND_ASM}" VERBATIM)

# 对象文件不是“机器码黑盒”：保存头部、节、符号、重定位与反汇编证据。
# Object files are not machine-code black boxes: preserve headers, sections, symbols,
# relocations, and disassembly as inspectable evidence.
add_custom_command(
  OUTPUT "${GENERATED}/c.object.txt" "${GENERATED}/c.symbols.txt"
         "${GENERATED}/c.relocations.txt" "${GENERATED}/c.disassembly.txt"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/c.object.txt" --
          "${LLVM_READOBJ_EXECUTABLE}" --file-headers --sections "${GENERATED}/c.rv64.o"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/c.symbols.txt" --
          "${LLVM_READOBJ_EXECUTABLE}" --symbols "${GENERATED}/c.rv64.o"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/c.relocations.txt" --
          "${LLVM_READOBJ_EXECUTABLE}" --relocations "${GENERATED}/c.rv64.o"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/c.disassembly.txt" --
          "${LLVM_OBJDUMP_EXECUTABLE}" --disassemble --symbolize-operands "${GENERATED}/c.rv64.o"
  DEPENDS "${GENERATED}/c.rv64.o" "${CAPTURE}"
  COMMENT "Inspecting RV64 object structure / 检查 RV64 对象结构"
  VERBATIM)

# 作者手写汇编的产物单独留证，避免用 C 后端生成物代替汇编器边界。
# Preserve the handwritten assembly output separately instead of using a C-backend
# object as a proxy for the assembler boundary.
add_custom_command(
  OUTPUT "${GENERATED}/asm.object.txt" "${GENERATED}/asm.symbols.txt"
         "${GENERATED}/asm.relocations.txt" "${GENERATED}/asm.disassembly.txt"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/asm.object.txt" --
          "${LLVM_READOBJ_EXECUTABLE}" --file-headers --sections "${GENERATED}/asm.rv64.o"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/asm.symbols.txt" --
          "${LLVM_READOBJ_EXECUTABLE}" --symbols "${GENERATED}/asm.rv64.o"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/asm.relocations.txt" --
          "${LLVM_READOBJ_EXECUTABLE}" --relocations "${GENERATED}/asm.rv64.o"
  COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/asm.disassembly.txt" --
          "${LLVM_OBJDUMP_EXECUTABLE}" --disassemble --symbolize-operands "${GENERATED}/asm.rv64.o"
  DEPENDS "${GENERATED}/asm.rv64.o" "${CAPTURE}"
  COMMENT "Inspecting handwritten-assembly RV64 object / 检查手写汇编的 RV64 对象"
  VERBATIM)

set(PIPELINE_OUTPUTS
  "${GENERATED}/bounded_factorial.i"
  "${GENERATED}/bounded_factorial.tokens.txt"
  "${GENERATED}/bounded_factorial.ast.json"
  "${GENERATED}/bounded_factorial.O0.ll" "${GENERATED}/bounded_factorial.O2.ll"
  "${GENERATED}/bounded_factorial.O0.s" "${GENERATED}/bounded_factorial.O2.s"
  "${GENERATED}/c.rv64.o" "${GENERATED}/sysy.rv64.o"
  "${GENERATED}/ir.rv64.o" "${GENERATED}/asm.rv64.o"
  "${GENERATED}/c.object.txt" "${GENERATED}/c.symbols.txt"
  "${GENERATED}/c.relocations.txt" "${GENERATED}/c.disassembly.txt"
  "${GENERATED}/asm.object.txt" "${GENERATED}/asm.symbols.txt"
  "${GENERATED}/asm.relocations.txt" "${GENERATED}/asm.disassembly.txt")
add_custom_target(pipeline DEPENDS ${PIPELINE_OUTPUTS})

set(CHECK_ARGUMENTS
  --preprocessed "${GENERATED}/bounded_factorial.i"
  --tokens "${GENERATED}/bounded_factorial.tokens.txt"
  --ast "${GENERATED}/bounded_factorial.ast.json"
  --llvm-o0 "${GENERATED}/bounded_factorial.O0.ll"
  --llvm-o2 "${GENERATED}/bounded_factorial.O2.ll"
  --assembly-o0 "${GENERATED}/bounded_factorial.O0.s"
  --assembly-o2 "${GENERATED}/bounded_factorial.O2.s"
  --symbols "${GENERATED}/c.symbols.txt"
  --relocations "${GENERATED}/c.relocations.txt"
  --disassembly "${GENERATED}/c.disassembly.txt"
  --asm-object-info "${GENERATED}/asm.object.txt"
  --asm-symbols "${GENERATED}/asm.symbols.txt"
  --asm-relocations "${GENERATED}/asm.relocations.txt"
  --asm-disassembly "${GENERATED}/asm.disassembly.txt"
  --object "${GENERATED}/c.rv64.o" --object "${GENERATED}/sysy.rv64.o"
  --object "${GENERATED}/ir.rv64.o" --object "${GENERATED}/asm.rv64.o")
add_custom_target(check_pipeline
  COMMAND "${Python3_EXECUTABLE}" "${CHECK}" ${CHECK_ARGUMENTS}
  DEPENDS pipeline "${CHECK}"
  COMMENT "Checking compiler-stage evidence / 检查编译阶段证据"
  VERBATIM)

set(METRIC_ARGUMENTS
  --llvm-o0 "${GENERATED}/bounded_factorial.O0.ll"
  --llvm-o2 "${GENERATED}/bounded_factorial.O2.ll"
  --assembly-o0 "${GENERATED}/bounded_factorial.O0.s"
  --assembly-o2 "${GENERATED}/bounded_factorial.O2.s")
add_custom_target(optimization_metrics
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/optimization_metrics.py" ${METRIC_ARGUMENTS}
  DEPENDS pipeline "${CMAKE_CURRENT_SOURCE_DIR}/scripts/optimization_metrics.py"
  COMMENT "Reporting O0/O2 structural metrics / 报告 O0/O2 结构指标"
  VERBATIM)

add_custom_target(check_advanced
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_advanced.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/advanced/add.mlir"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/advanced/add.mlir"
          "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_advanced.py"
  COMMENT "Checking outlook material / 检查展望材料"
  VERBATIM)

add_test(NAME pipeline_artifacts COMMAND "${Python3_EXECUTABLE}" "${CHECK}" ${CHECK_ARGUMENTS})
set_tests_properties(pipeline_artifacts PROPERTIES REQUIRED_FILES "${GENERATED}/asm.rv64.o")
add_test(NAME optimization_metrics
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/optimization_metrics.py" ${METRIC_ARGUMENTS})
set_tests_properties(optimization_metrics PROPERTIES REQUIRED_FILES "${GENERATED}/bounded_factorial.O2.s")
add_test(NAME outlook_structure COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_advanced.py" "${CMAKE_CURRENT_SOURCE_DIR}/advanced/add.mlir")

# 本机执行负责快速验证 C、SysY 与目标无关 IR；课程 runtime 只作为链接依赖。
# Native execution quickly validates C, SysY, and target-independent IR; the course
# runtime is merely a link dependency.
if(UNIX)
  add_custom_command(
    OUTPUT "${GENERATED}/runtime.native.o"
    COMMAND "${CLANG_EXECUTABLE}" -std=c11 -c "${ROOT_DIR}/lib/sylib.c" -o "${GENERATED}/runtime.native.o"
    DEPENDS "${ROOT_DIR}/lib/sylib.c" "${ROOT_DIR}/lib/sylib.h" VERBATIM)
  add_custom_command(
    OUTPUT "${GENERATED}/c.native.o" "${GENERATED}/sysy.native.o" "${GENERATED}/ir.native.o"
    COMMAND "${CLANG_EXECUTABLE}" -std=c11 -c "${C_SOURCE}" -o "${GENERATED}/c.native.o"
    COMMAND "${CLANG_EXECUTABLE}" -x c -include "${BUILTIN_HEADER}" -c "${SYSY_SOURCE}" -o "${GENERATED}/sysy.native.o"
    COMMAND "${CLANG_EXECUTABLE}" -c "${HAND_IR}" -o "${GENERATED}/ir.native.o"
    DEPENDS "${C_SOURCE}" "${SYSY_SOURCE}" "${BUILTIN_HEADER}" "${HAND_IR}" VERBATIM)
  foreach(form IN ITEMS c sysy ir)
    add_custom_command(
      OUTPUT "${GENERATED}/${form}.native"
      COMMAND "${CLANG_EXECUTABLE}" "${GENERATED}/${form}.native.o" "${GENERATED}/runtime.native.o"
              -o "${GENERATED}/${form}.native"
      DEPENDS "${GENERATED}/${form}.native.o" "${GENERATED}/runtime.native.o" VERBATIM)
  endforeach()
  add_custom_target(native_verify
    COMMAND "${Python3_EXECUTABLE}" "${VERIFY_PROGRAMS}"
            --program "${GENERATED}/c.native" --program "${GENERATED}/sysy.native"
            --program "${GENERATED}/ir.native"
    DEPENDS "${GENERATED}/c.native" "${GENERATED}/sysy.native" "${GENERATED}/ir.native"
    COMMENT "Running shared native vectors / 运行本机共享测试向量" VERBATIM)
  add_test(NAME native_equivalence COMMAND "${Python3_EXECUTABLE}" "${VERIFY_PROGRAMS}"
    --program "${GENERATED}/c.native" --program "${GENERATED}/sysy.native" --program "${GENERATED}/ir.native")
  set_tests_properties(native_equivalence PROPERTIES REQUIRED_FILES "${GENERATED}/ir.native")
endif()

# GNU cross driver supplies the Linux startup objects, libc, and static linker inputs.
# GNU 交叉驱动提供 Linux 启动对象、libc 与静态链接输入。
if(RISCV_GCC_EXECUTABLE)
  add_custom_command(
    OUTPUT "${GENERATED}/runtime.rv64.o"
    COMMAND "${RISCV_GCC_EXECUTABLE}" -march=rv64gc -mabi=lp64d -std=c11 -c
            "${ROOT_DIR}/lib/sylib.c" -o "${GENERATED}/runtime.rv64.o"
    DEPENDS "${ROOT_DIR}/lib/sylib.c" "${ROOT_DIR}/lib/sylib.h" VERBATIM)
  foreach(form IN ITEMS c sysy ir asm)
    add_custom_command(
      OUTPUT "${GENERATED}/${form}.rv64"
      COMMAND "${RISCV_GCC_EXECUTABLE}" -march=rv64gc -mabi=lp64d -static -no-pie
              "${GENERATED}/${form}.rv64.o" "${GENERATED}/runtime.rv64.o" -o "${GENERATED}/${form}.rv64"
      DEPENDS "${GENERATED}/${form}.rv64.o" "${GENERATED}/runtime.rv64.o" VERBATIM)
  endforeach()
  # 链接后证据明确区分 ET_EXEC/程序头与上游 ET_REL 对象。
  # Post-link evidence distinguishes the executable/program headers from ET_REL inputs.
  add_custom_command(
    OUTPUT "${GENERATED}/asm.executable.txt"
    COMMAND "${Python3_EXECUTABLE}" "${CAPTURE}" --output "${GENERATED}/asm.executable.txt" --
            "${LLVM_READOBJ_EXECUTABLE}" --file-headers --program-headers --symbols
            "${GENERATED}/asm.rv64"
    DEPENDS "${GENERATED}/asm.rv64" "${CAPTURE}"
    COMMENT "Inspecting linked handwritten-assembly executable / 检查手写汇编链接结果"
    VERBATIM)
  add_custom_target(riscv_link DEPENDS "${GENERATED}/c.rv64" "${GENERATED}/sysy.rv64"
    "${GENERATED}/ir.rv64" "${GENERATED}/asm.rv64" "${GENERATED}/asm.executable.txt")
  if(QEMU_RISCV64_EXECUTABLE)
    add_custom_target(riscv_verify
      COMMAND "${Python3_EXECUTABLE}" "${VERIFY_PROGRAMS}"
        --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/c.rv64"
        --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/sysy.rv64"
        --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/ir.rv64"
        --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/asm.rv64"
      DEPENDS riscv_link COMMENT "Running shared RV64/QEMU vectors / 运行 RV64/QEMU 共享向量" VERBATIM)
    add_test(NAME riscv_equivalence COMMAND "${Python3_EXECUTABLE}" "${VERIFY_PROGRAMS}"
      --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/c.rv64"
      --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/sysy.rv64"
      --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/ir.rv64"
      --program "${QEMU_RISCV64_EXECUTABLE}" "${GENERATED}/asm.rv64")
    set_tests_properties(riscv_equivalence PROPERTIES REQUIRED_FILES "${GENERATED}/asm.rv64")
  endif()
endif()

add_custom_target(verify DEPENDS check_pipeline check_advanced optimization_metrics)
if(TARGET native_verify)
  add_dependencies(verify native_verify)
endif()
if(TARGET riscv_verify)
  add_dependencies(verify riscv_verify)
elseif(TARGET riscv_link)
  add_dependencies(verify riscv_link)
endif()

message(STATUS "Clang: ${CLANG_EXECUTABLE}")
message(STATUS "LLVM readobj: ${LLVM_READOBJ_EXECUTABLE}")
message(STATUS "LLVM objdump: ${LLVM_OBJDUMP_EXECUTABLE}")
message(STATUS "RISC-V GCC: ${RISCV_GCC_EXECUTABLE}")
message(STATUS "QEMU RISC-V: ${QEMU_RISCV64_EXECUTABLE}")
