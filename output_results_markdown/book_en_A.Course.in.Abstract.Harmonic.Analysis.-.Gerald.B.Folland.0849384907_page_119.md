Let  $g, h$  be the inverse Fourier transforms of  $\chi_U, \chi_{U_K}$  (as given by the Plancherel theorem), and let  $f = |U|^{-1}gh$ . Then  $f \in L^1$  and  $\hat{f} = \hat{g} * \hat{h}$  by Proposition (4.36); thus  $\hat{f}(\xi) = |U|^{-1} \int_U \chi_{U_K}(\eta^{-1}\xi) d\eta$  has the desired properties. ■

(4.51) Theorem. If  $N \subset \hat{G}$  is closed, then  $\nu(\iota(N)) = N$ .

Proof: If  $\xi \notin N$ , take  $K = \{\xi\}$  and  $W = \hat{G} \setminus N$  in Lemma (4.50) to obtain  $f \in \iota(N)$  such that  $\hat{f}(\xi) \neq 0$ . ■

When  $G$  is compact, the other half of the correspondence is easily analyzed. First, a simple lemma that will also be useful elsewhere.

(4.52) Lemma. If  $f \in L^1(G)$  and  $\xi \in \hat{G}$  ( $\subset L^\infty(G)$ ) then  $f * \xi = \hat{f}(\xi)\xi$ .

Proof: For any  $x \in G$ ,

$$f * \xi(x) = \int f(y) \langle y^{-1}x, \xi \rangle dy = \langle x, \xi \rangle \int f(y) \overline{\langle y, \xi \rangle} dy = \hat{f}(\xi) \langle x, \xi \rangle. \quad \square$$

(4.53) Theorem. If  $G$  is compact, then  $\iota(\nu(I)) = I$  for every closed ideal  $I \subset L^1(G)$ .

Proof: Since  $G$  is compact, we have  $\hat{G} \subset L^\infty \subset L^2 \subset L^1$ . Suppose  $f \in \iota(\nu(I))$ . Then  $f * \xi = \hat{f}(\xi)\xi$  by Lemma (4.52), and either  $\hat{f}(\xi) = 0$  or  $\xi \notin \nu(I)$ . In the first case,  $f * \xi = 0$ ; in the second case, there exists  $g \in I$  such that  $\hat{g}(\xi) = 1$ , so that  $\xi = g * \xi \in I$  by Lemma (4.52) again. In either case we have  $f * \xi \in I$ , and hence  $f * g \in I$  for any  $g$  in the linear span of  $\hat{G}$ . The latter is dense in  $L^2$  by Corollary (4.26), so  $f * g \in I$  for all  $g \in L^2$  since  $I$  is closed. Finally, we can take  $g$  to be an approximate identity to conclude that  $f \in I$ . ■

When  $G$  is noncompact, the question of whether  $\iota(\nu(I)) = I$  is much more delicate. We now exhibit a simple example to show that the answer can be negative.

(4.54) Theorem. Let  $G = \mathbb{R}^n$  with  $n \ge 3$ , and let  $S$  be the unit sphere in  $\mathbb{R}^n$ . There is a closed ideal  $I$  in  $L^1(\mathbb{R}^n)$  such that  $\nu(I) = S$  but  $I \neq \iota(S)$ .

Proof: First we observe that if  $f$  and  $x_1 f$  (= the function whose value at  $x$  is  $x_1 f(x)$ ) are in  $L^1(\mathbb{R}^n)$  then

$$\begin{aligned} -2\pi i (x_1 f) \hat{(\xi)} &= \int (-2\pi i x_1 e^{-2\pi i \xi \cdot x}) f(x) dx \\ &= \int \frac{\partial e^{-2\pi i \xi \cdot x}}{\partial \xi_1} f(x) dx = \frac{\partial \hat{f}}{\partial \xi_1}(\xi). \end{aligned} \quad (4.55)$$

Hence  $\partial \hat{f} / \partial \xi_1$  exists and is continuous.

Let  $I$  be the set of all  $f \in L^1$  such that  $x_1 f \in L^1$  and  $\hat{f}|_S = (\partial \hat{f} / \partial \xi_1)|_S = 0$ , and let  $I$  be the closure of  $I$  in  $L^1$ . Since  $(L_y f) \hat{(\xi)} =$