    # 手写 RV64GC / LP64D 汇编；所有调用边界保持 16 字节栈对齐。
    # Hand-written RV64GC / LP64D assembly; every call boundary keeps 16-byte stack alignment.
    .text
    .attribute arch, "rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_zicsr2p0"
    .globl clipped_dot
    .type clipped_dot, @function
clipped_dot:
    li      t0, 0
    li      t1, 0
.Lloop:
    bge     t1, a2, .Ldone
    slli    t2, t1, 2
    add     t3, a0, t2
    lw      t4, 0(t3)
    add     t3, a1, t2
    lw      t5, 0(t3)
    mulw    t4, t4, t5
    blt     t4, a3, .Llower
    blt     a4, t4, .Lupper
.Laccumulate:
    addw    t0, t0, t4
    addiw   t1, t1, 1
    j       .Lloop
.Llower:
    mv      t4, a3
    j       .Laccumulate
.Lupper:
    mv      t4, a4
    j       .Laccumulate
.Ldone:
    mv      a0, t0
    ret
    .size clipped_dot, .-clipped_dot

    .globl main
    .type main, @function
main:
    addi    sp, sp, -80
    sd      ra, 72(sp)

    li t0, -4
    sw t0, 0(sp)
    li t0, 1
    sw t0, 4(sp)
    li t0, 7
    sw t0, 8(sp)
    li t0, 3
    sw t0, 12(sp)
    li t0, 9
    sw t0, 16(sp)
    li t0, -2
    sw t0, 20(sp)
    li t0, 6
    sw t0, 24(sp)
    li t0, 5
    sw t0, 28(sp)

    li t0, 2
    sw t0, 32(sp)
    li t0, -3
    sw t0, 36(sp)
    li t0, 1
    sw t0, 40(sp)
    li t0, 4
    sw t0, 44(sp)
    li t0, -1
    sw t0, 48(sp)
    li t0, 5
    sw t0, 52(sp)
    li t0, 2
    sw t0, 56(sp)
    li t0, 3
    sw t0, 60(sp)

    call    getint
    bge     a0, zero, .Lcheck_high
    li      a2, 0
    j       .Lcall_kernel
.Lcheck_high:
    li      t0, 8
    ble     a0, t0, .Luse_input
    li      a2, 8
    j       .Lcall_kernel
.Luse_input:
    mv      a2, a0
.Lcall_kernel:
    mv      a0, sp
    addi    a1, sp, 32
    li      a3, -8
    li      a4, 12
    call    clipped_dot
    call    putint
    li      a0, 10
    call    putch

    li      a0, 0
    ld      ra, 72(sp)
    addi    sp, sp, 80
    ret
    .size main, .-main

    .section .note.GNU-stack,"",@progbits
