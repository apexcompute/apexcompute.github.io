> **Watch and try it:** the video, a guess-first question and the interactive figures for this episode are on [the episode page](https://apexcompute.github.io/courses/finite-elements/E02/).

# E02 materials: a bar that heats itself, worked by hand with the "weak form"

Finite Elements from Scratch (I used two open courses, from EAFIT and Imperial College London, as references; not affiliated with the authors of those courses, see `../NOTICE.md`). I wrote the script myself; it contains no notebooks, code, data or assignments from those two courses.

```text
  20 °C |==== element 1 =====|==== element 2 =====| 20 °C
       x = 0             x = 2 cm            x = 4 cm
       node 1             node 2              node 3
```

An aluminum alloy bar, length L = 4 cm, cross-section A = 1 cm², thermal conductivity k = 200 W/(m·K). The whole bar heats evenly, P = 80 W in all, that is q = 2000 W/m per meter. Both end temperatures are fixed at 20 °C. It is split into two elements, each h = 2 cm long.

The video writes no program; it is all pen and paper. This script checks every number of that work, so you can follow along while you watch.

## 1. How to run

```bash
python3 weak_e02.py
```

NumPy only; it finishes in a second or two. The output follows the order of the video, in steps 0–6:

0. Unit check (kA/h is in W/K, times a temperature gives W; q times a length is also W);
1. Integration by parts, a review: on 0 to 1 take v = x, u = x², and compute each side once (1 = 2 − 1);
2. The equation −kA T'' = q and its exact solution (40 °C at the middle, 35 °C at 1 cm from an end), and "why the two-piece broken line can't go into the original equation";
3. Use the middle hat N2 as the test function and get T2;
4. Each element's 2×2 small table [[1, −1], [−1, 1]] W/K, put together into 3×3, both end temperatures known; solve T2, then use rows 1 and 3 to get the heat leaving the ends;
5. Compare to the exact solution: at the nodes, at element midpoints, heat flow;
6. Side note: the finite volume "box" and the finite element "hat".

Every integral is done two ways: a hand formula (the area of a triangle) and numerical integration (the midpoint rule, cutting the bar into many small pieces); only when they agree does it print `PASS`. The last lines of the output should be:

```text
  heat flow by the broken line's slope: -20 W just left of x = 2 cm, 20 W just right of it (jumps by 40 W at the node)
  element 1 by the slope: 20 W in at one end, 20 W out at the other, but it makes 40 W inside -> not balanced element by element

summary: T1, T2, T3 = 20, 40, 20 °C
```

The full output is kept in the course repository at `experiments/E02/results/weak_e02.txt` (every number in the video comes from there).

## 2. Which step of the output each part of the video matches

| In the video | Output |
|---|---|
| The two heat parameters, 20 W made per centimeter | first three lines |
| Integration by parts, a review | step 1 |
| Heat balance of a thin slice, exact solution, the broken line won't go in | step 2 |
| T2 from the middle hat (element 1, element 2, the triangle area under the hat) | step 3 |
| Each element's small table, putting them together, heat leaving the ends | step 4 |
| Comparing to the exact solution | step 5 |
| Finite volume side note | step 6 |

## 3. Assumptions and exceptions

In the video each result carries only its main assumption; the rest are here.

- **"The broken line can't go into the original equation"**: the original equation −kA T'' = q needs the temperature to have a second derivative. Each piece of the broken line is straight, so its second derivative is 0; at the kink the slope changes suddenly and there is no second derivative. So the broken line can never satisfy the original equation point by point, whatever T2 is.
- **What the weak form asks for**: ∫ kA T' v' dx = ∫ q v dx, for every v that is 0 at both ends. It only uses first derivatives of T and v; a first derivative may jump at finitely many points, but must not be so large that the integral can't be computed. The other way round, if a T that has a second derivative satisfies the weak form for every such v, it satisfies the original equation (the video only states this, without proof; section 4.2 of the notes of reference A proves both directions).
- **The end term**: the extra term from integration by parts is the heat leaving the ends times the value of v at the ends. In this episode both end temperatures are fixed, and we take v to be 0 at both ends, so the term does not appear. If one end is given something other than a temperature (for example, no heat may leave there), the term stays; the episode on boundaries comes back to it.
- **Why only one hat**: with two elements and both end temperatures known, only one number of the broken line, T2, is left to find; the only hat that is 0 at both ends is the middle one, and the one equation it gives is enough. Using all three hats (step 4), the two extra equations carry the heat leaving the ends on the right side; those two numbers are not known beforehand, so they are set aside, and once T2 is solved they give the heat at the ends, just like the force from the wall in the last episode.
- **"Exactly equal to the exact value at the nodes" only in this example**: in 1D, for this equation, with k and A constant along the bar and the heat integrals done exactly, the two-piece broken line has the same values at the nodes as the exact solution (also for other heat distributions; try `--source middle`). In 2D this generally does not hold; if the integrals are done with an approximate formula, it may not hold either. Inside the elements they are not equal: at x = 1 cm the broken line gives 30 °C, the exact solution 35 °C. The next episode looks again with more elements.
- **"The small table is the same as a spring's"**: in 1D, with the temperature a straight line in each element and k and A constant in the element, the four numbers are kA/h × [[1, −1], [−1, 1]]. When k or A varies inside the element, the four numbers have to be integrated as ∫ kA Na' Nb' dx. The small tables of 2D and 3D elements are integrated the same way; they just no longer look like one spring.
- **"The heat is shared half to each end"**: only true when the element heats evenly. In general it is ∫ q Na dx, weighted by the hat; with `--source middle`, element 1 gives 10 W to node 1 and 30 W to node 2.
- **The broken line's slope is not the true heat flow**: in element 1 the broken line has the same slope everywhere, giving 20 W; the true heat flow drops linearly from 40 W at the left end to 0 at the middle, and equals 20 W only at the element midpoint. The heat leaving the ends is more accurate from rows 1 and 3 of step 4 (exactly 40 W in this example) than from the broken line's slope.
- **Finite volume side note**: the control volume (the "box") runs from x = 1 cm to 3 cm; its heat balance is written as "heat made in the box = heat leaving through its two faces", with the face heat from the broken line's slope. Seen as a weighted check, its test function is "1 inside the box, 0 outside", not a hat. With even heating, the two ways give the same equation in this example; when only the middle half heats (`--source middle`), the box weighs 80 W and the hat 60 W, and T2 is 60 and 50 °C (exact 50 °C). This only shows "the two methods give different equations"; on a mesh this coarse it can't tell which is better. In finite volumes every box's heat balance adds up; in finite elements the balance element by element from the broken line's slope does not. That is how the two methods are by nature.

## 4. Try it

Change the right end temperature to 40 °C, keeping the left end at 20 °C:

```bash
python3 weak_e02.py --t-right 40
```

Before running it, work out T2 by hand with the equation from the video: 1 × (T2 − 20) + 1 × (T2 − 40) = 40.

<details><summary>Check your answer</summary>

T2 = 50 °C; the exact solution at x = 2 cm is also 50 °C, so the node matches again. The heat leaving the ends becomes 50 W at the left end and 30 W at the right end, still 80 W in total (output steps 4 and 5).

</details>

## 5. Other options

- `--power P`: heating power of the whole bar (W), default 80.
- `--t-left T`, `--t-right T`: end temperatures (°C), both 20 by default.
- `--source middle`: only the middle half (1 cm to 3 cm) heats, with the same total power (4000 W per meter on that stretch). The step 6 side note is only printed for the default even heating.

Dependencies: Python 3 (the author used 3.13), NumPy (the author used 2.3.1; needs 2.0 or later, for `np.trapezoid`).
