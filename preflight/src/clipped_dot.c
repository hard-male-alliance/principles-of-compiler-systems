#include "case_config.h"

/**
 * \brief 对两个整数数组的前缀计算逐项截断点积。 / Compute an element-wise clipped dot product over two prefixes.
 *
 * \param a 左输入数组；至少含 n 个元素。 / Left input array with at least n elements.
 * \param b 右输入数组；至少含 n 个元素。 / Right input array with at least n elements.
 * \param n 前缀长度；调用者保证 0 <= n <= VECTOR_LENGTH。 / Prefix length; caller guarantees the bounded range.
 * \param lo 每一项的闭区间下界。 / Inclusive lower bound for a term.
 * \param hi 每一项的闭区间上界。 / Inclusive upper bound for a term.
 * \return 采用 SysY i32 算术得到的累加值。 / Accumulated value using SysY i32 arithmetic.
 */
int clipped_dot(const int a[], const int b[], int n, int lo, int hi) {
  int acc = 0;
  int i = 0;
  while (i < n) {
    int term = a[i] * b[i];
    if (term < lo) {
      term = lo;
    } else if (term > hi) {
      term = hi;
    }
    acc = acc + term;
    i = i + 1;
  }
  return acc;
}

/**
 * \brief 读取并约束前缀长度，随后输出案例结果。 / Read and bound the prefix length, then print the case result.
 * \return 成功时返回 0。 / Zero on success.
 */
int main(void) {
  int a[VECTOR_LENGTH] = {-4, 1, 7, 3, 9, -2, 6, 5};
  int b[VECTOR_LENGTH] = {2, -3, 1, 4, -1, 5, 2, 3};
  int n = getint();
  if (n < 0) {
    n = 0;
  } else if (n > VECTOR_LENGTH) {
    n = VECTOR_LENGTH;
  }
  int result = clipped_dot(a, b, n, TERM_MIN, TERM_MAX);
  putint(result);
  putch(10);
  return 0;
}
