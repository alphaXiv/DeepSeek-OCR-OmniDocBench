![Figure 6-19 shows a 3D model of a helmet. A red point (点) is marked on the top center, and a red auxiliary ellipse (椭圆辅助线) is drawn around the base of the helmet.]()![](_page_0_Picture_0.jpeg)

图 6-19 绘制辅助线和点

在顶视图中以刚刚绘制的水平线为直径，捕捉其两个端点绘制一个椭圆，如图 6-20 所示。

![Figure 6-20 shows a top view of the construction geometry. A large yellow ellipse (椭圆) is drawn. A red point (点) is marked at the center, and a vertical purple auxiliary line (辅助线) passes through the center, representing the diameter used for drawing the ellipse.]()![](_page_0_Picture_3.jpeg)

图 6-20 绘制椭圆

### 3. 绘制曲线

在左视图中捕捉点和椭圆的四分点，参考头盔背景图绘制头盔两侧的两条曲线，并适当调整使其光滑，如图 6-21 所示。

![Figure 6-21 shows a side view of the construction geometry. Two smooth yellow curves, labeled '线1' (Curve 1, on the right) and '线2' (Curve 2, on the left), are drawn, defining the profile of the helmet.]()![](_page_0_Picture_7.jpeg)

图 6-21 绘制两侧曲线

### 4. 双轨扫掠

执行“建立曲面”工具箱中的“双轨扫掠”命令，以点和椭圆为路径，以两条曲线为断面曲线，在打开的“双轨扫掠选项”对话框中，直接单击“确定”，完成头盔主体曲面的创建，如图 6-22 所示。

![Figure 6-22 shows the result of the 'Double Rail Sweep' command, creating the main helmet surface. The image also displays the '双轨扫掠选项' (Double Rail Sweep Options) dialog box. The options include:
断面曲线选项 (Cross-section Curve Options):
- 不要更改断面(D) (Do not change cross-section)
- 重建断面点数(R) (Rebuild cross-section points): 5 个控制点(O) (Control points)
- 重新逼近断面公差(F) (Refit cross-section tolerance): 0.01
- 维持第一个断面形状(V) (Maintain first cross-section shape)
- 维持最后一个断面形状(L) (Maintain last cross-section shape)
- 保持高度(M) (Maintain height) [Checkbox unchecked]
- 正切但不分割(A) (Tangent but not split) [Checkbox unchecked]
边缘连续性 (Edge Continuity) section with a table for A and B edges and columns for 位置 (Position), 相切 (Tangent), and 曲率 (Curvature).
Button: 加入控制断面 (Add control cross-section).
Buttons: 确定 (OK), 取消 (Cancel), 说明(H) (Help).]()![](_page_0_Picture_11.jpeg)

图 6-22 双轨扫掠

### 5. 绘制前部侧面轮廓线

执行“控制点曲线”命令，参考背景图，在左视图中绘制头盔侧面轮廓线，如图 6-23 所示。

![Figure 6-23 shows a 3D model of the helmet with a yellow control point curve (曲线) drawn along the front side profile, defining the boundary for the visor area.]()![](_page_0_Picture_15.jpeg)

图 6-23 绘制前部侧面轮廓线

### 6. 分割前部曲面

执行左侧工具条上的“分割”命令，选择头盔曲面作为“要分割的物件”，选择刚绘制的曲线作为“切割用物件”，进行曲面分割，分割后的效果如图 6-24 所示。此时可通过执