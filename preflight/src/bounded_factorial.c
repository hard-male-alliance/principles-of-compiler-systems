/**
 * @file bounded_factorial.c
 * @brief 贯穿编译阶段的边界化阶乘实例。 / Bounded-factorial case study spanning compiler stages.
 *
 * 输入先归一化到 [0, 10]，随后由独立函数迭代计算阶乘。宏与外部函数声明
 * 有意保留在源码中，使预处理结果能够直接展示两者的处理边界。
 * Input is normalized to [0, 10] before an independent iterative factorial
 * function runs. The macro and external declarations intentionally expose the
 * preprocessing boundary.
 */

#define FACTORIAL_LIMIT 10

int getint(void);
void putint(int value);
void putch(int value);

/** 将任意输入限制到阶乘的安全演示区间。 / Clamp input to the safe demonstration range. */
int clamp_input(int value) {
  if (value < 0) {
    return 0;
  }
  if (value > FACTORIAL_LIMIT) {
    return FACTORIAL_LIMIT;
  }
  return value;
}

/** 迭代计算 n!；调用者保证 0 <= n <= 10。 / Iteratively compute n! for 0 <= n <= 10. */
int factorial(int n) {
  int result = 1;
  int factor = 2;
  while (factor <= n) {
    result = result * factor;
    factor = factor + 1;
  }
  return result;
}

/** 读取一个整数并输出边界化阶乘。 / Read one integer and print its bounded factorial. */
int main(void) {
  int input = getint();
  int bounded = clamp_input(input);
  int result = factorial(bounded);
  putint(result);
  putch(10);
  return 0;
}
