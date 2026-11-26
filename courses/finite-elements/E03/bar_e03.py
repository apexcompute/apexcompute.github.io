# Copyright (c) 2026 the course author. All rights reserved. For personal learning only.
"""E03: a bar that heats itself, both end temperatures fixed; compute the temperature with n linear elements and compare to the exact solution.

    20 °C |o-----o-----o-----o-----o| 20 °C        (what n = 4 looks like: nodes 1 … 5, elements 1 … 4)
         x = 0                    x = L = 4 cm

The same bar as E02: aluminum alloy, length L = 4 cm, cross-section A = 1 cm², thermal conductivity k = 200 W/(m·K);
the bar heats evenly, P = 80 W in all, that is q = P / L = 2000 W/m per meter; both end temperatures fixed at 20 °C.
Equation (1D steady heat conduction, the sides of the bar insulated):
    -kA T'' = q(x)      0 < x < L,      T(0) = T_LEFT,  T(L) = T_RIGHT
Units: length m (printed in cm), temperature °C (differences K), heat W, kA/h in W/K.

Five steps; the core is the six functions below (step 2 has two):
  1. make_mesh        node positions, and which two nodes each element joins
  2. element_table    2x2 small table of one element (E02, on paper)
     element_heat     heat made in one element, shared to its two nodes
  3. assemble         add each element into the big table K and right side f
  4. fix_ends         ends known: move known columns x T right, drop the ends
  5. solve            solve the system that is left
Then compare to the exact solution: at the nodes and at element middles.

Numbering: nodes and elements start at 0 (the Python habit); printed +1:
nodes 1 … n+1, elements 1 … n.

Usage:
  python3 bar_e03.py                   default: n = 4 printed step by step, then n = 2, 4, 8, 16, 32 compared to the exact solution
  python3 bar_e03.py --n 8             the step-by-step pass with 8 elements instead
  python3 bar_e03.py --source middle   only the middle half heats (same total power, like --source middle in E02)
  python3 bar_e03.py --share midpoint  a rough way to share the heat (README section 3: the nodes no longer match)
All parameters are in the "parameters" block below; they can also be changed on the command line (python3 bar_e03.py --help).
NumPy only. The data structures are my own: the nodes are a list of x coordinates, the elements a list of (left node, right node).
"""
import argparse

import numpy as np

# ---------------------------------------------------------------- parameters (change them here; defaults as in E02)
L_CM = 4.0            # bar length, cm
A_CM2 = 1.0           # cross-section area, cm²
K_COND = 200.0        # thermal conductivity, W/(m·K)
POWER = 80.0          # heat made by the whole bar, W
T_LEFT = 20.0         # fixed temperature at the left end, °C
T_RIGHT = 20.0        # fixed temperature at the right end, °C
N_SHOW = 4            # number of elements for the step-by-step pass
N_LIST = (2, 4, 8, 16, 32)   # element counts compared to the exact solution


# ---------------------------------------------------------------- unit check
# Each quantity is stored as (power of W, power of m, power of K). Temperature differences are in K (1 °C apart is 1 K apart).
DIM = {"k": (1, -1, -1), "A": (0, 2, 0), "h": (0, 1, 0), "T": (0, 0, 1), "q": (1, -1, 0)}


def dmul(*terms):
    return tuple(sum(t[i] for t in terms) for i in range(3))


def unit_check():
    inv_h = tuple(-x for x in DIM["h"])
    table = dmul(DIM["k"], DIM["A"], inv_h)        # the numbers in the small table: kA/h
    lhs = dmul(table, DIM["T"])                    # small table times temperature
    rhs = dmul(DIM["q"], DIM["h"])                 # heat in one element: q h
    ok = table == (1, 0, -1) and lhs == rhs == (1, 0, 0)
    print("unit check: kA/h [W/K] * T [K] -> W, q [W/m] * h [m] -> W:", "OK" if ok else "FAIL")
    if not ok:
        raise SystemExit("unit mismatch")


# ---------------------------------------------------------------- heat source
def heat_pieces(L, q_avg, source):
    """The heat source as a few constant pieces: [(from, to, q), ...], in m and W/m.

    uniform: the whole bar heats; middle: only L/4 to 3L/4 heats, same total power, so that stretch is 2 times as strong.
    """
    if source == "uniform":
        return [(0.0, L, q_avg)]
    return [(0.0, L / 4, 0.0), (L / 4, 3 * L / 4, 2 * q_avg), (3 * L / 4, L, 0.0)]


# ================================================================ the five steps of finite elements
# 1. mesh
def make_mesh(L, n):
    """n elements of equal length. x: positions of the n+1 nodes (m);
    elems: row e holds element e: (left node, right node)."""
    x = np.linspace(0.0, L, n + 1)
    elems = np.array([(e, e + 1) for e in range(n)])
    return x, elems


# 2. one element
def element_table(kA, h):
    """2x2 small table of one element: kA/h times [[1, -1], [-1, 1]], in W/K.
    Same shape: the table of one spring in E01."""
    return kA / h * np.array([[1.0, -1.0], [-1.0, 1.0]])


def element_heat(xl, xr, pieces):
    """Heat made in one element, shared to its two nodes by the hats, in W.

    left node gets ∫ q (xr - x)/h dx, right node gets ∫ q (x - xl)/h dx,
    over this element only. Where a heated stretch ends inside it, split,
    integrate piece by piece (constant times line: the midpoint is exact).
    With the same heat everywhere: q h / 2 and q h / 2, half each.
    """
    h = xr - xl
    fe = np.zeros(2)
    for (a, b, q) in pieces:
        lo, hi = max(a, xl), min(b, xr)          # overlap with this element
        if hi > lo:
            xm = 0.5 * (lo + hi)
            fe += q * (hi - lo) * np.array([(xr - xm) / h, (xm - xl) / h])
    return fe


def element_heat_midpoint(xl, xr, pieces):
    """A rough way to share heat (README section 3, the counterexample):
    use q at the element midpoint only, for the whole element."""
    xm, h = 0.5 * (xl + xr), xr - xl
    q = sum(qq for (a, b, qq) in pieces if a <= xm < b)
    return np.array([q * h / 2, q * h / 2])


# 3. assembly
def assemble(x, elems, kA, pieces, heat=element_heat, show=None):
    """One element at a time: compute its small table and end heats,
    and add them into K and f at its two nodes."""
    K = np.zeros((len(x), len(x)))
    f = np.zeros(len(x))
    for e, (i, j) in enumerate(elems):
        ke = element_table(kA, x[j] - x[i])
        fe = heat(x[i], x[j], pieces)
        K[i, i] += ke[0, 0]                      # only the 4 cells at i, j
        K[i, j] += ke[0, 1]
        K[j, i] += ke[1, 0]
        K[j, j] += ke[1, 1]
        f[i] += fe[0]                            # left share to i, right to j
        f[j] += fe[1]
        if show:                                 # demo print only, no effect
            show(e, i, j, ke, fe, K)
    return K, f


# 4. both end temperatures known
def fix_ends(K, f, t_left, t_right):
    """First and last columns times the known end temperatures go right.

    First/last rows also hold the unknown end heat flow: use them after solving.
    So cross out the end rows and columns; the middle nodes' equations stay.
    """
    rhs = f - K[:, 0] * t_left - K[:, -1] * t_right   # first col, last col
    return K[1:-1, 1:-1], rhs[1:-1]              # 1:-1 drops first and last


# 5. solve
def solve(n, p, share="hat", show=None):
    pieces = heat_pieces(p["L"], p["q"], p["source"])
    x, elems = make_mesh(p["L"], n)
    heat = element_heat if share == "hat" else element_heat_midpoint
    K, f = assemble(x, elems, p["kA"], pieces, heat, show)
    Kr, fr = fix_ends(K, f, p["t_left"], p["t_right"])
    T = np.zeros(len(x))
    T[0], T[-1] = p["t_left"], p["t_right"]
    T[1:-1] = np.linalg.solve(Kr, fr)            # middle-node temperatures
    return dict(x=x, elems=elems, K=K, f=f, Kr=Kr, fr=fr, T=T, pieces=pieces)


# ================================================================ for comparison
def heat_integrals(x, pieces):
    """Q1(x) = ∫0^x q (how much heat is made from the left end to x), Q2(x) = ∫0^x Q1. q is a few constant pieces, so this integrates exactly."""
    Q1 = Q2 = 0.0
    for (a, b, q) in pieces:
        if x <= a:
            break
        s = min(x, b) - a                 # length covered inside this piece
        Q2 += Q1 * s + 0.5 * q * s * s
        Q1 += q * s
    return Q1, Q2


def exact_solution(xs, p, pieces):
    """-kA T'' = q, both end temperatures known. Integrate twice from left to right: T(x) = T_LEFT + C x - Q2(x)/kA, C set by the right end temperature.

    A parabola where it heats, a straight line where it doesn't. With even heating and both ends at 20 °C it is 20 + 5 x (4 - x), x in cm.
    """
    L, kA = p["L"], p["kA"]
    C = (p["t_right"] - p["t_left"] + heat_integrals(L, pieces)[1] / kA) / L
    return np.array([p["t_left"] + C * xv - heat_integrals(xv, pieces)[1] / kA for xv in np.atleast_1d(xs)])


def end_heat(r):
    """Bring back the two crossed-out end rows: f - K T at the ends is the heat leaving the bar there (W, outward positive).

    At a middle node K T = f: the heat shared to that node is carried away exactly by the elements on both sides. At the ends they are not equal;
    the difference is the heat leaving through that end.
    """
    out = r["f"] - r["K"] @ r["T"]
    return out[0], out[-1]


def exact_end_heat(p, pieces):
    """Heat leaving through the two ends in the exact solution (W). Left end: kA T'(0); right end = total heat - left end."""
    L, kA = p["L"], p["kA"]
    C = (p["t_right"] - p["t_left"] + heat_integrals(L, pieces)[1] / kA) / L
    return kA * C, heat_integrals(L, pieces)[0] - kA * C


def compare(r, p):
    """At the nodes and at each element's middle: the finite element temperature and the exact solution. In an element the finite element answer is a straight line, so the middle is the average of its two ends."""
    x, T, elems = r["x"], r["T"], r["elems"]
    xm = 0.5 * (x[elems[:, 0]] + x[elems[:, 1]])
    Tfe_mid = 0.5 * (T[elems[:, 0]] + T[elems[:, 1]])
    return exact_solution(x, p, r["pieces"]), xm, Tfe_mid, exact_solution(xm, p, r["pieces"])


# ================================================================ printing
def cm(x_m):
    return f"{x_m * 100:g}"


def g(v):
    """Print a number: drop rounding noise (below 1e-9 counts as 0) and -0."""
    v = 0.0 if abs(v) < 1e-9 else round(float(v), 9)
    return f"{v:g}"


def show_matrix(title, a, first=1):
    """Print a matrix; rows and columns are labeled with node numbers (printed counting from first)."""
    print(title)
    print("          " + "".join(f"node{j}".rjust(8) for j in range(first, first + a.shape[1])))
    for i, row in enumerate(a):
        print(f"  node{i + first:<4d}" + "".join(g(v).rjust(8) for v in row))


def show_vector(title, v, first=1):
    print(title)
    print("          " + "".join(f"node{j}".rjust(8) for j in range(first, first + len(v))))
    print("          " + "".join(g(x).rjust(8) for x in v))


def show_add(e, i, j, ke, fe, K):
    print(f"\nadd element {e + 1} (node {i + 1} -> node {j + 1}): small table kA/h = {g(ke[0, 0])} W/K, "
          f"heat {g(fe[0])} W + {g(fe[1])} W")
    show_matrix("  K so far [W/K]:", K)


def report_steps(n, p, share):
    print("\n" + "=" * 72)
    print(f"step by step with n = {n} elements")
    print("=" * 72)
    x, elems = make_mesh(p["L"], n)
    print("\nstep 1: mesh (printed from 1; inside the program nodes and elements count from 0)")
    print("  node positions x [cm]:  " + "  ".join(f"{i + 1}:{cm(v)}" for i, v in enumerate(x)))
    print("  elements (left, right): " + "  ".join(f"{e + 1}:({i + 1},{j + 1})" for e, (i, j) in enumerate(elems)))
    h = x[1] - x[0]
    print(f"\nstep 2: one element, h = {cm(h)} cm, kA/h = {g(p['kA'])} / {g(h)} = {g(p['kA'] / h)} W/K")
    show_matrix("  small table kA/h * [[1,-1],[-1,1]] [W/K]:", element_table(p["kA"], h))
    print("\nstep 3: assembly, one element at a time")
    r = solve(n, p, share, show=show_add)
    show_vector("\nheat to each node f [W]:", r["f"])
    print(f"  sum of f = {g(r['f'].sum())} W = heat made in the whole bar")
    print(f"\nstep 4: T1 = {g(p['t_left'])} and T{n + 1} = {g(p['t_right'])} °C are known:")
    print(f"  move column 1 x {g(p['t_left'])} and column {n + 1} x {g(p['t_right'])} to the right side,")
    print(f"  then cross out rows and columns 1 and {n + 1}")
    show_matrix("  reduced K [W/K]:", r["Kr"], first=2)
    show_vector("  reduced right side [W]:", r["fr"], first=2)
    print("\nstep 5: solve")
    print("  T [°C]: " + "  ".join(f"T{i + 1} = {g(v)}" for i, v in enumerate(r["T"])))
    resid = np.abs(r["Kr"] @ r["T"][1:-1] - r["fr"]).max()
    print("  check K T = f on the inner nodes: max |K T - f| < 1e-9 W ->", "PASS" if resid < 1e-9 else "FAIL")
    lo, ro = end_heat(r)
    ok = abs(lo + ro - r["f"].sum()) < 1e-9 * abs(r["f"].sum())
    el, er = exact_end_heat(p, r["pieces"])
    print(f"  rows 1 and {n + 1} taken back: heat out of the left end {g(lo)} W, right end {g(ro)} W")
    print(f"  sum {g(lo + ro)} W = heat made ->", "PASS" if ok else "FAIL", f"  (exact: {g(el)} W, {g(er)} W)")

    print("\ncompare with the exact solution")
    Tex_nodes, xm, Tfe_mid, Tex_mid = compare(r, p)
    print("  at the nodes:")
    print("      node   x [cm]   FEM [°C]   exact [°C]   FEM - exact [K]")
    for i, (xv, a, b) in enumerate(zip(r["x"], r["T"], Tex_nodes)):
        print(f"  {i + 1:8d} {cm(xv):>8} {g(a):>10} {g(b):>12} {g(a - b):>17}")
    print("  at the middle of each element:")
    print("   element   x [cm]   FEM [°C]   exact [°C]   FEM - exact [K]")
    for e, (xv, a, b) in enumerate(zip(xm, Tfe_mid, Tex_mid)):
        print(f"  {e + 1:8d} {cm(xv):>8} {g(a):>10} {g(b):>12} {g(a - b):>17}")
    # put the exact solution's node values into the reduced equations: does every row hold?
    plug = np.abs(r["Kr"] @ Tex_nodes[1:-1] - r["fr"]).max()
    print(f"  put the exact temperatures at the nodes into the reduced equations: max |K T - f| = {g(plug)} W ->",
          "they fit" if plug < 1e-9 else "they do not fit")
    return r


def report_table(p, share, n_list):
    print("\n" + "=" * 72)
    print("compare with the exact solution for n = " + ", ".join(str(n) for n in n_list))
    print("=" * 72)
    print("      n   h [cm]   largest |FEM - exact| [K]       ratio to the row above")
    print("                   at nodes   at element middles   (element middles)")
    prev = None
    rows = []
    for n in n_list:
        r = solve(n, p, share)
        Tex_nodes, xm, Tfe_mid, Tex_mid = compare(r, p)
        en = float(np.abs(r["T"] - Tex_nodes).max())
        em = float(np.abs(Tfe_mid - Tex_mid).max())
        ratio = f"{em / prev:.4f}" if (prev and em > 1e-9) else "-"
        print(f"  {n:5d} {cm(p['L'] / n):>8} {g(en):>10} {g(em):>20}   {ratio}")
        prev = em
        rows.append((n, en, em))
    return rows


def params_from_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--length", type=float, default=L_CM, help="bar length [cm]")
    ap.add_argument("--area", type=float, default=A_CM2, help="cross-section [cm^2]")
    ap.add_argument("--k", type=float, default=K_COND, help="thermal conductivity [W/(m K)]")
    ap.add_argument("--power", type=float, default=POWER, help="heat made in the whole bar [W]")
    ap.add_argument("--source", choices=["uniform", "middle"], default="uniform",
                    help="uniform: the whole bar heats; middle: only L/4..3L/4 heats (same total)")
    ap.add_argument("--t-left", type=float, default=T_LEFT, help="left end temperature [°C]")
    ap.add_argument("--t-right", type=float, default=T_RIGHT, help="right end temperature [°C]")
    ap.add_argument("--n", type=int, default=N_SHOW, help="elements for the step-by-step run")
    ap.add_argument("--share", choices=["hat", "midpoint"], default="hat",
                    help="how the heat of an element is shared to its two nodes (README section 3)")
    a = ap.parse_args(argv)
    if a.n < 2:
        raise SystemExit("need at least 2 elements (one inner node)")
    L = a.length / 100
    p = dict(L=L, kA=a.k * a.area * 1e-4, q=a.power / L, source=a.source, t_left=a.t_left, t_right=a.t_right)
    return a, p


def main():
    a, p = params_from_args()
    unit_check()
    print(f"bar: L = {g(a.length)} cm, A = {g(a.area)} cm^2, k = {g(a.k)} W/(m K), kA = {g(p['kA'])} W m/K")
    print(f"heat: P = {g(a.power)} W, q = P / L = {g(p['q'])} W/m ({a.source}), shared to nodes by '{a.share}'")
    print(f"ends held at {g(p['t_left'])} and {g(p['t_right'])} °C")
    report_steps(a.n, p, a.share)
    report_table(p, a.share, N_LIST)


if __name__ == "__main__":
    main()
