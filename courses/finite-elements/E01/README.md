# E01 materials: how three springs become `K u = f`

Finite Elements from Scratch (I used two open courses, from EAFIT and Imperial College London, as references; not affiliated with the authors of those courses, see `../NOTICE.md`). I wrote the script myself; it contains no notebooks, code, data or assignments from those two courses.

```text
wall |--[k1]--o--[k2]--o--[k3]--o  --> F
     1        2        3        4      (node numbers)
```

Three springs in a chain. Node 1 is pinned to the wall, and node 4 is pulled to the right with F. Defaults: k1 = 30, k2 = 20, k3 = 60 N/mm, F = 60 N. Units: force in N, displacement in mm, k in N/mm.

## 1. How to run

```bash
python3 springs_e01.py
```

It finishes in under a second. The script follows the order of the video and prints the matrix at every step:

1. A unit check (K times u has the same unit as f: N);
2. Each spring's own 2×2 stiffness matrix, plus one matrix-times-vector check. The matrix gives "the forces the outside must put on the two end nodes to hold these displacements"; the spring's own pull on the nodes points the other way;
3. Adding the springs one by one into the 4×4 big matrix, printing after each one, and writing out which node's force balance each row is;
4. Does moving the whole chain 1 mm need a force? (No.) The 4×4 only has the three springs in it; the wall is not in yet. Without the wall's force, the outside forces add up to 60 N and the equations have no solution; with the wall's force, once there is one solution there are infinitely many (shift the whole chain once more);
5. Pin node 1: cross out row 1 and column 1, solve the remaining 3×3, check it by hand, and find the force from the wall;
6. Make the middle spring twice as stiff (20 → 40 N/mm), redo it, and list the cells of the big matrix that changed.

The last lines of the output should be:

```text
cells that changed: 4 of 16 -> (2,2) 50->70 (2,3) -20->-40 (3,2) -20->-40 (3,3) 80->100
displacements [mm]  A: 0  2  5  6   B: 0  2  3.5  4.5
nodes whose displacement changed: [3, 4]
```

The full output is kept in the course repository at `experiments/E01/results/springs_e01.txt` (every number in the video comes from there). Each case (A is the original, B is after the middle spring gets stiffer) has two `PASS` lines; the script checks them itself: `K u = f` holds on the nodes that are not fixed, and the displacements by hand match the ones the program solves for.

Other options:

- `--k K1 K2 K3`: change the k of the three springs (N/mm).
- `--force F`: change the pull on node 4 (N).
- `--k2-new X`: in the comparison, replace the middle spring with X (default: twice K2).

## 2. Dependencies

- The output above comes from Python 3.13.2 and NumPy 2.3.1 (2026-11-15). Only `numpy.linalg.solve` and `matrix_rank` are used, so any NumPy from 1.24 on should work [to be checked: only run on 2.3.1].
- No plots, no matplotlib.

## 3. Assumptions and exceptions

In the video a result carries only its main assumption; the rest are here.

- **The springs are linear**: force is proportional to stretch, and k is a constant. A real spring pulled too far, or a rubber band, does not meet this, and the equations no longer have the shape `K u = f`.
- **At rest** (said together with "linear" in the video): force balance only holds once the nodes stop moving, so there is no acceleration term. When things move there is one more matrix, tied to mass; it is only needed later, for transient heat and vibration.
- **The springs all lie on one line and only move along it**: for bars placed at an angle, each one's stiffness matrix also has to be rotated to its direction; that comes with trusses.
- **"Changing one spring only touches 4 cells"**: because each node has one unknown (how far it moves to the right) and a spring joins only two nodes, 2 × 2 = 4; it also assumes the connections stay the same and only this spring's k changes. Later elements join more nodes, so one element touches more cells: with one unknown per node (temperature, say), a three-node triangle touches 3 × 3 = 9 cells; in 2D elasticity each node has two unknowns, so a three-node triangle is 6 × 6, up to 36 cells. "Only the cells where its own nodes cross" stays true.
- **The displacement of node 2 does not change**: this is a property of this chain. The force is only applied at the end, so every spring carries the same F, and node 2 depends only on the first spring. With a force on a middle node, or springs joined into a network, this is no longer so. The hand calculation's "every spring carries F" also only holds in this case.
- **Fixing one node is enough**: this needs the chain to be unbroken and every spring's k to be greater than 0 (k3 = 0 in section 4 is the counterexample). For a chain like this on a straight line, "the whole chain shifts together" is the only way to move without effort, and pinning one point removes it. A body in a plane has three such ways; that comes with elasticity.
- **How to fix it**: here the row and the column are crossed out, which is one convenient way to handle u1 = 0. There are other ways (keep the row and column and change the diagonal, or hold the node with a very stiff spring); they come with boundary conditions.
- **Pinned at a nonzero displacement**: if node 1 is not pinned at 0 but pushed to a known position u1 = d, column 1 does not give 0. First move this column times d to the right side (subtract the cell of K times d from the right side of each equation), then cross out the row and column.
- **A continuous body also leads to `K u = f`**: the springs in this episode are separate pieces to begin with; they are not a finite element model of a continuous body, only the smallest example for seeing "once it is split into elements, how to assemble and how to solve". How a continuous bar is split into elements, and where each element's stiffness matrix comes from, starts in the next episode.

## 4. Change it and play

Cut the third spring, that is, k3 = 0:

```bash
python3 springs_e01.py --k 30 20 0
```

Think about two things before you run it:

1. Which cells of the 4×4 big matrix become 0?
2. With node 1 still pinned to the wall, can you still solve for the displacements? Why?

<details><summary>Check your answer</summary>

```text
  node 3: -20 u2 +20 u3 = 0
  node 4: 0 = 60
...
  reduced K has rank 2 of 3: still no unique answer.
```

Of the 4 cells the third spring used to occupy, (3,3), (3,4), (4,3), (4,4), its share is gone: (3,4), (4,3), (4,4) become 0, and (3,3) keeps only the 20 from the second spring. The row of node 4 becomes "0 = 60": node 4 is cut off from the chain, the 60 N pulling it is held by no spring, and this equation cannot hold. Pinning node 1 only holds the part connected to the wall; it cannot hold the cut-off node 4. To solve it, node 4 also needs something holding it.

</details>
