// AscendNPU IR 官方 VecAdd 快速入门的最小内核。
// Minimal kernel from the official AscendNPU IR VecAdd quick start.
// 本文件仅作静态方言结构研究；仓库 CI 不具备 CANN 或昇腾 NPU。
// This file is for static dialect study only; repository CI has no CANN or Ascend NPU.
func.func @add(
    %arg0: memref<16xi16, #hivm.address_space<gm>>,
    %arg1: memref<16xi16, #hivm.address_space<gm>>,
    %arg2: memref<16xi16, #hivm.address_space<gm>>)
    attributes {hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>} {
  %lhs = memref.alloc() : memref<16xi16, #hivm.address_space<ub>>
  hivm.hir.load
      ins(%arg0 : memref<16xi16, #hivm.address_space<gm>>)
      outs(%lhs : memref<16xi16, #hivm.address_space<ub>>)
  %rhs = memref.alloc() : memref<16xi16, #hivm.address_space<ub>>
  hivm.hir.load
      ins(%arg1 : memref<16xi16, #hivm.address_space<gm>>)
      outs(%rhs : memref<16xi16, #hivm.address_space<ub>>)
  %result = memref.alloc() : memref<16xi16, #hivm.address_space<ub>>
  hivm.hir.vadd
      ins(%lhs, %rhs : memref<16xi16, #hivm.address_space<ub>>,
                        memref<16xi16, #hivm.address_space<ub>>)
      outs(%result : memref<16xi16, #hivm.address_space<ub>>)
  hivm.hir.store
      ins(%result : memref<16xi16, #hivm.address_space<ub>>)
      outs(%arg2 : memref<16xi16, #hivm.address_space<gm>>)
  return
}
