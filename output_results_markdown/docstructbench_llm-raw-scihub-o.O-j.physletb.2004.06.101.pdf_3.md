For consistency, the time derivative of the constraints of (10) must vanish and hence they must have vanishing Poisson bracket with  $H$ . Using the fundamental Poisson brackets

$$[U(x), \Pi^U(y)] = \delta(x - y), \quad (13)$$

etc., we find that the primary constraints of (10) imply the secondary constraints

$$(\Sigma, \Sigma_i) = (-\partial_k \Pi_k^V, \varepsilon^{ijk} \partial_j (\Pi_k^B - m V_k) - \mu^2 B_i). \quad (14)$$

If  $\mu^2 = 0$  (the Cremmer–Scherk model Lagrangian [1]), the constraints of (14) would become reducible as then  $\partial_i \Sigma_i = 0$  and only the transverse portions of  $\Sigma_i$  are constraints. Furthermore, with  $\mu^2 \neq 0$ , the requirement  $\dot{\Sigma}_i = 0$  leads to a tertiary constraint

$$T_k \equiv \mu^2 \Pi_k^B = 0 \quad (15)$$

with  $\Sigma_i$  and  $T_k$  constituting second class constraints as

$$[T_k(x), \Sigma_i(y)] = \mu^4 \delta_{ik} \delta(x - y). \quad (16)$$

All other constraints are first class and no further constraints need to be imposed for consistency. There are consequently five first class constraints ( $\Phi^U$ ,  $\Phi_k^A$  and  $\Sigma$ ) and six second class constraints ( $\Sigma_i$  and  $T_k$ ). The constraints  $\Phi^U$  and  $\Sigma$  correspond to the usual gauge transformations  $\delta W_0 = \partial_0 \Omega$ ,  $\delta W_i = \partial_i \Omega$  associated with a gauge field  $W_\mu$ , while  $\Phi_k^A$  is associated with the fact that in (12)  $A_k$  acts merely as a Lagrange multiplier (i.e., it is not dynamical) and hence its value is completely arbitrary. Suitable gauge conditions associated with the first class constraints are

$$(\gamma^U, \gamma_k^A, \gamma^V) = (U, A_k, \partial_k V_k) = 0. \quad (17)$$

From (10), (14), (15) and (17) it is evident that the only dynamical degrees of freedom are

$$V_i^T \equiv (\delta_{ij} - \partial_i \partial_j / \partial^2) V_j. \quad (18)$$

We can verify this directly by explicitly eliminating the non-physical degrees of freedom in (4). First, one decomposes  $V_k$ ,  $A_k$  and  $B_k$  into transverse ( $T$ ) and longitudinal ( $L$ ) parts where

$$\nabla \times \mathbf{V}^L \equiv 0 \equiv \nabla \cdot \mathbf{V}^T, \quad (19)$$

etc., (4) now becomes

$$2L = (\dot{\mathbf{B}}^L)^2 - (\nabla \cdot \mathbf{B}^L)^2 + [\dot{\mathbf{B}}^T - \nabla \times \mathbf{A}^T]^2 + (\dot{\mathbf{V}}^T)^2 - (\nabla \times \mathbf{V}^T)^2 + [\dot{\mathbf{V}}^L - \nabla U]^2 \\ + 2m[\mathbf{V}^T \cdot (\nabla \times \mathbf{A}^T) + \mathbf{B}^L \cdot \dot{\mathbf{V}}^L + \mathbf{B}^T \cdot \dot{\mathbf{V}}^T - \mathbf{B}^L \cdot \nabla U] + 2\mu^2[\mathbf{A}^T \cdot \mathbf{B}^T + \mathbf{A}^L \cdot \mathbf{B}^L]. \quad (20)$$

The equations of motion for  $\mathbf{A}^L$  and  $U$ , respectively, imply that

$$\mathbf{B}^L = 0 = \dot{\mathbf{V}}^L - \nabla U, \quad (21)$$

reducing (20) to

$$2L = (\dot{\mathbf{V}}^T)^2 - (\nabla \times \mathbf{V}^T)^2 + [\dot{\mathbf{B}}^T - \nabla \times \mathbf{A}^T]^2 + 2m\mathbf{V}^T \cdot (\nabla \times \mathbf{A}^T) + 2m\mathbf{B}^T \cdot \dot{\mathbf{V}}^T + 2\mu^2\mathbf{A}^T \cdot \mathbf{B}^T. \quad (22)$$

Since

$$\mathbf{A}^T \cdot \mathbf{B}^T = -(\nabla \times \mathbf{A}^T) \cdot (\nabla^2)^{-1} (\nabla \times \mathbf{B}^T), \quad (23)$$

we can eliminate  $\nabla \times \mathbf{A}^T$  from (22) to obtain

$$\nabla \times \mathbf{A}^T = \dot{\mathbf{B}}^T - m\mathbf{V}^T + \mu^2 (\nabla^2)^{-1} (\nabla \times \mathbf{B}^T). \quad (24)$$