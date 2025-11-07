## 避免凌乱的曲线图

在用曲线图做趋势比较时，若有超过3个以上数据系列，极易出现曲线之间相互交叉、乱成一团麻的情况，很难清楚地观察各个系列的变化趋势（图3-29）。

在这种情况下，可以使用一种叫作平板图（Panel chart）的图表处理方法。

如图3-30所示，将各条曲线分开来绘制，彼此并不交叉影响，显得很清晰。但它们仍在一个图表中，共用一个纵坐标轴，便于观察趋势和比较大小。这种处理方法适用于多系列曲线图，系列之间量纲相同，数量级相差不是太大的情况。

其实现技巧，只是将原来的数据源进行图中所示的“错行”组织，做出的曲线图自然也就错开了。独立的格子通过设置网格线间隔实现，上面的公司名称标签使用文本框或辅助系列来完成。具体做法这里不再细述，读者可参见范例文件中的步骤。

![Figure 3-29: A line chart showing market share data for six companies (Company 1 to Company 6) from 2002 to 2009. The lines are highly overlapping and crossing each other, making it difficult to read and analyze the trends.]()![](_page_0_Figure_5.jpeg)

图3-29 线条纠缠在一起显得异常凌乱，不便于阅读分析

![Figure 3-30: A panel chart (subplots) showing market share data for six companies (Company 1 to Company 6) from 2002 to 2009. Each company's data is plotted in its own subplot, separated by vertical grid lines, avoiding line crossing and making trends easier to read.]()![](_page_0_Figure_7.jpeg)

图3-30 将多系列的曲线图做成彼此分离的平板图，避免了曲线的交叉凌乱