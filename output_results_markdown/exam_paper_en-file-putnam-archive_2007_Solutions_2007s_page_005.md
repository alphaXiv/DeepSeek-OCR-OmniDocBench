by comparing the sum to an integral. This gives

$$n^{n^2/2 - C_1 n} e^{-n^2/4} \le 1^{1+c} 2^{2+c} \dots n^{n+c} \\ \le n^{n^2/2 + C_2 n} e^{-n^2/4}.$$

We now interpret  $f(n)$  as counting the number of  $n$ -tuples  $(a_1, \dots, a_n)$  of nonnegative integers such that

$$a_1 1! + \dots + a_n n! = n!.$$

For an upper bound on  $f(n)$ , we use the inequalities  $0 \le a_i \le n!/i!$  to deduce that there are at most  $n!/i! + 1 \le 2(n!/i!)$  choices for  $a_i$ . Hence

$$f(n) \le 2^n \frac{n!}{1!} \dots \frac{n!}{n!} \\ = 2^n 2^1 3^2 \dots n^{n-1} \\ \le n^{n^2/2 + C_3 n} e^{-n^2/4}.$$

For a lower bound on  $f(n)$ , we note that if  $0 \le a_i < (n-1)!/i!$  for  $i = 2, \dots, n-1$  and  $a_n = 0$ , then  $0 \le a_2 2! + \dots + a_n n! \le n!$ , so there is a unique choice of  $a_1$  to complete this to a solution of  $a_1 1! + \dots + a_n n! = n!$ . Hence

$$f(n) \ge \frac{(n-1)!}{2!} \dots \frac{(n-1)!}{(n-1)!} \\ = 3^1 4^2 \dots (n-1)^{n-3} \\ \ge n^{n^2/2 + C_4 n} e^{-n^2/4}.$$