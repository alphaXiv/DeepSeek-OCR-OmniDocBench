![Zhejiang University logo]()![](_page_0_Picture_0.jpeg)

浙江大学  
Zhejiang University

## 数学建模

# 奇点分类 (III)

- $\Delta = 0$  A, 有两个相同的特征值

$$\mathbf{P} \xi \xi (1 \ 2) \quad \mathbf{P}^{-1} \mathbf{A} \mathbf{P} = \begin{pmatrix} \lambda & 0 \\ 0 & \lambda \end{pmatrix}$$
$$\begin{cases} \frac{du}{dt} = \lambda u \\ \frac{dv}{dt} = \lambda v \end{cases} \quad \begin{cases} u = u_0 e^{\lambda t} \\ v = v_0 e^{\lambda t} \end{cases} \quad \frac{u}{v} = \frac{u_0}{v_0}$$

- $\alpha < 0, \lambda < 0$
- $\alpha > 0, \lambda > 0$

$$\frac{du}{dt} = \mathbf{P}^{-1} \mathbf{A} \mathbf{P} u$$
$$\alpha = \operatorname{tr}(\mathbf{A}) = \lambda_1 + \lambda_2$$
$$\beta = |\mathbf{A}| = \lambda_1 \lambda_2$$

![Phase portrait showing radial trajectories pointing towards the origin in the u-v plane, characteristic of a stable star node (sink).]()![](_page_0_Figure_8.jpeg)