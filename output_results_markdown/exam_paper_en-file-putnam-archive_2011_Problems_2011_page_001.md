# The 72nd William Lowell Putnam Mathematical Competition

## Saturday, December 3, 2011

A1 Define a *growing spiral* in the plane to be a sequence of points with integer coordinates  $P_0 = (0,0), P_1, \dots, P_n$  such that  $n \ge 2$  and:

- the directed line segments  $P_0P_1, P_1P_2, \dots, P_{n-1}P_n$  are in the successive coordinate directions east (for  $P_0P_1$ ), north, west, south, east, etc.;
- the lengths of these line segments are positive and strictly increasing.

[Picture omitted.] How many of the points  $(x,y)$  with integer coordinates  $0 \le x \le 2011, 0 \le y \le 2011$  cannot be the last point,  $P_n$  of any growing spiral?

A2 Let  $a_1, a_2, \dots$  and  $b_1, b_2, \dots$  be sequences of positive real numbers such that  $a_1 = b_1 = 1$  and  $b_n = b_{n-1}a_n - 2$  for  $n = 2, 3, \dots$ . Assume that the sequence  $(b_j)$  is bounded. Prove that

$$S = \sum_{n=1}^{\infty} \frac{1}{a_1 \dots a_n}$$

converges, and evaluate  $S$ .

A3 Find a real number  $c$  and a positive number  $L$  for which

$$\lim_{r \to \infty} \frac{r^c \int_0^{\pi/2} x^r \sin x dx}{\int_0^{\pi/2} x^r \cos x dx} = L.$$

A4 For which positive integers  $n$  is there an  $n \times n$  matrix with integer entries such that every dot product of a row with itself is even, while every dot product of two different rows is odd?

A5 Let  $F: \mathbb{R}^2 \to \mathbb{R}$  and  $g: \mathbb{R} \to \mathbb{R}$  be twice continuously differentiable functions with the following properties:

- $F(u,u) = 0$  for every  $u \in \mathbb{R}$ ;
- for every  $x \in \mathbb{R}$ ,  $g(x) > 0$  and  $x^2 g(x) \le 1$ ;
- for every  $(u,v) \in \mathbb{R}^2$ , the vector  $\nabla F(u,v)$  is either  $0$  or parallel to the vector  $\langle g(u), -g(v) \rangle$ .

Prove that there exists a constant  $C$  such that for every  $n \ge 2$  and any  $x_1, \dots, x_{n+1} \in \mathbb{R}$ , we have

$$\min_{i \ne j} |F(x_i, x_j)| \le \frac{C}{n}.$$

A6 Let  $G$  be an abelian group with  $n$  elements, and let

$$\{g_1 = e, g_2, \dots, g_k\} \subseteq G$$

be a (not necessarily minimal) set of distinct generators of  $G$ . A special die, which randomly selects one of the elements  $g_1, g_2, \dots, g_k$  with equal probability, is rolled  $m$  times and the selected elements are multiplied to produce an element  $g \in G$ . Prove that there exists a real number  $b \in (0, 1)$  such that

$$\lim_{m \to \infty} \frac{1}{b^{2m}} \sum_{x \in G} \left( \text{Prob}(g = x) - \frac{1}{n} \right)^2$$

is positive and finite.

B1 Let  $h$  and  $k$  be positive integers. Prove that for every  $\epsilon > 0$ , there are positive integers  $m$  and  $n$  such that

$$\epsilon < |h\sqrt{m} - k\sqrt{n}| < 2\epsilon.$$

B2 Let  $S$  be the set of all ordered triples  $(p,q,r)$  of prime numbers for which at least one rational number  $x$  satisfies  $px^2 + qx + r = 0$ . Which primes appear in seven or more elements of  $S$ ?

B3 Let  $f$  and  $g$  be (real-valued) functions defined on an open interval containing  $0$ , with  $g$  nonzero and continuous at  $0$ . If  $fg$  and  $f/g$  are differentiable at  $0$ , must  $f$  be differentiable at  $0$ ?

B4 In a tournament, 2011 players meet 2011 times to play a multiplayer game. Every game is played by all 2011 players together and ends with each of the players either winning or losing. The standings are kept in two  $2011 \times 2011$  matrices,  $T = (T_{hk})$  and  $W = (W_{hk})$ . Initially,  $T = W = 0$ . After every game, for every  $(h,k)$  (including for  $h=k$ ), if players  $h$  and  $k$  tied (that is, both won or both lost), the entry  $T_{hk}$  is increased by 1, while if player  $h$  won and player  $k$  lost, the entry  $W_{hk}$  is increased by 1 and  $W_{kh}$  is decreased by 1.

Prove that at the end of the tournament,  $\det(T+iW)$  is a non-negative integer divisible by  $2^{2010}$ .

B5 Let  $a_1, a_2, \dots$  be real numbers. Suppose that there is a constant  $A$  such that for all  $n$ ,

$$\int_{-\infty}^{\infty} \left( \sum_{i=1}^{n} \frac{1}{1+(x-a_i)^2} \right)^2 dx \le An.$$

Prove there is a constant  $B > 0$  such that for all  $n$ ,

$$\sum_{i,j=1}^{n} (1 + (a_i - a_j)^2) \ge Bn^3.$$

B6 Let  $p$  be an odd prime. Show that for at least  $(p+1)/2$  values of  $n$  in  $\{0, 1, 2, \dots, p-1\}$ ,

$$\sum_{k=0}^{p-1} k! n^k \quad \text{is not divisible by } p.$$