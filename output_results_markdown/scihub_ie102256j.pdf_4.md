![Figure 5 shows four plots illustrating sensitivity analysis and SVD results for the ternary system, comparing three relative volatility cases: alpha_390 = 1.50 (red dashed-dotted line), alpha_390 = 1.75 (green dashed line), and alpha_390 = 2.00 (solid blue line). The x-axis for all plots is N_T (Number of Trays), ranging from 0 to 30.
Top Left Plot: K_FA0 (Sensitivity of K to F_A0) vs N_T. K_FA0 ranges from -400 to 0.
Top Right Plot: K_FB0 (Sensitivity of K to F_B0) vs N_T. K_FB0 ranges from -20 to 60.
Bottom Left Plot: U_FA0 (SVD result for F_A0) vs N_T. U_FA0 ranges from -0.4 to 0.
Bottom Right Plot: U_FB0 (SVD result for F_B0) vs N_T. U_FB0 ranges from -0.2 to 0.6.
]()![](_page_0_Figure_2.jpeg)

Figure 5. Sensitivity analysis and SVD results for ternary system.

**Table 4. Controller Pairing and Parameters for Ternary System**

| $\alpha_{390}$ | loop              | $K_C$ | $\tau_I$ | action  |
|----------------|-------------------|-------|----------|---------|
| 2.00           | $T_4 - F_{A0}$    | 8.29  | 16.76    | direct  |
|                | $T_{18} - F_{B0}$ | 19.54 | 22.57    | reverse |
| 1.75           | $T_6 - F_{A0}$    | 5.70  | 39.6     | direct  |
|                | $T_{23} - F_{B0}$ | 11.26 | 11.22    | reverse |
| 1.50           | $T_9 - F_{A0}$    | 8.87  | 40.13    | direct  |
|                | $T_{29} - F_{B0}$ | 51.01 | 20.20    | reverse |

increase as the value of  $\alpha_{390}$  decreases. However, the offset does not exceed 0.1 mol % even for the case of  $\alpha_{390} = 1.50$ .

The results of this ternary system differ significantly from those of the quaternary systems in terms of the actions of temperature controllers. The studies on quaternary systems concluded that the two temperature controllers had to have the same action.<sup>6</sup> However, dynamically stable results are obtained for this ternary system with temperature controllers having opposite actions. Details of the physical explanation of this situation are given in a recent paper.<sup>26</sup>

**3.2. Ternary System with Inert Component.** The flowsheet of ternary system with inert is given in Figure 9. This system involves four components. However, one of them is an inert component I in terms of the reaction. Since its volatility is assumed the same as that of the light reactant A, it is fed from the fresh feed stream  $F_{A0}$  as a mixture with A. The other fresh feed stream  $F_{B0}$  contains pure reactant B. While the heavy product C leaves the column from the bottom, the low-boiling inert I is removed from the distillate without taking part in the reaction. Thus, the column has three zones: a stripping section, a reactive zone, and a rectifying section. It is assumed that the light and heavy fresh feed streams are fed from the bottom and top trays of the reactive zone, respectively.

The main design objective is to obtain the purity of the bottoms product at 98 mol % C. On the other hand, the amount of reactants escaping from the distillate stream should also be considered. This is especially important for the light reactant A, which has an identical volatility with the inert component I.

Thus, a constraint of 3 mol % is defined for the maximum amount of reactants leaving the column from the top. The liquid holdups in the reactive trays are selected as 2000 mols to have reasonable liquid height. The composition of  $F_{A0}$  is 50 mol % A and 50 mol % I. Kinetic parameters of the ternary system are given in Table 5. The basic design procedure is based on the existing paper in the literature.<sup>21</sup>

The optimization problem for the ternary system with inert includes five design variables. These are (1) the number of stripping trays  $N_S$ , (2) the number of reactive trays  $N_{RX}$ , and (3) the number of rectifying trays  $N_R$ , (4) the column pressure  $P$ , and (5) the reflux  $R$ . The objective function is TAC, and the same basis of economics is used as that has been used for the ternary system without inert component.

Table 6 gives the optimum design parameters and economics for the relative volatility cases considered. For the base case of  $\alpha_{390} = 2.00$ , the optimum operating pressure of the column is 9 bar. The bottoms purity of 98 mol % C is achieved with a column having 7 stripping, 12 reactive, and 7 rectifying trays. The column diameter is 1.00 m with a vapor boilup of 55.06 mol/s. The total capital investment for the column, reboiler, and condenser is  $\$532.42 \times 10^3$ , while the cost of energy is  $\$237.33 \times 10^3$ /yr. Assuming a payback period of 3 years, the TAC is  $\$414.80 \times 10^3$ /yr. There is a slight decrease in the operating pressure with the decrease of  $\alpha_{390}$ , but the change is not dramatic. This decrease is reasonable because lower pressure helps the VLE by reducing temperatures and increasing relative volatilities. There is an increase in the optimum number of total trays with the decrease of  $\alpha_{390}$ . Decrease of  $\alpha_{390}$  from 2.00 to 1.75 results in a higher change in the number of separation trays. On the other hand, the increase in the number of reactive trays is more remarkable for the case of  $\alpha_{390} = 1.50$ . The other design variable reflux  $R$  and the vapor boilup  $V_S$  increase dramatically as  $\alpha_{390}$  declines. Thus, the capital and energy costs get significantly higher as the value of  $\alpha_{390}$  decreases.

Figure 10 shows the temperature profiles of three relative volatility cases. There is a sharp temperature profile for the case of  $\alpha_{390} = 2.00$ . This is especially true for the stripping section. The decrease of the value of  $\alpha_{390}$  moderates the sharpness of the temperature profile. The size of the hump in the reactive zone also