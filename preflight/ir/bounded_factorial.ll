; 边界化阶乘的手写 opaque-pointer LLVM IR。 / Handwritten opaque-pointer LLVM IR.
; 控制流刻意保留源码的三个函数边界。 / Control flow preserves the three source functions.

declare i32 @getint()
declare void @putint(i32)
declare void @putch(i32)

define i32 @clamp_input(i32 %value) {
entry:
  %negative = icmp slt i32 %value, 0
  br i1 %negative, label %zero, label %check_high
zero:
  ret i32 0
check_high:
  %too_large = icmp sgt i32 %value, 10
  %bounded = select i1 %too_large, i32 10, i32 %value
  ret i32 %bounded
}

define i32 @factorial(i32 %n) {
entry:
  br label %loop
loop:
  %factor = phi i32 [ 2, %entry ], [ %next_factor, %body ]
  %result = phi i32 [ 1, %entry ], [ %next_result, %body ]
  %continue = icmp sle i32 %factor, %n
  br i1 %continue, label %body, label %done
body:
  %next_result = mul i32 %result, %factor
  %next_factor = add i32 %factor, 1
  br label %loop
done:
  ret i32 %result
}

define i32 @main() {
entry:
  %input = call i32 @getint()
  %bounded = call i32 @clamp_input(i32 %input)
  %result = call i32 @factorial(i32 %bounded)
  call void @putint(i32 %result)
  call void @putch(i32 10)
  ret i32 0
}
