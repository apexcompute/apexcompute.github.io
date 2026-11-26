> **Watch and try it:** the video, a guess-first question and the interactive figures for this episode are on [the episode page](https://apexcompute.github.io/courses/finite-elements/E03/).

# E03 materials: a heated bar, written as a finite element program

Finite Elements from Scratch (I used two open courses, from EAFIT and Imperial College London, as references; not affiliated with the authors of those courses, see `../NOTICE.md`). I wrote the script myself; it contains no notebooks, code, data or assignments from those two courses; the data structures and function interfaces are my own.

```text
   20 °C |o-----o-----o-----o-----o| 20 °C        n = 4: nodes 1 … 5, elements 1 … 4
        x = 0                  x = 4 cm
```

The same bar as last episode (E02): aluminum alloy, 4 cm long, cross-section 1 cm², thermal conductivity k = 200 W/(m·K); the whole bar heats evenly, 80 W in all (q = 2000 W/m per meter); both end temperatures fixed at 20 °C. Last episode worked it on paper with two elements, up to T2 = 40 °C; this episode extends it to n elements and writes it as a program.

| Parameter | Default | Command line |
|---|---|---|
| Bar length | 4 cm | `--length` |
| Cross-section area | 1 cm² | `--area` |
| Thermal conductivity | 200 W/(m·K) (order of magnitude for aluminum alloy) | `--k` |
| Heat made by the whole bar | 80 W, even | `--power`; `--source middle` heats only the middle half (same total power) |
| End temperatures | 20 °C, 20 °C | `--t-left`, `--t-right` |
| Elements in the step-by-step pass | 4 | `--n` |

## 1. How to run

```bash
python3 bar_e03.py
```

It finishes in under a second. The script first does a unit check, then prints everything step by step with 4 elements:

1. **Mesh**: where the 5 nodes are (0, 1, 2, 3, 4 cm), and which two nodes each of the 4 elements joins;
2. **One element**: h = 1 cm, the small table is kA/h times [[1, −1], [−1, 1]], kA/h = 2 W/K;
3. **Assembly**: add the elements one at a time into the 5×5 big table K, printing after each one; each element's 20 W of heat is shared half to each end node, adding up to f = (10, 20, 20, 20, 10) W;
4. **Both end temperatures known**: columns 1 and 5 times 20 °C move to the right side, then rows and columns 1 and 5 are crossed out, leaving 3×3;
5. **Solve**: T = 20, 35, 40, 35, 20 °C; bring back the two crossed-out rows: 40 W leaves through each end, 80 W in total, equal to the heat made.

Then compare to the exact solution T(x) = 20 + 5 x (4 − x) (x in cm): the same at the nodes, and at the middle of each element the finite element answer is 1.25 K low. Finally it computes n = 2, 4, 8, 16, 32 and lists the largest error at the nodes and at element middles. The last lines of the output should be:

```text
      n   h [cm]   largest |FEM - exact| [K]       ratio to the row above
                   at nodes   at element middles   (element middles)
      2        2          0                    5   -
      4        1          0                 1.25   0.2500
      8      0.5          0               0.3125   0.2500
     16     0.25          0             0.078125   0.2500
     32    0.125          0            0.0195312   0.2500
```

The full output is kept in the course repository at `experiments/E03/results/bar_e03.txt` (every number in the video comes from there). Differences below 1e-9 (rounding noise, such as 1e-14) are printed as 0.

In the program, nodes and elements are counted from 0 (the Python habit); everything printed has 1 added.

## 2. Dependencies

- The output above comes from Python 3.13.2 and NumPy 2.3.1 (2026-11-16); the terminal in the video ran in a container with Python 3.12.3 and NumPy 1.26.4, with the same output word for word. Only `numpy.linspace`, `numpy.linalg.solve` and array arithmetic are used.
- No plots, no matplotlib.

## 3. Assumptions and exceptions

In the video a result carries only its main assumption; the rest are here.

- **"The same as the exact solution at the nodes" only holds for this kind of example**: 1D, linear hats; the bar is connected and kA is greater than 0; kA is constant in each element; both end temperatures are given; each element's heat is shared exactly to its end nodes by the hats (`element_heat`). Why, in three steps: ① take the exact solution's values at the nodes and join them into a candidate broken line; ② the row of a middle node i comes from hat i, which covers only the two elements on either side; in one element the hat's slope and kA are constant, so the conduction side only sees the temperature difference across the element, and the candidate broken line and the exact curve have the same ends, so this side is the same; the heat side is integrated exactly by the hats, so it is the same too; the exact solution satisfies the weak form (E02), so the candidate values satisfy these equations (the `they fit` line of the script); ③ these equations have only one solution, so the program's answer must be it. Change any one of the following, and the nodes are no longer sure to match:
  - The heat is shared inexactly. `python3 bar_e03.py --source middle --share midpoint --n 3`: only look at the heat at the very middle of the element and treat the whole element as having it. The middle of element 1 does not heat, but the stretch to its right actually does, and that heat is left out; in the output, nodes 2 and 3 are 7.8 K below the exact solution (`experiments/E03/results/bar_e03_share_midpoint.txt`).
  - kA varies inside an element (for example the cross-section keeps getting thinner, or the material changes in the middle of the element).
  - 2D, 3D.
- **"The finite element answer is low in the middle of an element"**: in an element, the finite element answer is a straight line joining its two ends, while the exact solution bulges upward where there is heat (a parabola); the straight line sits on the chord, so it is low. Where there is no heat the exact solution is itself a straight line, and the finite element answer matches it there, even at element middles (try `--source middle`).
- **"Double the elements, and the error at element middles drops to a quarter"**: in this example (even heating, elements of equal length), the error at element middles is exactly q h² / (8 kA): 5 K at h = 2 cm, and each time h is halved it drops to a quarter. With uneven heating, elements of different lengths, or looking at heat flow instead of temperature, it drops at a different rate; that is looked at systematically later, in "how do you know it's right".
- **How the temperatures are fixed**: here it is "the known columns times the temperature move to the right side, then the end rows and columns are crossed out". Another common way keeps the rows and columns and changes that row to "T = known value" (the matrix keeps its size); the 2D chip uses that way.
- **Heat leaving through the ends**: bring back the two crossed-out rows, and `f − K T` is the heat leaving through the ends. In this example it is the same as in the exact solution (40 W each).
- **"This is called the Galerkin method"**: the hats that multiply the unknown middle temperatures are exactly the ones used as test functions (both end temperatures are given, so the two end hats are not used as test functions; they only fill in the small tables and read out the heat leaving through the ends). Use other test functions (for example the finite volume "box" in the E02 side note) and it is a different method, with different equations. The video only gives the name; it does not say it is "the best" or has "the smallest error". Claims like that need more assumptions and come later, with errors.

## 4. Change it and play

Heat only the middle half (1 cm to 3 cm; that stretch heats twice as strongly as before, still 80 W in total):

```bash
python3 bar_e03.py --source middle
```

Think about two things before you run it:

1. With 4 elements, do the nodes still match the exact solution?
2. At the middles of the 4 elements, in which elements does the finite element answer match the exact solution?

<details><summary>Check your answer</summary>

```text
  at the nodes:
      node   x [cm]   FEM [°C]   exact [°C]   FEM - exact [K]
         1        0         20           20                 0
         2        1         40           40                 0
         3        2         50           50                 0
         4        3         40           40                 0
         5        4         20           20                 0
  at the middle of each element:
   element   x [cm]   FEM [°C]   exact [°C]   FEM - exact [K]
         1      0.5         30           30                 0
         2      1.5         45         47.5              -2.5
         3      2.5         45         47.5              -2.5
         4      3.5         30           30                 0
```

The nodes still match (this example meets the conditions in section 3: kA is constant in each element, the edges of the heated stretch fall exactly on nodes 2 and 4, and the heat is shared exactly). Elements 1 and 4 do not heat; the exact solution is a straight line there to begin with, the finite element line lies on it, and the middle is 0 too; elements 2 and 3 heat, the exact solution bulges upward, the straight line sits on the chord, 2.5 K low. Where the error is depends on where the exact solution bends.

</details>
