#ifndef PREFLIGHT_CASE_CONFIG_H
#define PREFLIGHT_CASE_CONFIG_H

/** \file
 *  \brief 截断点积案例的可观察编译期契约。 / Observable compile-time contract for the clipped-dot case.
 */

/// 向量中可访问的元素数。 / Number of addressable vector elements.
#define VECTOR_LENGTH 8
/// 单项贡献的闭区间下界。 / Inclusive lower bound for each contribution.
#define TERM_MIN (-8)
/// 单项贡献的闭区间上界。 / Inclusive upper bound for each contribution.
#define TERM_MAX 12

/** 从 SysY 运行时读取一个整数。 / Read one integer through the SysY runtime. */
int getint(void);
/** 向 SysY 运行时写入一个十进制整数。 / Write one decimal integer through the SysY runtime. */
void putint(int value);
/** 向 SysY 运行时写入一个字符码。 / Write one character code through the SysY runtime. */
void putch(int value);

#endif
