# Copyright (c) 2026 the course author. All rights reserved. For personal learning only.
"""E04: how to "guess" the temperature inside an element: shape functions, degrees of freedom; are more nodes always better?

The same bar as E02 and E03: aluminum alloy, length L = 4 cm, cross-section A = 1 cm², k = 200 W/(m·K),
P = 80 W of heat for the whole bar, both ends at 20 °C. This episode looks at two kinds of heating:
  uniform  the whole bar heats evenly (as in E02, E03); the exact temperature is a parabola;
  heater   all 80 W in one short stretch at the very middle (default 1.8–2.2 cm, 0.4 cm wide),
           like a small heating chip stuck to the middle of the bar.

    20 °C |------------[##]------------| 20 °C      heater: only [##] heats
         x = 0        1.8 2.2       x = 4 cm

This episode solves no new system; it mostly looks at "shapes": the node temperatures are first taken as exact values,
joined inside the element by shape functions into a shape, and we see how far it is from the true temperature.
Only the last section lets the equation set the coefficients (the same weak form as E03), for comparison.

Units: length cm (printed), temperature °C (differences K), heat W, kA in W·cm/K.
Shape functions have no units.

Usage:
  python3 shape_e04.py                 default: print all nine sections
  python3 shape_e04.py --width 4       heater 4 cm wide, that is, the whole bar heats evenly
  python3 shape_e04.py --width 1.6     a wider heater, smoother temperature
  python3 shape_e04.py --degree 6      7 nodes for both the single polynomial and the linear elements
All parameters are in the "parameters" block below; they can also be changed on the command line (python3 shape_e04.py --help).
NumPy only. The data structure is my own: the nodes are a list of x coordinates.
"""
import argparse

import numpy as np
from numpy.polynomial import legendre as LEG

# ---------------------------------------------------------------- parameters (change them here)
L_CM = 4.0            # bar length, cm
A_CM2 = 1.0           # cross-section area, cm²
K_COND = 200.0        # thermal conductivity, W/(m·K)
POWER = 80.0          # heat, W
T_END = 20.0          # temperature at both ends, °C
CENTER_CM = 2.0       # heater center, cm
WIDTH_CM = 0.4        # heater width, cm (4 means the whole bar heats)
DEGREE = 10           # degree of the single polynomial over the whole bar; the same number of linear elements, so both have DEGREE + 1 nodes
FINE = 4001           # how many points along the bar when looking for "the largest error" (one every 0.001 cm)


# ---------------------------------------------------------------- unit check
# Each quantity is stored as (power of W, power of cm, power of K).
DIM = {"k": (1, -1, -1), "A": (0, 2, 0), "x": (0, 1, 0), "P": (1, 0, 0),
       "T": (0, 0, 1), "N": (0, 0, 0)}


def dmul(*terms):
    return tuple(sum(t[i] for t in terms) for i in range(3))


def unit_check():
    kA = dmul(DIM["k"], DIM["A"])                        # W·cm/K
    slope = dmul(DIM["P"], tuple(-v for v in kA))        # P / kA: K/cm
    q = dmul(DIM["P"], tuple(-v for v in DIM["x"]))      # P / width: W/cm
    bend = dmul(q, tuple(-v for v in kA), DIM["x"], DIM["x"])   # q x² / kA: K
    shape_T = dmul(DIM["N"], DIM["T"])                   # shape function × node temperature
    ok = (kA == (1, 1, -1) and slope == (0, -1, 1) and bend == (0, 0, 1)
          and shape_T == DIM["T"])
    print("unit check: P/kA [K/cm], q x^2/kA [K], N * T [K]:",
          "OK" if ok else "FAIL")
    if not ok:
        raise SystemExit("unit mismatch")


# ---------------------------------------------------------------- exact temperature
def exact_T(x, p):
    """-kA T'' = q, both ends at T0. Inside the heater [a, b] q = P/w, outside q = 0.

    Integrate twice from left to right: T(x) = T0 + C x - Q2(x)/kA, Q2 is the heat integrated twice
    (a straight line outside the heater, a parabola inside), and C brings the right end back to T0 too.
    With the heater at the very middle, the slope outside it is (P/2)/kA: half the heat leaves through each end.
    """
    x = np.asarray(x, dtype=float)
    a, b = p["c"] - p["w"] / 2, p["c"] + p["w"] / 2
    q = p["P"] / p["w"]                           # heat per centimeter inside the heater, W/cm

    def Q2(xv):
        d_in = np.clip(xv, a, b) - a              # how far into the heater
        return q * d_in ** 2 / 2 + q * p["w"] * np.clip(xv - b, 0, None)
    C = Q2(p["L"]) / (p["kA"] * p["L"])
    return p["T0"] + C * x - Q2(x) / p["kA"]


# ---------------------------------------------------------------- shape functions
def shape(nodes, i, x):
    """Shape function of node i (Lagrange): 1 at its own node, 0 at the other nodes.

    N_i(x) = product of (x - x_j) / (x_i - x_j), over all the other nodes j.
    The numerator makes it 0 at the other nodes, the denominator makes it exactly 1 at its own node.
    """
    x = np.asarray(x, dtype=float)
    N = np.ones_like(x)
    for j, xj in enumerate(nodes):
        if j != i:
            N = N * (x - xj) / (nodes[i] - xj)
    return N


def one_curve(nodes, values, x):
    """One single polynomial: T(x) = each node temperature × its own shape function, added up."""
    return sum(v * shape(nodes, i, x) for i, v in enumerate(values))


def broken_line(nodes, values, x):
    """Many linear elements: in each element only the two shape functions of its two ends (straight lines)."""
    return np.interp(x, nodes, values)


def equal_nodes(n, L):
    return np.linspace(0.0, L, n + 1)


def cheb_nodes(n, L):
    """Dense at the ends, sparse in the middle (Chebyshev points, ends included)."""
    return L / 2 - L / 2 * np.cos(np.pi * np.arange(n + 1) / n)


def worst(err, x):
    """The largest error and where it is. When left and right are symmetric, take the left one (differences under 1e-9 count as equal)."""
    e = np.abs(err)
    k = int(np.flatnonzero(e >= e.max() - 1e-9)[0])
    return e[k], x[k]


def g(v, nd=6):
    """For printing: differences under 1e-9 are printed as 0 (rounding noise)."""
    v = float(v)
    if abs(v) < 1e-9:
        return "0"
    return f"{v:.{nd}g}"


# ---------------------------------------------------------------- let the equation set the coefficients
def by_equation(deg, p):
    """One element (the whole bar), degree deg: the coefficients are set by the weak form, not by joining exact values.

    Temperature = T_END + a combination of polynomials that are 0 at both ends; the test functions are the same set
    (as in E03, called Galerkin). The set is built from Legendre polynomials:
    phi_k = P_{k+1} - P_{k-1} (k = 1 … deg-1), 0 at both ends.
    All the integrals are polynomials, integrated exactly with numpy's polynomial integration.
    """
    L, kA = p["L"], p["kA"]
    q = p["P"] / p["w"]
    sa = 2 * (p["c"] - p["w"] / 2) / L - 1        # where the heater is on s ∈ [-1, 1]
    sb = 2 * (p["c"] + p["w"] / 2) / L - 1
    phis = [LEG.legsub(np.eye(k + 2)[k + 1], np.eye(k + 2)[k - 1])
            for k in range(1, deg)]
    m = len(phis)
    K = np.zeros((m, m))
    f = np.zeros(m)
    for i, a in enumerate(phis):
        da = LEG.legder(a) * 2 / L                # d/dx = (2/L) d/ds
        for j, b in enumerate(phis):
            db = LEG.legder(b) * 2 / L
            I = LEG.legint(LEG.legmul(da, db))
            K[i, j] = kA * (LEG.legval(1, I) - LEG.legval(-1, I)) * L / 2
        I = LEG.legint(a)
        f[i] = q * (LEG.legval(sb, I) - LEG.legval(sa, I)) * L / 2
    c = np.linalg.solve(K, f)

    def T(x):
        s = 2 * np.asarray(x, dtype=float) / L - 1
        return p["T0"] + sum(ci * LEG.legval(s, a) for ci, a in zip(c, phis))
    return T


def linear_fem(n, p):
    """n linear elements, really solved the E03 way (only for the comparison in section 8).

    Each element's small table is kA/h [[1, -1], [-1, 1]]; the heat is shared exactly by the two hats
    (where a heater edge falls inside an element, only the overlap is integrated); end temperatures moved right, crossed out.
    """
    x = equal_nodes(n, p["L"])
    a, b = p["c"] - p["w"] / 2, p["c"] + p["w"] / 2
    q = p["P"] / p["w"]
    K = np.zeros((n + 1, n + 1))
    f = np.zeros(n + 1)
    for e in range(n):
        xl, xr = x[e], x[e + 1]
        h = xr - xl
        K[e:e + 2, e:e + 2] += p["kA"] / h * np.array([[1, -1], [-1, 1]])
        lo, hi = max(a, xl), min(b, xr)
        if hi > lo:
            xm = (lo + hi) / 2
            f[e:e + 2] += q * (hi - lo) * np.array([(xr - xm) / h, (xm - xl) / h])
    rhs = f - (K[:, 0] + K[:, -1]) * p["T0"]
    T = np.full(n + 1, p["T0"])
    T[1:-1] = np.linalg.solve(K[1:-1, 1:-1], rhs[1:-1])
    return x, T


def stiffness_cond(nodes, kA):
    """Build one element's conduction small table from the shape functions of these nodes (ends dropped) and return its condition number.

    A large condition number means rounding errors get amplified a lot when solving these equations (the exact solution is the same, but harder to compute accurately on a computer).
    The shape functions are numpy polynomials (built from their zeros at the other nodes), integrated with a 12-point Gauss rule (exact for
    the polynomials here).
    """
    P = np.polynomial.Polynomial
    n = len(nodes) - 1
    s, w = LEG.leggauss(12)
    a, b = nodes[0], nodes[-1]
    xg = (a + b) / 2 + (b - a) / 2 * s
    wg = (b - a) / 2 * w
    dN = []
    for i in range(1, n):
        Ni = P.fromroots(np.delete(nodes, i))
        Ni = Ni / Ni(nodes[i])
        dN.append(Ni.deriv()(xg))
    K = np.array([[kA * np.sum(wg * di * dj) for dj in dN] for di in dN])
    return np.linalg.cond(K)


# ================================================================ printing
def section(k, title):
    print()
    print(f"[{k}] {title}")


def part1():
    section(1, "linear shape functions in one element "
               "(E03 element 2: nodes at 1 and 2 cm, T = 35, 40 °C)")
    nodes = np.array([1.0, 2.0])
    print("    x [cm]   N_left   N_right   sum   35 N_left + 40 N_right")
    for x in (1.0, 1.25, 1.5, 1.75, 2.0):
        a, b = shape(nodes, 0, x), shape(nodes, 1, x)
        print(f"  {x:8g} {g(a):>8} {g(b):>9} {g(a + b):>5}   {g(35 * a + 40 * b):>8}")
    print("  (E03: FEM 37.5 at 1.5 cm, exact 38.75)")


def part2(p):
    section(2, "quadratic shape functions on 0-2 cm (nodes 0, 1, 2 cm; "
               "T = 20, 35, 40 from the exact curve)")
    nodes = np.array([0.0, 1.0, 2.0])
    vals = [20.0, 35.0, 40.0]
    print("    x [cm]   N_left    N_mid   N_right   sum   T (quadratic)   exact")
    pu = dict(p, w=p["L"], c=p["L"] / 2)
    for x in (0.0, 0.5, 1.0, 1.5, 2.0):
        N = [shape(nodes, i, x) for i in range(3)]
        T = sum(v * n for v, n in zip(vals, N))
        print(f"  {x:8g} {g(N[0]):>8} {g(N[1]):>8} {g(N[2]):>9} {g(sum(N)):>5}"
              f"   {g(T):>13} {g(exact_T(x, pu)):>7}")
    print("  N_left = (x-1)(x-2)/2,  N_mid = x(2-x),  N_right = x(x-1)/2   (x in cm)")


def part3(p):
    section(3, "uniform heating (whole bar, 80 W): same number of nodes, "
               "linear vs quadratic elements")
    pu = dict(p, w=p["L"], c=p["L"] / 2)
    xs = np.linspace(0, p["L"], FINE)
    Te = exact_T(xs, pu)
    print("   nodes   linear elements   largest |diff| [K]"
          "   quadratic elements   largest |diff| [K]")
    for nn in (3, 5, 9):
        ne = nn - 1
        xn = equal_nodes(ne, p["L"])
        e_lin = worst(broken_line(xn, exact_T(xn, pu), xs) - Te, xs)[0]
        nq = ne // 2
        e_q = 0.0
        for e in range(nq):                       # three nodes in each quadratic element
            loc = xn[2 * e:2 * e + 3]
            m = (xs >= loc[0]) & (xs <= loc[2])
            e_q = max(e_q, np.abs(one_curve(loc, exact_T(loc, pu), xs[m])
                                  - Te[m]).max())
        print(f"  {nn:6d} {ne:17d} {g(e_lin):>20} {nq:20d} {g(e_q):>20}")


def part4(p):
    section(4, f"heater bar: {g(p['P'])} W in {g(p['c'] - p['w'] / 2)}-"
               f"{g(p['c'] + p['w'] / 2)} cm, ends {g(p['T0'])} °C")
    left = p["kA"] * (exact_T(1e-6, p) - p["T0"]) / 1e-6    # kA T'(0): heat leaving through the left end
    s = left / p["kA"]
    print(f"  left end gets {g(left, 4)} W, right end {g(p['P'] - left, 4)} W;"
          f"  left of the heater the slope is {g(left, 4)} / {g(p['kA'])}"
          f" = {g(s, 4)} K/cm")
    xa = p["c"] - p["w"] / 2
    xs = np.linspace(0, p["L"], FINE)
    k = int(np.argmax(exact_T(xs, p)))
    print(f"  T at the heater edge {g(xa)} cm: {g(exact_T(xa, p), 4)} °C;"
          f"  hottest at {g(xs[k])} cm: {g(exact_T(xs[k], p), 4)} °C")
    xn = equal_nodes(p["deg"], p["L"])
    print(f"  {len(xn)} equally spaced nodes (every {g(p['L'] / p['deg'])} cm), "
          "exact T there:")
    print("    x [cm] " + " ".join(f"{g(v):>5}" for v in xn))
    print("    T [°C] " + " ".join(f"{g(v):>5}" for v in exact_T(xn, p)))


def part5(p):
    n = p["deg"]
    section(5, f"the same {n + 1} node values, connected three ways")
    xs = np.linspace(0, p["L"], FINE)
    Te = exact_T(xs, p)
    xn = equal_nodes(n, p["L"])
    xc = cheb_nodes(n, p["L"])
    rows = [(f"{n} linear elements", broken_line(xn, exact_T(xn, p), xs)),
            (f"one degree-{n} curve, equal spacing",
             one_curve(xn, exact_T(xn, p), xs)),
            (f"one degree-{n} curve, Chebyshev nodes",
             one_curve(xc, exact_T(xc, p), xs))]
    print("                                         largest |diff| [K]   at x [cm]"
          "   curve there [°C]   exact there [°C]")
    for name, y in rows:
        e, x = worst(y - Te, xs)
        k = int(np.flatnonzero(xs == x)[0])
        print(f"  {name:<38} {g(e):>18} {g(x):>11} {g(y[k]):>18} {g(Te[k]):>18}")
    print("  (Chebyshev nodes: " + " ".join(f"{v:.3f}" for v in xc) + " cm)")


def part6(p):
    section(6, "more nodes = better?  largest |diff| [K]")
    xs = np.linspace(0, p["L"], FINE)
    Te = exact_T(xs, p)
    print("   nodes   linear elements   one curve, equal spacing"
          "   one curve, Chebyshev nodes")
    for nn in (3, 5, 7, 9, 11, 13, 15, 17):
        n = nn - 1
        xn, xc = equal_nodes(n, p["L"]), cheb_nodes(n, p["L"])
        a = worst(broken_line(xn, exact_T(xn, p), xs) - Te, xs)[0]
        b = worst(one_curve(xn, exact_T(xn, p), xs) - Te, xs)[0]
        c = worst(one_curve(xc, exact_T(xc, p), xs) - Te, xs)[0]
        print(f"  {nn:6d} {g(a, 4):>17} {g(b, 4):>26} {g(c, 4):>28}")


def part7(p):
    n = p["deg"]
    section(7, f"move one node: all {n + 1} nodes at 20 °C, "
               f"then the middle one ({g(p['L'] / 2)} cm) at 21 °C")
    xs = np.linspace(0, p["L"], FINE)
    xn = equal_nodes(n, p["L"])
    v = np.full(n + 1, 20.0)
    v[n // 2] = 21.0
    h = p["L"] / n
    far = (xs < p["L"] / 2 - h - 1e-9) | (xs > p["L"] / 2 + h + 1e-9)
    end = xs <= h + 1e-9
    for name, y in (("linear elements", broken_line(xn, v, xs)),
                    (f"one degree-{n} curve", one_curve(xn, v, xs))):
        d = y - 20.0
        print(f"  {name:<20} largest change away from the two middle "
              f"elements: {g(np.abs(d[far]).max()):>7} K;"
              f"  in the first element (0-{g(h)} cm): {g(d[end].max()):>7} K")
    print(f"  shape functions of the degree-{n} curve (equal spacing), "
          f"highest and lowest value on 0-{g(p['L'])} cm:")
    print("    node   x [cm]    max      min")
    for i in range(n + 1):
        N = shape(xn, i, xs)
        print(f"  {i + 1:6d} {g(xn[i]):>8} {g(N.max(), 4):>7} {g(N.min(), 4):>8}")
    mid = n // 2
    bumps = []
    for a, b in zip(xn[:-1], xn[1:]):            # the value farthest from 0 in each gap
        N = shape(xn, mid, np.linspace(a, b, 401))
        bumps.append(N[int(np.argmax(np.abs(N)))])
    print(f"  middle node ({mid + 1}), farthest from 0 in each gap, left to right:")
    print("   " + " ".join(f"{g(v, 4):>6}" for v in bumps))
    Nc = shape(cheb_nodes(n, p["L"]), mid, xs)
    print(f"  the same node with Chebyshev nodes: max {g(Nc.max(), 4)}, "
          f"min {g(Nc.min(), 4)}")


def part8(p):
    n = p["deg"]
    section(8, "coefficients from the equation instead (one element, "
               "Galerkin as in E03)")
    xs = np.linspace(0, p["L"], FINE)
    Te = exact_T(xs, p)
    print("   degree   largest |diff| [K]   at x [cm]")
    for deg in sorted({2, 4, 6, 8, n}):
        T = by_equation(deg, p)
        e, x = worst(T(xs) - Te, xs)
        print(f"  {deg:7d} {g(e, 4):>20} {g(x):>11}")
    x, T = linear_fem(n, p)
    dn = np.abs(T - exact_T(x, p)).max()
    e = worst(broken_line(x, T, xs) - Te, xs)[0]
    print(f"  for comparison, {n} linear elements solved as in E03: node values"
          f" off by {g(dn)} K,")
    print(f"  so the FEM line is the broken line of [5]: largest |diff| {g(e, 4)} K")
    ce = stiffness_cond(equal_nodes(n, p["L"]), p["kA"])
    cc = stiffness_cond(cheb_nodes(n, p["L"]), p["kA"])
    print(f"  degree-{n} element matrix built from the shape functions: condition number"
          f" {ce:.3g} (equal spacing), {cc:.3g} (Chebyshev nodes), ratio {ce / cc:.3g}")


def part9():
    section(9, "two dimensions: one triangle, one square (corners in cm)")
    print("  triangle (0,0) (2,0) (0,2):  N1 = 1 - x/2 - y/2,  N2 = x/2,  N3 = y/2")
    tri = lambda x, y: np.array([1 - x / 2 - y / 2, x / 2, y / 2])
    Tc = np.array([30.0, 60.0, 90.0])
    print("    point          N1       N2       N3     sum   T (corners 30, 60, 90)")
    for name, (x, y) in (("corner 1", (0, 0)), ("edge 1-2 mid", (1, 0)),
                         ("edge 2-3 mid", (1, 1)), ("centroid", (2 / 3, 2 / 3))):
        N = tri(x, y)
        print(f"    {name:<13} {g(N[0], 4):>6} {g(N[1], 4):>8} {g(N[2], 4):>8}"
              f" {g(N.sum()):>7} {g(N @ Tc):>8}")
    print("  on edge 1-2 (y = 0) N3 = 0: T there uses only corners 1 and 2")
    print("  square 0-2 x 0-2: N = (straight line in x) * (straight line in y)")
    sq = lambda x, y: np.array([(1 - x / 2) * (1 - y / 2), x / 2 * (1 - y / 2),
                                x / 2 * y / 2, (1 - x / 2) * y / 2])
    Ts = np.array([30.0, 60.0, 90.0, 40.0])
    print("    point          N1       N2       N3       N4     sum"
          "   T (corners 30, 60, 90, 40)")
    for name, (x, y) in (("edge 1-2 mid", (1, 0)), ("center", (1, 1)),
                         ("(1.5, 0.5)", (1.5, 0.5))):
        N = sq(x, y)
        print(f"    {name:<13} {g(N[0], 4):>6} {g(N[1], 4):>8} {g(N[2], 4):>8}"
              f" {g(N[3], 4):>8} {g(N.sum()):>7} {g(N @ Ts):>8}")


def params_from_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--length", type=float, default=L_CM, help="bar length cm")
    ap.add_argument("--area", type=float, default=A_CM2, help="cross-section area cm²")
    ap.add_argument("--k", type=float, default=K_COND, help="thermal conductivity W/(m·K)")
    ap.add_argument("--power", type=float, default=POWER, help="heat W")
    ap.add_argument("--t-end", type=float, default=T_END, help="temperature at both ends °C")
    ap.add_argument("--center", type=float, default=CENTER_CM, help="heater center cm")
    ap.add_argument("--width", type=float, default=WIDTH_CM,
                    help="heater width cm (equal to the bar length means the whole bar heats evenly)")
    ap.add_argument("--degree", type=int, default=DEGREE,
                    help="degree of the single polynomial (= number of linear elements)")
    a = ap.parse_args(argv)
    kA = a.k / 100 * a.area                      # W/(m·K) → W/(cm·K), times cm²
    p = dict(L=a.length, kA=kA, P=a.power, T0=a.t_end, c=a.center, w=a.width,
             deg=a.degree)
    if not (0 < a.width <= a.length and a.center - a.width / 2 >= -1e-12
            and a.center + a.width / 2 <= a.length + 1e-12):
        raise SystemExit("the heater must lie inside the bar")
    return a, p


def main(argv=None):
    _, p = params_from_args(argv)
    unit_check()
    print(f"bar: L = {g(p['L'])} cm, kA = {g(p['kA'])} W*cm/K "
          f"(= {g(p['kA'] / 100)} W*m/K), P = {g(p['P'])} W, "
          f"ends {g(p['T0'])} °C")
    part1()
    part2(p)
    part3(p)
    part4(p)
    part5(p)
    part6(p)
    part7(p)
    part8(p)
    part9()


if __name__ == "__main__":
    main()
