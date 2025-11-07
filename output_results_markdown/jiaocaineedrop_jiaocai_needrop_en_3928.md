![Figure 15-1: Schematic diagram of a steam boiler pressure control system. Steam pressure P is measured and input to the Pressure Controller (PC). The PC output (multiplied by c1) is combined with a signal derived from the Gas flow (瓦斯气, F1) measurement (multiplied by c2) in a summing junction (Σ). The output of the summing junction serves as the setpoint for the Flow Controller (FC). The FC controls the Fuel Oil (燃料油, F2) flow via a control valve. Feedwater (给水) is also supplied to the boiler. Steam (蒸汽) is the output.]()![](_page_0_Picture_0.jpeg)

图 15-1

2、控制方框图如图 15-2 所示

![Figure 15-2: Detailed control block diagram for steam pressure control. The system uses cascade control with feedforward compensation. The pressure setpoint (压力设定值) is compared with the measured steam pressure (蒸汽压力测量变送). The error feeds into the Pressure Controller (PC). The PC output is multiplied by c1 and summed with the signal from the Gas Flow Measurement Transmitter (瓦斯气流量测量变送) multiplied by c2. This sum acts as the setpoint for the inner flow loop. This setpoint is compared with the measured Fuel Oil Flow (燃料油测量变送). The error feeds into the Flow Controller (FC). The FC output drives the Fuel Oil Control Valve (燃料油调节阀), resulting in flow F2, which affects the Steam Pressure P via the Steam Pressure Control Channel (蒸汽压力控制通道). The Gas Flow F1 acts as a disturbance via the Steam Pressure Disturbance Channel (蒸汽压力干扰通道). The outputs of the control and disturbance channels are summed to yield the Steam Pressure P.]()![](_page_0_Figure_3.jpeg)

图 15-2

$$\text{图中系数分别为: } c_1 = 1, c_2 = -\frac{\lambda_1}{\lambda_2}$$

3、控制阀为气开阀, FC 控制器为反作用控制器, PC 为反作用控制器