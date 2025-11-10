$$$$

This completes the proof. ■

**Theorem 7.4** For  $x \ge 1$ ,

$$\Delta(x) = \sum_{n \le x} (\log n - d(n) + 2\gamma) = O(x^{1/2}).$$

**Proof.** By Theorem 7.3 we have

$$\sum_{n \le x} d(n) = x \log x + (2\gamma - 1)x + O(x^{1/2}).$$

By Theorem 6.4 we have

$$\sum_{n \le x} \log n = x \log x - x + O(\log x).$$

Subtracting the first equation from the second, we obtain

$$\sum_{n \le x} (\log n - d(n) + 2\gamma) = O(x^{1/2}) - 2\gamma\{x\} + O(\log x) = O(x^{1/2}).$$

■

![](_page_0_Picture_11.jpeg)

An *ordered factorization* of the positive integer  $n$  into exactly  $\ell$  factors is an  $\ell$ -tuple  $(d_1, \dots, d_\ell)$  such that  $n = d_1 \cdots d_\ell$ . The divisor function  $d(n)$  counts the number of ordered factorizations of  $n$  into exactly two factors, since each factorization  $n = dd'$  is completely determined by the first factor  $d$ . For every positive integer  $\ell$ , we define the arithmetic function  $d_\ell(n)$  as the number of factorizations of  $n$  into exactly  $\ell$  factors. Then  $d_1(n) = 1$  and  $d_2(n) = d(n)$  for all  $n$ .