> **Watch and try it:** the video, a guess-first question and the interactive figures for this episode are on [the episode page](https://apexcompute.github.io/courses/finite-elements/E04/).

# E04 materials: how to guess the temperature inside an element (shape functions; are more nodes always better?)

Finite Elements from Scratch (I used two open courses, from EAFIT and Imperial College London, as references; not affiliated with the authors of those courses, see `../NOTICE.md`). I wrote the script myself; it contains no notebooks, code, data or assignments from those two courses; the data structures and function interfaces are my own.

```text
 even heating (E02, E03):  20 °C |================================| 20 °C      80 W over the whole bar
 heater (this episode):    20 °C |--------------[##]--------------| 20 °C      all 80 W in 1.8–2.2 cm
                                x = 0          1.8 2.2         x = 4 cm
```

The same aluminum bar as E02 and E03: 4 cm long, cross-section 1 cm², k = 200 W/(m·K), both ends at 20 °C, 80 W of heat in all. This episode looks at two kinds of heating: the whole bar heating evenly (the exact temperature is a parabola), and all 80 W packed into a 0.4 cm "heater" in the middle (a straight line outside it, a dome inside it, 58 °C at the hottest).

This episode mostly looks at **shapes**: the node temperatures are first taken as exact values and joined by shape functions, and we see how far the shape is from the true temperature. Only section 8 lets the equation set the coefficients (the same weak form as E03), for comparison.

| Parameter | Default | Command line |
|---|---|---|
| Bar length | 4 cm | `--length` |
| Cross-section area | 1 cm² | `--area` |
| Thermal conductivity | 200 W/(m·K) | `--k` |
| Heat | 80 W | `--power` |
| End temperatures | 20 °C | `--t-end` |
| Heater center, width | 2 cm, 0.4 cm (a width equal to the bar length means the whole bar heats evenly) | `--center`, `--width` |
| Degree of the single polynomial (= number of linear elements) | 10 | `--degree` |

## 1. How to run

```bash
python3 shape_e04.py
```

It finishes in under a second. It first does a unit check, then prints nine sections:

1. The two shape functions in one linear element (element 2 of E03: nodes at 1 and 2 cm, temperatures 35 and 40 °C; 0.5 each at 1.5 cm, joined into 37.5);
2. The three shape functions of a quadratic element (0–2 cm, nodes at 0, 1, 2 cm): 0.375, 0.75, −0.125 at 0.5 cm, adding up to 1;
3. With even heating and the same number of nodes, how far off linear and quadratic elements are;
4. The exact temperature with the heater: 40 W leaves through each end, 20 degrees per centimeter outside the heater, 56 °C at its edges, 58 °C at the top; the temperatures at 11 evenly spaced nodes;
5. The same values at the 11 nodes, the largest error of three ways of joining them: 10 linear elements 1.125 K, one evenly spaced degree-10 polynomial 14.25 K, one degree-10 polynomial on Chebyshev nodes 1.0 K;
6. Node counts from 3 to 17, the largest error of the three ways;
7. Raise only the middle node by 1 degree: linear elements only move two elements, while the degree-10 polynomial moves by 6.15 degrees in the first element; the largest and smallest values of each of the evenly spaced degree-10 shape functions;
8. Let the equation set the coefficients (one element, degree 2 … 10): at degree 10 the largest error is 0.859 K and the ends don't swing; 10 linear elements really solved, matching the exact values at the nodes; the last line is the condition number of the element small table built from degree-10 shape functions (evenly spaced 1.76e4, Chebyshev 65.3);
9. 2D: the shape functions of one triangle and one square, their values at a few points.

The output is kept in the course repository at `experiments/E04/results/shape_e04.txt` (every number in the video comes from there). Differences below 1e-9 (rounding noise) are printed as 0.

## 2. Dependencies

- The output above comes from Python 3.13.2 and NumPy 2.3.1 (2026-11-16). NumPy only (arrays, `linalg.solve`, `polynomial.legendre`).
- No plots, no matplotlib.

## 3. Assumptions and exceptions

In the video a result carries only its main assumption; the rest are here.

- **"One evenly spaced degree-10 polynomial swings at the ends, off by up to 14 degrees"**: what is compared is **the shape joined through the true values at the nodes** (in mathematics, interpolation). It takes three conditions together to swing this badly: evenly spaced nodes; one single polynomial for the whole bar; and all the bending of the temperature squeezed into the middle 0.4 cm (the heater: within that short stretch the slope goes from rising 20 degrees per centimeter to falling 20 degrees per centimeter). Take one away and it changes:
  - Nodes dense at the ends (Chebyshev points, x_j = L/2 − (L/2) cos(π j / p), j = 0 … p): the same degree 10, largest error 1.0 K (section 5);
  - A wider heater, a smoother temperature: 1.17 K with `--width 1.6`; 0 with the whole bar heating evenly (`--width 4`), because the exact temperature is itself a parabola, which a degree-10 polynomial can represent exactly.
- **"Let the equation set the coefficients and it doesn't swing"**: when finite elements really compute, the coefficients are not joined through true values; they are set by the equation (the weak form). The same bar, one degree-10 element: the polynomial set by the equation is off by at most 0.859 K (section 8). On the same straight element, with the same complete space of degree-10 polynomials, exact integrals and exact arithmetic, changing the nodes only changes how the function is put together; the function set by the equation stays the same. The section 8 script doesn't use nodes at all: it builds from a set of Legendre polynomials that are 0 at both ends. So "high degree is unstable" is about **high-degree interpolation on evenly spaced nodes**, not high-degree finite elements themselves. The polynomial set by the equation is the same function whichever shape functions write it and wherever it is evaluated, so plotting it or reading values from it won't swing again. Evenly spaced nodes still matter in two places: ① things like initial temperatures, material data and measured data often have to be joined into a shape through known points, and evenly spaced high-degree joining swings; ② the system built from evenly spaced high-degree shape functions amplifies rounding errors much more on a computer: in the last line of section 8, the condition number at degree 10 is 1.76e4, with Chebyshev nodes 65.3, 270 times apart. The nodes that high-degree finite elements actually use are also of the dense-at-the-ends kind. If the nodes are also used to set geometry, coefficients, loads or numerical integration, changing the nodes is more than changing how the function is put together, and the result may change too.
- **"The broken line of 10 linear elements is the finite element solution"**: only holds in 1D examples of the E03 kind (kA constant in each element, both end temperatures given, each element's heat shared exactly by the hats). The heater edges at 1.8 and 2.2 cm fall inside elements; the script integrates the overlap separately, so the sharing is still exact (section 8, E03 README section 3).
- **"Why it swings at the ends"**: the video explains it with "raise one middle node" and "the middle node's shape function shoots up to 6.15 in the gaps near the ends", which shows how sensitive one evenly spaced polynomial is. In full, the 14.25 K is the result of 11 shape functions added together. A comparison (`experiments/E04/results/crosscheck_e04.txt` line 6): replace the dome with a pointed top of two straight lines (heater width going to 0), and the degree-10 polynomial through the same 11 points is off by up to 26.5 K; the dome is 2 K lower than the pointed top only at the middle node, and that one point alone moves the curve by −12.3 K at 0.119 cm (where the middle node's shape function is about 6.15). Why, with evenly spaced nodes, it bulges higher the closer it gets to the ends comes from the factor "product of all (x − node)" in the interpolation error formula: with even spacing it is largest at the ends. The video doesn't cover this formula.
- **"Quadratic shape functions can be negative"**: at the nodes they are still 1 and 0, and the three add up to 1 everywhere, so when the three nodes are equally hot, the whole element joined from them is equally hot too. Every Lagrange shape function set has this "adds up to 1" property. But it doesn't guarantee the joined temperature stays between the node temperatures: between nodes it may still be hotter than the hottest node or colder than the coldest (the evenly spaced degree 10 in section 5 is an example).
- **"With even heating one quadratic element is exact"**: the exact temperature is itself a parabola (three points fix a parabola); letting the equation set the coefficients is exact too (the degree-2 line in section 8 is for the heater, not for even heating; for even heating with the equation setting the coefficients, see `--width 4`: 0 error at degree 2).
- **2D** (the video only covers linear triangles): the three shape functions of a linear triangle are what mathematics calls "barycentric coordinates"; on an edge, the shape function of the third corner is 0, so when two triangles share an edge the temperature along it is the same straight line, and they fit together without a seam. The bilinear shape functions of a square are products of 1D straight lines in the two directions; for corner 1 (bottom left), for example, it is (1 − x/2)(1 − y/2); at the very center all four are 1/4, so with corners at 30, 60, 90, 40 °C the center is 55 °C (section 9); along an edge, again only the two corners of that edge count. Slanted quadrilaterals come next episode.
- **Chebyshev points and the Runge phenomenon**: the video says these two names only once, without deriving them.

## 4. Change it and play

Let the whole bar heat evenly (as in E02, E03):

```bash
python3 shape_e04.py --width 4
```

Think about two things before you run it:

1. Does one evenly spaced degree-10 polynomial still swing now?
2. How far off are 10 linear elements at most?

<details><summary>Check your answer</summary>

```text
[5] the same 11 node values, connected three ways
                                         largest |diff| [K]   at x [cm]   curve there [°C]   exact there [°C]
  10 linear elements                                    0.2         0.2               23.6               23.8
  one degree-10 curve, equal spacing                      0           0                 20                 20
  one degree-10 curve, Chebyshev nodes                    0           0                 20                 20
```

No swing, not off at all: the exact temperature is a parabola, polynomials of degree 10 already include parabolas, and the one through the 11 points can only be the parabola itself. The 10 linear elements are off by 0.2 K, which is the element-middle error from E03, q h² / (8 kA), with h = 0.4 cm. Whether it swings depends on what the temperature itself looks like: with the same way of joining, a smooth temperature is fine; only a sharp bend in the temperature causes trouble.

</details>
