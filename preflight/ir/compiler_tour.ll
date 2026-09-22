; 等价的手写 LLVM IR（opaque pointers）。 / Equivalent handwritten LLVM IR (opaque pointers).
; 仅使用目标无关的 i32 语义，可由 Clang 同时降低到宿主机与 RV64GC。
; Only target-independent i32 semantics are used, allowing host and RV64GC lowering.

@ticks = global i32 0, align 4

declare i32 @getint()
declare void @putint(i32)
declare void @putch(i32)

define i32 @mark() {
entry:
  %old = load i32, ptr @ticks, align 4
  %new = add i32 %old, 1
  store i32 %new, ptr @ticks, align 4
  ret i32 1
}

define i32 @fib(i32 %n) {
entry:
  %base = icmp sle i32 %n, 1
  br i1 %base, label %return_n, label %recurse

return_n:
  ret i32 %n

recurse:
  %n1 = sub i32 %n, 1
  %left = call i32 @fib(i32 %n1)
  %n2 = sub i32 %n, 2
  %right = call i32 @fib(i32 %n2)
  %result = add i32 %left, %right
  ret i32 %result
}

define i32 @sum(ptr %values, i32 %length) {
entry:
  br label %loop

loop:
  %i = phi i32 [ 0, %entry ], [ %next_i, %body ]
  %total = phi i32 [ 0, %entry ], [ %next_total, %body ]
  %more = icmp slt i32 %i, %length
  br i1 %more, label %body, label %done

body:
  %slot = getelementptr i32, ptr %values, i32 %i
  %value = load i32, ptr %slot, align 4
  %next_total = add i32 %total, %value
  %next_i = add i32 %i, 1
  br label %loop

done:
  ret i32 %total
}

define i32 @main() {
entry:
  %values = alloca [8 x i32], align 16
  %input = call i32 @getint()
  %below = icmp slt i32 %input, 0
  %at_least_zero = select i1 %below, i32 0, i32 %input
  %above = icmp sgt i32 %at_least_zero, 8
  %n = select i1 %above, i32 8, i32 %at_least_zero
  %first = getelementptr [8 x i32], ptr %values, i32 0, i32 0
  store i32 0, ptr %first, align 4
  br label %fill_test

fill_test:
  %i = phi i32 [ 0, %entry ], [ %next_i, %fill_body ]
  %more = icmp slt i32 %i, %n
  br i1 %more, label %fill_body, label %short_lhs

fill_body:
  %square = mul i32 %i, %i
  %linear = add i32 %square, %i
  %value = add i32 %linear, 1
  %slot = getelementptr [8 x i32], ptr %values, i32 0, i32 %i
  store i32 %value, ptr %slot, align 4
  %next_i = add i32 %i, 1
  br label %fill_test

short_lhs:
  %large = icmp sgt i32 %n, 2
  br i1 %large, label %short_rhs, label %else

short_rhs:
  %marked = call i32 @mark()
  %truthy = icmp ne i32 %marked, 0
  br i1 %truthy, label %then, label %else

then:
  %old_then = load i32, ptr %first, align 4
  %fib_n = call i32 @fib(i32 %n)
  %new_then = add i32 %old_then, %fib_n
  store i32 %new_then, ptr %first, align 4
  br label %print

else:
  %old_else = load i32, ptr %first, align 4
  %new_else = add i32 %old_else, 7
  store i32 %new_else, ptr %first, align 4
  br label %print

print:
  %total = call i32 @sum(ptr %first, i32 %n)
  call void @putint(i32 %total)
  call void @putch(i32 10)
  %tick_count = load i32, ptr @ticks, align 4
  call void @putint(i32 %tick_count)
  call void @putch(i32 10)
  ret i32 0
}
