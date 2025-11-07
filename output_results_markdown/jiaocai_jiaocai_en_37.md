2. (18%) On FA and Regular LanguagesSay whether each of the following languages is regular or not regular? Prove your answers.

(a)  $L_1 = \{w | w \in \{0, 1\}^* \text{ and } w \text{ has an equal number of 0s and 1s}\}$ .

(b)  $L_2 = \{w | w \in \{0, 1\}^* \text{ and } w \text{ has an equal number of 01s and 10s}\}$ .

3. (20%) On PDA and Context-Free LanguagesLet  $L_3 = \{wca^m b^n | w \in \{a, b\}^*, \text{ where } w = w^R, \text{ and } m, n \in \mathbb{N}, n \le m \le 2n\}$ .

(a) Give a context-free grammar for the language  $L_3$ .

(b) Design a PDA  $M = (K, \Sigma, \Gamma, \Delta, s, F)$  accepting the language  $L_3$ .

Solution: (a)

(b) The PDA  $M = (K, \Sigma, \Gamma, \Delta, s, F)$  is defined below:

|                                            | $(q, \sigma, \beta)$ | $(p, \gamma)$ |
|--------------------------------------------|----------------------|---------------|
| $K = \{$ _______________________ $\}$      |                      |               |
| $\Sigma = \{a, b, c\}$                     |                      |               |
| $\Gamma = \{$ _______________________ $\}$ |                      |               |
| $s =$ _______________________              |                      |               |
| $F = \{$ _______________________ $\}$      |                      |               |