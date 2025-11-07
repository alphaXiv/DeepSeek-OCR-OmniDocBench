as desired.

**Remark:** The use of Cesaro's lemma above is the special case  $b_n = n$  of the *Cesaro-Stolz theorem*: if  $a_n, b_n$  are sequences such that  $b_n$  is positive, strictly increasing, and unbounded, and

$$\lim_{n \to \infty} \frac{a_{n+1} - a_n}{b_{n+1} - b_n} = L,$$

then

$$\lim_{n \to \infty} \frac{a_n}{b_n} = L.$$

**Second solution:** In this solution, rather than applying Taylor's theorem with remainder to  $(1+x)^m$  for  $1 < m < 2$  and  $x > 0$ , we only apply convexity to deduce that  $(1+x)^m \ge 1+mx$ . This gives

$$a_{n+1}^{(k+1)/k} - a_n^{(k+1)/k} \ge \frac{k+1}{k},$$

and so

$$a_n^{(k+1)/k} \ge \frac{k+1}{k} n + c$$

for some  $c \in \mathbb{R}$ . In particular,

$$\liminf_{n \to \infty} \frac{a_n^{(k+1)/k}}{n} \ge \frac{k+1}{k}$$

and so

$$\liminf_{n \to \infty} \frac{a_n}{n^{k/(k+1)}} \ge \left(\frac{k+1}{k}\right)^{k/(k+1)}.$$

But turning this around, the fact that

$$\begin{aligned} a_{n+1} - a_n &= a_n^{-1/k} \\ &\le \left(\frac{k+1}{k}\right)^{-1/(k+1)} n^{-1/(k+1)} (1+o(1)), \end{aligned}$$

where  $o(1)$  denotes a function tending to 0 as  $n \to \infty$ , yields

$$\begin{aligned} a_n &\le \left(\frac{k+1}{k}\right)^{-1/(k+1)} \sum_{i=1}^{n} i^{-1/(k+1)} (1+o(1)) \\ &= \frac{k+1}{k} \left(\frac{k+1}{k}\right)^{-1/(k+1)} n^{k/(k+1)} (1+o(1)) \\ &= \left(\frac{k+1}{k}\right)^{k/(k+1)} n^{k/(k+1)} (1+o(1)), \end{aligned}$$

so

$$\limsup_{n \to \infty} \frac{a_n}{n^{k/(k+1)}} \le \left(\frac{k+1}{k}\right)^{k/(k+1)}$$

and this completes the proof.

**Third solution:** We argue that  $a_n \to \infty$  as in the first solution. Write  $b_n = a_n - L n^{k/(k+1)}$ , for a value of  $L$  to be determined later. We have

$$\begin{aligned} b_{n+1} &= b_n + a_n^{-1/k} - L((n+1)^{k/(k+1)} - n^{k/(k+1)}) \\ &= e_1 + e_2, \end{aligned}$$

where

$$e_1 = b_n + a_n^{-1/k} - L^{-1/k} n^{-1/(k+1)}$$

$$e_2 = L((n+1)^{k/(k+1)} - n^{k/(k+1)}) \\ - L^{-1/k} n^{-1/(k+1)}.$$

We first estimate  $e_1$ . For  $-1 < m < 0$ , by the convexity of  $(1+x)^m$  and  $(1+x)^{1-m}$ , we have

$$\begin{aligned} 1+mx &\le (1+x)^m \\ &\le 1+mx(1+x)^{m-1}. \end{aligned}$$

Hence

$$\begin{aligned} -\frac{1}{k} L^{-(k+1)/k} n^{-1} b_n &\le e_1 - b_n \\ &\le -\frac{1}{k} b_n a_n^{-(k+1)/k}. \end{aligned}$$

Note that both bounds have sign opposite to  $b_n$ ; moreover, by the bound  $a_n = \Omega(n^{(k-1)/k})$ , both bounds have absolutely value strictly less than that of  $b_n$  for  $n$  sufficiently large. Consequently, for  $n$  large,

$$|e_1| \le |b_n|.$$

We now work on  $e_2$ . By Taylor's theorem with remainder applied to  $(1+x)^m$  for  $x > 0$  and  $0 < m < 1$ ,

$$\begin{aligned} 1+mx &\ge (1+x)^m \\ &\ge 1+mx + \frac{m(m-1)}{2} x^2. \end{aligned}$$

The “main term” of  $L((n+1)^{k/(k+1)} - n^{k/(k+1)})$  is  $L \frac{k}{k+1} n^{-1/(k+1)}$ . To make this coincide with  $L^{-1/k} n^{-1/(k+1)}$ , we take

$$L = \left(\frac{k+1}{k}\right)^{k/(k+1)}.$$

We then find that

$$|e_2| = O(n^{-2}),$$

and because  $b_{n+1} = e_1 + e_2$ , we have  $|b_{n+1}| \le |b_n| + |e_2|$ . Hence

$$|b_n| = O\left(\sum_{i=1}^{n} i^{-2}\right) = O(1),$$