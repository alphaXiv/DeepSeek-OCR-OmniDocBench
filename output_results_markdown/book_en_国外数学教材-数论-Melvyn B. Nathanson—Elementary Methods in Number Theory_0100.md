**Proof.** This follows immediately from Theorem 3.3, since  $|(\mathbb{Z}/p\mathbb{Z})^\times| = p - 1$ .  $\square$ 

The following table lists the primitive roots for the first six primes.

| $p$ | $\varphi(p-1)$ | primitive roots |
|-----|----------------|-----------------|
| 2   | 1              | 1               |
| 3   | 1              | 2               |
| 5   | 2              | 2, 3            |
| 7   | 2              | 3, 5            |
| 11  | 4              | 2, 6, 7, 8      |
| 13  | 4              | 2, 6, 7, 11     |

Let  $p$  be a prime, and let  $g$  be a primitive root modulo  $p$ . If  $a$  is an integer not divisible by  $p$ , then there exists a unique integer  $k$  such that

$$a \equiv g^k \pmod{p}$$

and

$$k \in \{0, 1, \dots, p-2\}.$$

This integer  $k$  is called the *index* of  $a$  with respect to the primitive root  $g$ , and is denoted by

$$k = \operatorname{ind}_g(a).$$

If  $k_1$  and  $k_2$  are any integers such that  $k_1 \le k_2$  and

$$a \equiv g^{k_1} \equiv g^{k_2} \pmod{p},$$

then

$$g^{k_2 - k_1} \equiv 1 \pmod{p},$$

and so

$$k_1 \equiv k_2 \pmod{p-1}.$$

If  $a \equiv g^k \pmod{p}$  and  $b \equiv g^\ell \pmod{p}$ , then  $ab \equiv g^k g^\ell = g^{k+\ell} \pmod{p}$ , and so

$$\operatorname{ind}_g(ab) \equiv k + \ell \equiv \operatorname{ind}_g(a) + \operatorname{ind}_g(b) \pmod{p-1}.$$

The index map  $\operatorname{ind}_g$  is also called the *discrete logarithm* to the base  $g$  modulo  $p$ .

For example, 2 is a primitive root modulo 13. Here is a table of  $\operatorname{ind}_2(a)$  for  $a = 1, \dots, 12$ :

| $a$ | $\operatorname{ind}_2(a)$ | $a$ | $\operatorname{ind}_2(a)$ |
|-----|---------------------------|-----|---------------------------|
| 1   | 0                         | 7   | 11                        |
| 2   | 1                         | 8   | 3                         |
| 3   | 4                         | 9   | 8                         |
| 4   | 2                         | 10  | 10                        |
| 5   | 9                         | 11  | 7                         |
| 6   | 5                         | 12  | 6                         |