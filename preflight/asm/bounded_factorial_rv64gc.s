/* 边界化阶乘的 RV64GC Linux 汇编。 / RV64GC Linux assembly for bounded factorial. */
    .option arch, rv64gc
    .text

    .globl clamp_input
    .type clamp_input, @function
clamp_input:
    bgez    a0, .Lcheck_high
    li      a0, 0
    ret
.Lcheck_high:
    li      t0, 10
    ble     a0, t0, .Lclamp_done
    li      a0, 10
.Lclamp_done:
    ret
    .size clamp_input, .-clamp_input

    .globl factorial
    .type factorial, @function
factorial:
    li      t0, 1
    li      t1, 2
.Lfactorial_test:
    bgt     t1, a0, .Lfactorial_done
    mulw    t0, t0, t1
    addiw   t1, t1, 1
    j       .Lfactorial_test
.Lfactorial_done:
    mv      a0, t0
    ret
    .size factorial, .-factorial

    .globl main
    .type main, @function
main:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    call    getint
    call    clamp_input
    call    factorial
    call    putint
    li      a0, 10
    call    putch
    li      a0, 0
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret
    .size main, .-main

    .section .note.GNU-stack,"",@progbits
