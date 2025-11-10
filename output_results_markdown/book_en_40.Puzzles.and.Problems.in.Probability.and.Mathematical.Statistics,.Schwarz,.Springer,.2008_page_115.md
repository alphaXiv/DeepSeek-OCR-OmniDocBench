The last two expectations in this expression are known from the basic result about  $E[U]$  so that the only really new part concerns the expectation of the product  $UV$ . Now, by the definition of  $U$ ,  $V$ 

$$UV = \exp(X) \cdot \exp(Y) = \exp(X + Y)$$

Let the rv  $S = X + Y$ . Clearly,  $S$  is normally distributed, with mean  $\mu_s = \mu_x + \mu_y$  and variance  $\sigma_s^2 = \sigma_x^2 + \sigma_y^2 + 2\rho\sigma_x\sigma_y$ . It then follows from the basic result about  $E[U]$  that

$$\begin{aligned}E[UV] &= E[\exp(S)] \\ &= \exp\left(\mu_s + \frac{1}{2}\sigma_s^2\right)\end{aligned}$$

Putting together this result \text{---} with  $\mu_s, \sigma_s$  expressed in terms of the original parameters as earlier \text{---} and the previously known facts about the means and variances of  $U$ ,  $V$ , the correlation coefficient is, after slight simplification, found to be

$$\operatorname{corr}(U, V) = \frac{\exp(\rho\sigma_x\sigma_y) - 1}{\sqrt{[\exp(\sigma_x^2) - 1][\exp(\sigma_y^2) - 1]}}$$

Note that the correlation between  $U$  and  $V$  is completely independent of the means of  $X$  and  $Y$ . As explained earlier, the exponentiation turns the *location* parameters  $\mu_x, \mu_y$  of  $X$  and  $Y$  into *scaling factors* of  $U$  and  $V$ . Because variations of the scaling factors generally do not change linear correlations, the result was to be expected. On the other hand, the standard deviations  $\sigma_x, \sigma_y$  of  $X$  and  $Y$  turn into *powers* for  $U$  and  $V$ , which generally do influence the linear correlation coefficient.

The result about the correlation of  $U$  and  $V$  may also be used to verify the properties we already discussed in part c. Note, in particular, that in the equal-variance case  $\sigma_x = \sigma_y = \sigma$  we get

$$\operatorname{corr}(U, V) = \frac{\exp(\rho\sigma^2) - 1}{\exp(\sigma^2) - 1}$$

The correlation of  $U$  and  $V$  is shown in Figure 3.25 as a function of the correlation  $\rho$  of the original rvs  $X$  and  $Y$ , for three values of  $\sigma$ . For  $\rho = +1$ , the two correlations are identical, but for any other value the correlation between  $U$  and  $V$  is weaker than that between  $X$  and  $Y$ .