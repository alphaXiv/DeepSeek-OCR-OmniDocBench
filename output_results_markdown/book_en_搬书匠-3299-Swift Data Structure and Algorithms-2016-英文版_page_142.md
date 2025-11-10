Now let's review these concepts with the following tree example:

![Diagram of a binary tree. The root node is labeled 2. It connects to two child nodes: 8 and 1. Node 8 connects to leaves 7 and 11. Node 1 connects to leaf 5. The nodes are labeled 'Root', 'Edge', 'Node', and 'Leaves'.]()This figure shows a tree data structure example. The root node is 2. It branches to nodes 8 and 1. Node 8 branches to leaves 7 and 11. Node 1 branches to leaf 5. Node 2 is labeled "Root". The edge connecting 2 and 8 is labeled "Edge". Node 1 is labeled "Node". Nodes 7, 11, and 5 are grouped and labeled "Leaves".

![](_page_0_Figure_2.jpeg)

Tree data structure elements

- Root node: [2].
- Nodes: [2, 8, 1, 7, 11, 5].
- Leaves: [7, 11, 5].
- Height: There are two edges between the root [2] and the furthest connected leaf (which could be [7], [11], or [5] with same distance from the root). So the height of the tree is 2.
- Parent example: [8] is the parent of [7, 11].
- Children example: [7, 11] are the children of [8]. [5] is the child of [1].
- Subtrees: Starting in the root node [2], It has two subtrees: one is [8, 7, 11] and another one is [1, 5].
- Height of node [8]: 1.
- Depth of node [5]: 2.
- Level of root node: Depth + 1 = 0 + 1 = 1.

## Overview of different types of tree

There are different types of tree data structures, each one with their own benefits and implementations. We are going to have a quick look over the most common ones so we can gain a good overview of the different types and choose which one to use in each case wisely.

After the following introduction to the different types of trees, we will go deeper into the details, properties, uses, and implementations.