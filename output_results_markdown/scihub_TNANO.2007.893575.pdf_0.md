A New Capacitorless 1T DRAM Cell: Surrounding Gate MOSFET With Vertical Channel (SGVC Cell)Hoon Jeong, Ki-Whan Song, Il Han Park, Tae-Hun Kim, Yeun Seung Lee, Seong-Goo Kim, Jun Seo, Kyoungyong Cho, Kangyoon Lee, Hyungcheol Shin, Member, IEEE, Jong Duk Lee, Member, IEEE, and Byung-Gook Park, Member, IEEE

**Abstract**—We propose a surrounding gate MOSFET with vertical channel (SGVC cell) as a 1T DRAM cell. To confirm the memory operation of the SGVC cell, we simulated its memory effect and fabricated the highly scalable SGVC cell. According to simulation and measurement results, the SGVC cell can operate as a 1T DRAM having a sufficiently large sensing margin. Also, due to its vertical channel structure and common source architecture, it can readily be made into a  $4F^2$  cell array.

**Index Terms**—Memory effect, 1T DRAM cell, sensing margin, surrounding gate, vertical channel.

I. INTRODUCTIONTO OVERCOME the scalability issues and process complexity of 1-transistor/1-capacitor DRAM cell, capacitorless 1-transistor (1T) DRAM cells have been recently proposed and investigated [1]. The mainstream 1T DRAM cell is a floating body transistor cell (FBC) which consists of a MOSFET with its body floating electrically. The FBC is realized by a MOSFET formed on partially depleted silicon-on-insulator (PD-SOI). When excess holes exist in the floating body, the cell state can be defined as “1” (decreased  $V_{ ext{th}}$ ). On the other hand, when excess holes are swept out of the floating body through forward bias on the body–drain junction, the cell state can be defined as “0” (increased  $V_{ ext{th}}$ ). By measuring the drain current difference between “1” and “0” states of the cell, we can sense whether the holes are accumulated in the floating body. Because the floating body is used as the storage node, the FBC has no complicated storage capacitor. Therefore, the FBC has a simple process and can have a cell area below  $4F^2$ . [2], [3]

In this work, we propose a surrounding gate MOSFET with vertical channel (SGVC cell) as a 1T DRAM cell. Unlike other 1T DRAM cells which are integrated on SOI substrates, the SGVC cell can be more cost effective since it can be fabricated on bulk Si substrates. Also, there is no need for the source contact and line due to the common source structure, which makes

Manuscript received June 18, 2006; revised December 9, 2006. This work was presented at the 2006 IEEE Silicon Nanoelectronics Workshop. The review of this paper was arranged by Associate Editor T. Hiramoto.

H. Jeong, I. H. Park, T.-H. Kim, Y. S. Lee, H. Shin, J. D. Lee and B.-G. Park are with the School of Electrical Engineering, Seoul National University, Seoul 151-742, Korea (e-mail: gbhbt@naver.com).

K.-W. Song is with the ATD Team, Semiconductor R&D Division, Samsung Electronics Co. Ltd., Youngin 449-711, Korea.

S.-G. Kim and K. Lee are with the Technology Development Team, Semiconductor R&D Division, Samsung Electronics Co. Ltd., Youngin 449-711, Korea.

J. Seo and K. Cho is with the Process Development Team, Semiconductor R&D Division, Samsung Electronics Co. Ltd., Youngin 449-711, Korea

Color versions of one or more of the figures in this paper are available online at http://ieeexplore.ieee.org.

Digital Object Identifier 10.1109/TNANO.2007.893575

TABLE I  
SGVC CELL SIMULATION PARAMETERS

|                | Program (1/0)<br>(Impact Ionization) | Read  |
|----------------|--------------------------------------|-------|
| Gate Voltage   | 1 V                                  | 1 V   |
| Drain Voltage  | 1 V (-1 V)                           | 0.1 V |
| Source Voltage | 0 V                                  | 0 V   |
|                |                                      |       |