Parallel processing of products on the computer is facilitated by a variant of (3) for computing  $\mathbf{C} = \mathbf{AB}$ , which is used by standard algorithms (such as in Lapack). In this method,  $\mathbf{A}$  is used as given,  $\mathbf{B}$  is taken in terms of its column vectors, and the product is computed columnwise; thus,

$$(5) \mathbf{AB} = \mathbf{A}[\mathbf{b}_1 \mathbf{b}_2 \dots \mathbf{b}_p] = [\mathbf{Ab}_1 \mathbf{Ab}_2 \dots \mathbf{Ab}_p].$$

Columns of  $\mathbf{B}$  are then assigned to different processors (individually or several to each processor), which simultaneously compute the columns of the product matrix  $\mathbf{Ab}_1$ ,  $\mathbf{Ab}_2$ , etc.