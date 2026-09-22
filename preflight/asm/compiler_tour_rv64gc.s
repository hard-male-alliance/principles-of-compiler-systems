/* 等价的 RISC-V RV64GC Linux 汇编。 / Equivalent RISC-V RV64GC Linux assembly. */
    .option arch, rv64gc
    .text

    .globl mark
    .type mark, @function
mark:
    lui     t0, %hi(ticks)
    lw      t1, %lo(ticks)(t0)
    addiw   t1, t1, 1
    sw      t1, %lo(ticks)(t0)
    li      a0, 1
    ret
    .size mark, .-mark

    .globl fib
    .type fib, @function
fib:
    addi    sp, sp, -32
    sd      ra, 24(sp)
    sd      s0, 16(sp)
    sd      s1, 8(sp)
    mv      s0, a0
    li      t0, 1
    ble     a0, t0, .Lfib_done
    addiw   a0, s0, -1
    call    fib
    mv      s1, a0
    addiw   a0, s0, -2
    call    fib
    addw    a0, s1, a0
.Lfib_done:
    ld      s1, 8(sp)
    ld      s0, 16(sp)
    ld      ra, 24(sp)
    addi    sp, sp, 32
    ret
    .size fib, .-fib

    .globl sum
    .type sum, @function
sum:
    li      t0, 0
    li      t1, 0
.Lsum_loop:
    bge     t0, a1, .Lsum_done
    slli    t2, t0, 2
    add     t2, a0, t2
    lw      t3, 0(t2)
    addw    t1, t1, t3
    addiw   t0, t0, 1
    j       .Lsum_loop
.Lsum_done:
    mv      a0, t1
    ret
    .size sum, .-sum

    .globl main
    .type main, @function
main:
    addi    sp, sp, -80
    sd      ra, 72(sp)
    sd      s0, 64(sp)
    sd      s1, 56(sp)
    sd      s2, 48(sp)
    call    getint
    mv      s0, a0
    bgez    s0, .Lclamp_high
    li      s0, 0
.Lclamp_high:
    li      t0, 8
    ble     s0, t0, .Lclamped
    li      s0, 8
.Lclamped:
    sw      zero, 0(sp)
    li      s1, 0
.Lfill_test:
    bge     s1, s0, .Lshort_lhs
    mulw    t0, s1, s1
    addw    t0, t0, s1
    addiw   t0, t0, 1
    slli    t1, s1, 2
    add     t1, sp, t1
    sw      t0, 0(t1)
    addiw   s1, s1, 1
    j       .Lfill_test
.Lshort_lhs:
    li      t0, 2
    ble     s0, t0, .Lelse
    call    mark
    beqz    a0, .Lelse
    lw      s1, 0(sp)
    mv      a0, s0
    call    fib
    addw    s1, s1, a0
    sw      s1, 0(sp)
    j       .Lprint
.Lelse:
    lw      t0, 0(sp)
    addiw   t0, t0, 7
    sw      t0, 0(sp)
.Lprint:
    mv      a0, sp
    mv      a1, s0
    call    sum
    mv      s2, a0
    call    putint
    li      a0, 10
    call    putch
    lui     t0, %hi(ticks)
    lw      a0, %lo(ticks)(t0)
    call    putint
    li      a0, 10
    call    putch
    li      a0, 0
    ld      s2, 48(sp)
    ld      s1, 56(sp)
    ld      s0, 64(sp)
    ld      ra, 72(sp)
    addi    sp, sp, 80
    ret
    .size main, .-main

    .bss
    .balign 4
    .globl ticks
    .type ticks, @object
    .size ticks, 4
ticks:
    .zero 4

    .section .note.GNU-stack,"",@progbits
