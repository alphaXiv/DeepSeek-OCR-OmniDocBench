### 7.3 Linear Systems of Equations. Gauss Elimination

#### Matrix Form of the Linear System (1). (continued)

We assume that the coefficients  $a_{jk}$  are not all zero, so that  $A$  is not a zero matrix. Note that  $x$  has  $n$  components, whereas  $b$  has  $m$  components. The matrix

$$\tilde{A} = \left[ \begin{array}{ccc|c} a_{11} & \cdots & a_{1n} & b_1 \\ \cdot & \cdots & \cdot & \cdot \\ \cdot & \cdots & \cdot & \cdot \\ a_{m1} & \cdots & a_{mn} & b_m \end{array} \right]$$

is called the **augmented matrix** of the system (1). The dashed vertical line could be omitted, as we shall do later. It is merely a reminder that the last column of  $\tilde{A}$  did not come from matrix  $A$  but came from vector  $b$ . Thus, we **augmented** the matrix  $A$ .