上述程序框图用的是当型循环结构, 如果用直到型循环结构表示, 则程序框图为(图 1.1-15):

![Program flowchart (Figure 1.1-15) using a post-test loop structure.]()Flowchart (Figure 1.1-15) illustrating a post-test loop structure (DO-WHILE/DO-UNTIL) designed to calculate the sum of integers from 1 to 100. The steps are: Start (Oval) → Process:  $i=1$  (Rectangle) → Process:  $S=0$  (Rectangle). Then enters the loop body: Process:  $S=S+i$  (Rectangle) → Process:  $i=i+1$  (Rectangle). Then the decision diamond:  $i > 100?$ . If No (否), flow returns to  $S=S+i$ . If Yes (是), flow proceeds to Output  $S$  (Parallelogram) → End (Oval).

![](_page_0_Figure_3.jpeg)

图 1.1-15![Icon of a book with a question mark, labeled '思考' (Thought).]()![](_page_0_Picture_5.jpeg)

如何用自然语言表述图 1.1-15 中的算法? 改进这一算法, 表示输出  $1, 1+2, 1+2+3, ext{ extellipsis}, 1+2+3+ ext{ extellipsis}+(n-1)+n (n ext{ extepsilon} N^*)$  的过程.

例 7 某工厂 2005 年的年生产总值为 200 万元, 技术革新后预计以后每年的年生产总值都比上一年增长 5%. 设计一个程序框图, 输出预计年生产总值超过 300 万元的最早年份.

算法分析:

先写出解决本例的算法步骤:

第一步, 输入 2005 年的年生产总值.

第二步, 计算下一年的年生产总值.

第三步, 判断所得的结果是否大于 300. 若是, 则输出该年的年份; 否则, 返回第二步.

由于“第二步”是重复操作的步骤, 所以本例可以用循环结构来实现. 我们按照“确定循环体”“初始化变量”“设定循环控制条件”的顺序来构造循环结构.