续表

| 序号 | 监控内容    | 连接变量   | 输入值   |       | 输出值   |      |      |
|----|---------|--------|-------|-------|-------|------|------|
|    |         |        | 数值类型  | 数值范围  | 数值类型  | 整数位数 | 小数位数 |
| 3  | 操作值     | MV     |       |       | 模拟量输出 | 3位   | 2位   |
| 4  | 手动设定值   | SP_man | 模拟量输入 | 0~100 | 模拟量输出 | 3位   | 2位   |
| 5  | PID比例系数 | PID0_P | 模拟量输入 | 0~100 | 模拟量输出 | 3位   | 2位   |
| 6  | PID积分时间 | PID0_I | 模拟量输入 | 0~100 | 模拟量输出 | 3位   | 2位   |
| 7  | PID微分时间 | PID0_D | 模拟量输入 | 0~100 | 模拟量输出 | 3位   | 2位   |
| 8  | 控制方式    | MAN_on | 离散值输入 | 0或1   | 离散值输出 |      |      |

实时趋势曲线 (Real-time Trend Curve) Dialog Box

Tabs: 曲线定义 (Curve Definition) | 标识定义 (Identifier Definition) (Active)

 标识X轴——时间轴 (Mark X-axis — Time Axis) 标识Y轴——数值轴 (Mark Y-axis — Value Axis)

数值轴 (Value Axis)标识数目 (Number of Identifiers):  起始值 (Start Value):  最大值 (Maximum Value): 

整数位数 (Integer Digits):  小数位位数 (Decimal Digits):   科学计数法 (Scientific Notation) 字体 (Font)

数值格式 (Value Format) 工程百分比 (Engineering Percentage)  
 实际值 (Actual Value)

时间轴 (Time Axis)标识数目 (Number of Identifiers):  格式 (Format):  年  月  日  时  分  秒

更新频率 (Update Frequency):   秒 (Second)  分 (Minute) 字体 (Font)

时间长度 (Time Length):   秒 (Second)  分 (Minute)  时 (Hour)

确定 (Confirm) 取消 (Cancel)

![](_page_0_Picture_3.jpeg)

图4.75 实时趋势曲线标识定义——设置坐标轴液位PID控制 (Level PID Control)

A monitoring interface displaying a real-time trend graph. The Y-axis ranges from 000.00 to 100.00.

Below the graph, system parameters and controls are displayed:

| 手动设定值 (Manual Setpoint): ###### | 比例系数 (Proportion Coefficient): ###### | <button>自动方式 (Automatic Mode)</button>             |
|---------------------------------|---------------------------------------|----------------------------------------------------|
| 设定值 (Setpoint): ######          | 积分时间 (Integral Time): ######          | <button>启动变频器 (Start Frequency Converter)</button> |
| 测量值 (Measured Value): ######    | 微分时间 (Differential Time): ######      | <button>手动方式 (Manual Mode)</button>                |
| 操作值 (Operation Value): ######   | 控制方式 (Control Mode): ######           | <button>停变频器 (Stop Frequency Converter)</button>   |

![](_page_0_Figure_5.jpeg)

图4.76 监控主界面