**B-5 First solution.** The answer is no. Suppose otherwise. For the condition to make sense,  $f$  must be differentiable. Since  $f$  is strictly increasing, we must have  $f'(x) \ge 0$  for all  $x$ . Also, the function  $f'(x)$  is strictly increasing: if  $y > x$  then  $f'(y) = f(f(y)) > f(f(x)) = f'(x)$ . In particular,  $f'(y) > 0$  for all  $y \in \mathbb{R}$ .

For any  $x_0 \ge -1$ , if  $f(x_0) = b$  and  $f'(x_0) = a > 0$ , then  $f'(x) > a$  for  $x > x_0$  and thus  $f(x) \ge a(x - x_0) + b$  for  $x \ge x_0$ . Then either  $b < x_0$  or  $a = f'(x_0) = f(f(x_0)) = f(b) \ge a(b - x_0) + b$ . In the latter case,  $b \le a(x_0 + 1)/(a + 1) \le x_0 + 1$ . We conclude in either case that  $f(x_0) \le x_0 + 1$  for all  $x_0 \ge -1$ .

It must then be the case that  $f(f(x)) = f'(x) \le 1$  for all  $x$ , since otherwise  $f(x) > x + 1$  for large  $x$ . Now by the above reasoning, if  $f(0) = b_0$  and  $f'(0) = a_0 > 0$ , then  $f(x) > a_0x + b_0$  for  $x > 0$ . Thus for  $x > \max\{0, -b_0/a_0\}$ , we have  $f(x) > 0$  and  $f(f(x)) > a_0x + b_0$ . But then  $f(f(x)) > 1$  for sufficiently large  $x$ , a contradiction.

**Second solution.** (Communicated by Catalin Zara.) Suppose such a function exists. Since  $f$  is strictly increasing and differentiable, so is  $f \circ f = f'$ . In particular,  $f$  is twice differentiable; also,  $f''(x) = f'(f(x))f'(x)$  is the product of two strictly increasing nonnegative functions, so it is also strictly increasing and nonnegative. In particular, we can choose  $\alpha > 0$  and  $M \in \mathbb{R}$  such that  $f''(x) > 4\alpha$  for all  $x \ge M$ . Then for all  $x \ge M$ ,

$$f(x) \ge f(M) + f'(M)(x - M) + 2\alpha(x - M)^2.$$

In particular, for some  $M' > M$ , we have  $f(x) \ge \alpha x^2$  for all  $x \ge M'$ .

Pick  $T > 0$  so that  $\alpha T^2 > M'$ . Then for  $x \ge T$ ,  $f(x) > M'$  and so  $f'(x) = f(f(x)) \ge \alpha f(x)^2$ . Now

$$\frac{1}{f(T)} - \frac{1}{f(2T)} = \int_T^{2T} \frac{f'(t)}{f(t)^2} dt \ge \int_T^{2T} \alpha dt;$$

however, as  $T \to \infty$ , the left side of this inequality tends to 0 while the right side tends to  $+\infty$ , a contradiction.

**Third solution.** (Communicated by Noam Elkies.) Since  $f$  is strictly increasing, for some  $y_0$ , we can define the inverse function  $g(y)$  of  $f$  for  $y \ge y_0$ . Then

 $x = g(f(x))$ , and we may differentiate to find that  $1 = g'(f(x))f'(x) = g'(f(x))f(f(x))$ . It follows that  $g'(y) = 1/f(y)$  for  $y \ge y_0$ ; since  $g$  takes arbitrarily large values, the integral  $\int_{y_0}^\infty dy/f(y)$  must diverge. One then gets a contradiction from any reasonable lower bound on  $f(y)$  for  $y$  large, e.g., the bound  $f(x) \ge \alpha x^2$  from the second solution. (One can also start with a linear lower bound  $f(x) \ge \beta x$ , then use the integral expression for  $g$  to deduce that  $g(x) \le \gamma \log x$ , which in turn forces  $f(x)$  to grow exponentially.)

**B-6** For any polynomial  $p(x)$ , let  $[p(x)]A$  denote the  $n \times n$  matrix obtained by replacing each entry  $A_{ij}$  of  $A$  by  $p(A_{ij})$ ; thus  $A^{[k]} = [x^k]A$ . Let  $P(x) = x^n + a_{n-1}x^{n-1} + \dots + a_0$  denote the characteristic polynomial of  $A$ . By the Cayley-Hamilton theorem,

$$\begin{aligned} 0 &= A \cdot P(A) \\ &= A^{n+1} + a_{n-1}A^n + \dots + a_0A \\ &= A^{[n+1]} + a_{n-1}A^{[n]} + \dots + a_0A^{[1]} \\ &= [xp(x)]A. \end{aligned}$$

Thus each entry of  $A$  is a root of the polynomial  $xp(x)$ .

Now suppose  $m \ge n + 1$ . Then

$$\begin{aligned} 0 &= [x^{m+1-n}P(x)]A \\ &= A^{[m+1]} + a_{n-1}A^{[m]} + \dots + a_0A^{[m+1-n]} \end{aligned}$$

since each entry of  $A$  is a root of  $x^{m+1-n}P(x)$ . On the other hand,

$$\begin{aligned} 0 &= A^{m+1-n} \cdot P(A) \\ &= A^{m+1} + a_{n-1}A^m + \dots + a_0A^{m+1-n}. \end{aligned}$$

Therefore if  $A^k = A^{[k]}$  for  $m + 1 - n \le k \le m$ , then  $A^{m+1} = A^{[m+1]}$ . The desired result follows by induction on  $m$ .

**Remark.** David Feldman points out that the result is best possible in the following sense: there exist examples of  $n \times n$  matrices  $A$  for which  $A^k = A^{[k]}$  for  $k = 1, \dots, n$  but  $A^{n+1} \ne A^{[n+1]}$ .