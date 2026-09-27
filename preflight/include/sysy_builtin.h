#ifndef PREFLIGHT_SYSY_BUILTIN_H
#define PREFLIGHT_SYSY_BUILTIN_H

/** \file
 *  \brief 仅供通用 C 前端解析 SysY 内建函数的声明。 / Declarations only, for parsing SysY built-ins with a generic C front end.
 */

/** 读取一个 SysY 整数。 / Read one SysY integer. */
int getint(void);
/** 输出一个 SysY 整数。 / Emit one SysY integer. */
void putint(int value);
/** 输出一个字符码。 / Emit one character code. */
void putch(int value);

#endif
