; 手写 opaque-pointer LLVM IR；语义与 clipped_dot.sy 一致。
; Hand-written opaque-pointer LLVM IR; semantics match clipped_dot.sy.
source_filename = "clipped_dot.handwritten.ll"
target datalayout = "e-m:e-p:64:64-i64:64-i128:128-n32:64-S128"
target triple = "riscv64-unknown-linux-gnu"

@a.init = private constant [8 x i32] [i32 -4, i32 1, i32 7, i32 3, i32 9, i32 -2, i32 6, i32 5], align 16
@b.init = private constant [8 x i32] [i32 2, i32 -3, i32 1, i32 4, i32 -1, i32 5, i32 2, i32 3], align 16

declare i32 @getint()
declare void @putint(i32)
declare void @putch(i32)
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg)

define i32 @clipped_dot(ptr readonly %a, ptr readonly %b, i32 %n, i32 %lo, i32 %hi) {
entry:
  br label %loop

loop:
  %i = phi i32 [ 0, %entry ], [ %i.next, %body ]
  %acc = phi i32 [ 0, %entry ], [ %acc.next, %body ]
  %more = icmp slt i32 %i, %n
  br i1 %more, label %body, label %exit

body:
  %index = sext i32 %i to i64
  %a.element = getelementptr inbounds i32, ptr %a, i64 %index
  %b.element = getelementptr inbounds i32, ptr %b, i64 %index
  %a.value = load i32, ptr %a.element, align 4
  %b.value = load i32, ptr %b.element, align 4
  %product = mul i32 %a.value, %b.value
  %below = icmp slt i32 %product, %lo
  %lowered = select i1 %below, i32 %lo, i32 %product
  %above = icmp sgt i32 %lowered, %hi
  %term = select i1 %above, i32 %hi, i32 %lowered
  %acc.next = add i32 %acc, %term
  %i.next = add i32 %i, 1
  br label %loop

exit:
  ret i32 %acc
}

define i32 @main() {
entry:
  %a = alloca [8 x i32], align 16
  %b = alloca [8 x i32], align 16
  call void @llvm.memcpy.p0.p0.i64(ptr align 16 %a, ptr align 16 @a.init, i64 32, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 16 %b, ptr align 16 @b.init, i64 32, i1 false)
  %raw = call i32 @getint()
  %negative = icmp slt i32 %raw, 0
  %nonnegative = select i1 %negative, i32 0, i32 %raw
  %too.large = icmp sgt i32 %nonnegative, 8
  %n = select i1 %too.large, i32 8, i32 %nonnegative
  %result = call i32 @clipped_dot(ptr %a, ptr %b, i32 %n, i32 -8, i32 12)
  call void @putint(i32 %result)
  call void @putch(i32 10)
  ret i32 0
}
