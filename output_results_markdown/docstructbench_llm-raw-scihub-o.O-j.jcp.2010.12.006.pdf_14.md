![Figure 4 shows four plots of dispersion contours (ky vs kx) for Maxwell's equations.]()Figure 4 displays four plots of dispersion contours in the  $k_x$ - $k_y$  plane, ranging from -30 to 30 on both axes. The contours represent constant values of  $\omega$ .

- (a) Exact dispersion: Shows perfectly circular, concentric contours centered at the origin.
- (b) Boxscheme: Shows slightly squared, concentric contours centered at the origin.
- (c) Symplectic method: Shows a periodic pattern of contours resembling diamonds or squares, centered at the origin and repeating approximately every 30 units in both  $k_x$  and  $k_y$ .
- (d) Yee's method: Shows significantly squared/diamond-shaped, concentric contours centered at the origin.

![](_page_0_Figure_2.jpeg)

Fig. 4. The dispersion contours with stepsizes  $\Delta t = 0.01$ ,  $\Delta = 0.1$  for Maxwell's equations (46) from (a) exact dispersion; (b) boxscheme; (c) symplectic method and (d) Yee's method. The constant contour values are  $\omega \in [2, 4, 6, \dots, 24]$ .

$$\varphi = \tan^{-1} \left( \frac{(v_g)_y}{(v_g)_x} \right), \quad |v_g| = \sqrt{(v_g)_x^2 + (v_g)_y^2}. \quad (48)$$

Substituting into (48) the vectors  $\kappa$  and  $v_g$  in polar coordinates (44), and let  $a = |\kappa|\Delta$ , this yields the propagation angle  $\varphi$  and the propagation speed  $|v_g|$  in terms of  $a$  and  $\theta$ .

For example,  $\varphi$  for the boxscheme is given by

$$\varphi = \tan^{-1} \left( \frac{\sin\left(\frac{1}{2}\sin(\theta)a\right)\cos^3\left(\frac{1}{2}\cos(\theta)a\right)}{\cos^3\left(\frac{1}{2}\sin(\theta)a\right)\sin\left(\frac{1}{2}\cos(\theta)a\right)} \right)$$

Taking the Taylor expansion of this expression with respect to  $a = 0$  yields,

$$\varphi \approx \theta - \frac{1}{12} \sin(4\theta)a^2 + O(a^3). \quad (49)$$

Similarly, the Taylor expansion of  $|v_g|$  at  $a = 0$  yields,

$$|v_g| \approx 1 + \left( \frac{1}{16} \cos(4\theta) - \frac{r^2}{4} + \frac{3}{16} \right) a^2 + O(a^4), \quad (50)$$