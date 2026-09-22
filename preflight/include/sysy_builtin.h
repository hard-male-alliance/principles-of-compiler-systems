#ifndef PREFLIGHT_SYSY_BUILTIN_H
#define PREFLIGHT_SYSY_BUILTIN_H

/**
 * SysY 示例所用的最小运行时契约。 / Minimal SysY runtime contract used by the example.
 *
 * 此头文件仅供宿主 C 前端分析，不属于 SysY 源程序。
 * This header is injected only for host-C frontend analysis and is not part of
 * the SysY source language.
 */
/** 读取一个十进制整数。 / Read one decimal integer. */
int getint(void);

/** 输出一个十进制整数且不附加换行。 / Print one decimal integer without a newline. */
void putint(int value);

/** 输出低字节对应的字符。 / Print the character represented by the low byte. */
void putch(int value);

#endif
