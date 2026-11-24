# Copyright (c) 2026 the course author. All rights reserved. For personal learning only.
"""E02: a bar that heats itself, both end temperatures fixed; work it by hand with a two-piece broken line and the "weak form".

    20 °C |=====================|===================| 20 °C
          x = 0             x = 2 cm            x = 4 cm
          node 1             node 2              node 3
            ----- element 1 ----  ----- element 2 ----

An aluminum alloy bar, length L = 4 cm, cross-section A = 1 cm², thermal conductivity k = 200 W/(m·K).
Every piece of the bar heats evenly, P = 80 W for the whole bar, that is q = P / L = 2000 W/m per meter.
Both end temperatures are fixed at 20 °C. Units: length m, temperature °C (differences K), heat flow W.

The video writes no program, it is all pen and paper; this script checks every number of that work:
  0. unit check;
  1. integration by parts, a review: one concrete function, each side computed once;
  2. the equation -kA T'' = q and its exact solution; put the broken line into it and see why that fails;
  3. weak form: use the middle "hat" N2 as the test function and get T2;
  4. each element's 2x2 small table, put together into 3x3, both end temperatures known; solve T2 and the heat leaving the ends;
  5. compare to the exact solution: at nodes, at element midpoints, heat flow;
  6. side note: the finite volume "box" and the finite element "hat", once with even heating and once with uneven.
Every integral is done two ways: a hand formula (area of a triangle or trapezoid) and numerical integration (midpoint rule with many pieces);
only when they agree does it print PASS. NumPy only; the data structures are my own.

Usage:
  python3 weak_e02.py                          default case (the numbers in the video)
  python3 weak_e02.py --power 120              change the total heating power (W)
  python3 weak_e02.py --t-left 20 --t-right 40 different end temperatures (the exercise in README section 4)
  python3 weak_e02.py --source middle          only the middle half heats (same total power)
"""
import argparse
from fractions import Fraction

import numpy as np

# ---------------------------------------------------------------- default case (my own numbers)
L = 0.04        # m, bar length 4 cm
A = 1.0e-4      # m², cross-section 1 cm²
K_COND = 200.0  # W/(m·K), thermal conductivity of aluminum alloy (order of magnitude)
POWER = 80.0    # W, heating power of the whole bar
T_END = 20.0    # °C, fixed temperature at both ends
N_FINE = 400000  # number of pieces for numerical integration


# ---------------------------------------------------------------- unit check
# Each quantity is stored as (power of W, power of m, power of K).
UNITS = {"k": (1, -1, -1), "A": (0, 2, 0), "h": (0, 1, 0), "T": (0, 0, 1), "q": (1, -1, 0)}


def add(*us):
    return tuple(sum(c) for c in zip(*us))


def neg(u):
    return tuple(-c for c in u)


def unit_check():
    conductance = add(UNITS["k"], UNITS["A"], neg(UNITS["h"]))   # kA/h
    left = add(conductance, UNITS["T"])                            # kA/h * T
    right = add(UNITS["q"], UNITS["h"])                            # q * h
    ok = conductance == (1, 0, -1) and left == right == (1, 0, 0)
    print("unit check: kA/h [W/K] * T [K] -> W, q [W/m] * h [m] -> W:", "OK" if ok else "FAIL")
    if not ok:
        raise SystemExit("unit mismatch")


def verdict(ok):
    return "PASS" if ok else "FAIL"


def num_int(f, a, b, n=N_FINE):
    """Midpoint-rule numerical integration (only used to check the hand integrals)."""
    x = a + (np.arange(n) + 0.5) * (b - a) / n
    return float(np.sum(f(x)) * (b - a) / n)


def fmt(x, nd=6):
    x = round(float(x), nd)
    return f"{0.0 if x == 0 else x:g}"


# ---------------------------------------------------------------- 1. integration by parts, a review
def step1_by_parts():
    print("\nstep 1: integration by parts with one concrete function, on 0 <= x <= 1")
    print("  v(x) = x, u(x) = x^2, so v' = 1, u' = 2x, u'' = 2")
    # derivative of a product: (v u')' = v' u' + v u''; check it at one point, x = 1
    x0 = 1.0
    lhs_pr, rhs_pr = 4 * x0, 1 * 2 * x0 + x0 * 2
    print(f"  product rule check at x = 1: (v u')' = (2 x^2)' = 4x = {fmt(lhs_pr)};"
          f" v' u' + v u'' = 2x + 2x = {fmt(rhs_pr)} -> {verdict(lhs_pr == rhs_pr)}")
    # exact values with fractions
    I_vupp = Fraction(1)                 # ∫0^1 x * 2 dx = 1
    bracket = Fraction(2)                # [x * 2x] from 0 to 1 = 2 - 0
    I_vpup = Fraction(1)                 # ∫0^1 1 * 2x dx = 1
    n1 = num_int(lambda x: x * 2.0, 0, 1)
    n2 = num_int(lambda x: 1.0 * 2.0 * x, 0, 1)
    print(f"  left:  integral of v u''  = integral of 2x            = {I_vupp}"
          f"   (numerical {fmt(n1)})")
    print(f"  right: [v u'] from 0 to 1 = 1*2 - 0*0                  = {bracket}")
    print(f"         integral of v' u'  = integral of 2x            = {I_vpup}"
          f"   (numerical {fmt(n2)})")
    print(f"  {I_vupp} = {bracket} - {I_vpup} -> "
          f"{verdict(I_vupp == bracket - I_vpup and abs(n1 - 1) < 1e-9 and abs(n2 - 1) < 1e-9)}")
    print("  the derivative moved from u (two primes) onto v (one prime each);"
          " the price is the bracket term at the two ends")
    print("  if v were zero at both ends, the bracket would be 0")


# ---------------------------------------------------------------- 2. equation, exact solution, put the broken line in
def source_fn(kind, q_avg):
    if kind == "uniform":
        return lambda x: np.full_like(np.asarray(x, dtype=float), q_avg)
    # middle: only L/4 to 3L/4 heats, same total power, so that stretch is 2 times as strong
    return lambda x: np.where((np.asarray(x) >= L / 4) & (np.asarray(x) <= 3 * L / 4), 2 * q_avg, 0.0)


def exact_solution(kind, q_avg, kA, t_left, t_right):
    """Exact solution of -kA T'' = q (end temperatures given). Returns T(x) and heat flow Phi(x) = -kA T'(x) (positive to the right)."""
    if kind == "uniform":
        def T(x):
            x = np.asarray(x, dtype=float)
            return t_left + (t_right - t_left) * x / L + q_avg / (2 * kA) * x * (L - x)

        def Phi(x):
            x = np.asarray(x, dtype=float)
            return -kA * ((t_right - t_left) / L + q_avg / (2 * kA) * (L - 2 * x))
        return T, Phi
    # middle: three pieces, heat flow linear on each; the part from the end temperature difference is one more straight line
    qm = 2 * q_avg
    a, b = L / 4, 3 * L / 4
    lin = (t_right - t_left) / L          # slope from the end temperature difference

    def Phi0(x):                           # heat flow of the symmetric part (same temperature at both ends)
        x = np.asarray(x, dtype=float)
        mid = qm * (x - L / 2)
        return np.clip(mid, -qm * (b - a) / 2, qm * (b - a) / 2)

    def T0(x):                             # temperature of the symmetric part: integrate -Phi0/kA from 0
        x = np.asarray(x, dtype=float)
        out = np.empty_like(x)
        for i, xi in enumerate(np.atleast_1d(x)):
            s = np.linspace(0.0, xi, 2001)
            out.flat[i] = -np.trapezoid(Phi0(s), s) / kA if xi > 0 else 0.0
        return out

    def T(x):
        x = np.asarray(x, dtype=float)
        return t_left + lin * x + T0(np.atleast_1d(x)).reshape(x.shape)

    def Phi(x):
        return Phi0(x) - kA * lin
    return T, Phi


def step2_equation(kA, q_avg, t_left, t_right, kind):
    print("\nstep 2: the equation and its exact solution")
    print("  heat flowing to the right through a cross-section: Phi = -kA dT/dx  [W]")
    print("  balance of a thin slice: (out on the right) - (in on the left) = heat made inside")
    print("  -> -kA T'' = q,   T(0) = {}, T(L) = {} °C".format(fmt(t_left), fmt(t_right)))
    T, Phi = exact_solution(kind, q_avg, kA, t_left, t_right)
    xs_cm = [0, 1, 2, 3, 4]
    print("  exact temperature [°C] at x = 0, 1, 2, 3, 4 cm:",
          "  ".join(fmt(T(x / 100.0)) for x in xs_cm))
    if kind == "uniform":
        print(f"  exact solution: T(x) = {fmt(t_left)} + ({fmt((t_right - t_left) / L)}) x"
              f" + {fmt(q_avg / (2 * kA))} x (L - x),  x in m"
              f"  (with x in cm: the last term is {fmt(q_avg / (2 * kA) / 1e4)} x (4 - x))")
        # put it back to check: T'' is constant
        Tpp = -q_avg / kA
        print(f"  check: T'' = {fmt(Tpp)} K/m^2, -kA T'' = {fmt(-kA * Tpp)} W/m = q -> "
              f"{verdict(abs(-kA * Tpp - q_avg) < 1e-9)}")
    print("  exact heat flow [W] (to the right) at x = 0, 1, 2, 3, 4 cm:",
          "  ".join(fmt(Phi(x / 100.0)) for x in xs_cm))
    print(f"  heat leaving the left end {fmt(-Phi(0.0))} W, the right end {fmt(Phi(L))} W,"
          f" total {fmt(-Phi(0.0) + Phi(L))} W = power {fmt(q_avg * L)} W -> "
          f"{verdict(abs(-Phi(0.0) + Phi(L) - q_avg * L) < 1e-6)}")
    print("  try a broken line (two straight pieces, kink at x = 2 cm) in the equation:")
    q_txt = f"q = {fmt(q_avg)} W/m" if kind == "uniform" else f"q = {fmt(2 * q_avg)} W/m in the middle half"
    print(f"    inside each piece T'' = 0, so -kA T'' = 0, but {q_txt} -> not equal")
    print("    at the kink the slope jumps, T'' does not exist there")
    return T, Phi


# ---------------------------------------------------------------- 3, 4. weak form, hats, small tables
def hat(i, nodes):
    """Hat function of node i (from 1): 1 at its own node, 0 at the other nodes, straight lines in between."""
    def N(x):
        vals = np.zeros(len(nodes))
        vals[i - 1] = 1.0
        return np.interp(x, nodes, vals)
    return N


def hat_slope_on(i, e, nodes):
    """Slope of hat N_i in element e (node e to e+1)."""
    a, b = nodes[e - 1], nodes[e]
    h = b - a
    if i == e:
        return -1.0 / h
    if i == e + 1:
        return 1.0 / h
    return 0.0


def step3_weak_middle_hat(kA, q, nodes, t_left, t_right):
    print("\nstep 3: weak form with the middle hat N2 as the test function")
    print("  weak form: integral of kA T' v' dx = integral of q v dx,"
          " for every v that is 0 at both ends")
    h = nodes[1] - nodes[0]
    print(f"  two elements, h = {fmt(h * 100)} cm; kA/h = {fmt(kA / h)} W/K;"
          f" broken line T1 = {fmt(t_left)}, T2 = ?, T3 = {fmt(t_right)} °C")
    print("  N2: 0 at x = 0, 1 at x = 2 cm, 0 at x = 4 cm (the only hat that is 0 at both ends)")
    # left side: on each piece a constant times a constant, times the element length
    c1 = kA * hat_slope_on(2, 1, nodes) * h       # factor of (T2 - T1)/h: in element 1, T' = (T2 - T1)/h
    c2 = kA * hat_slope_on(2, 2, nodes) * h       # in element 2, T' = (T3 - T2)/h
    print(f"  element 1: T' = (T2 - T1)/h, N2' = +1/h -> integral = kA/h (T2 - T1) = {fmt(c1 / h)} (T2 - {fmt(t_left)}) W")
    print(f"  element 2: T' = (T3 - T2)/h, N2' = -1/h -> integral = kA/h (T2 - T3) = {fmt(-c2 / h)} (T2 - {fmt(t_right)}) W")
    N2 = hat(2, nodes)
    rhs_hand = None
    rhs_num = num_int(lambda x: q(x) * N2(x), 0, L)
    if np.allclose(q(np.linspace(0, L, 9)), q(0.0)):
        rhs_hand = float(q(0.0)) * h            # triangle area: base 2h, height 1, area h
        print(f"  right side: q times the area under the hat (base {fmt(2 * h * 100)} cm, height 1,"
              f" area {fmt(h * 100)} cm) = {fmt(float(q(0.0)))} x {fmt(h)} = {fmt(rhs_hand)} W"
              f"   (numerical {fmt(rhs_num)}) -> {verdict(abs(rhs_hand - rhs_num) < 1e-6)}")
    else:
        print(f"  right side: integral of q N2 = {fmt(rhs_num)} W (numerical)")
    rhs = rhs_num if rhs_hand is None else rhs_hand
    # 2 (kA/h) T2 - (kA/h)(T1 + T3) = rhs
    g = kA / h
    T2 = (rhs + g * (t_left + t_right)) / (2 * g)
    print(f"  equation: {fmt(g)} (T2 - {fmt(t_left)}) + {fmt(g)} (T2 - {fmt(t_right)}) = {fmt(rhs)}"
          f"  ->  {fmt(2 * g)} T2 = {fmt(rhs + g * (t_left + t_right))}  ->  T2 = {fmt(T2)} °C")
    # the "overall heat balance" of option D in the bet: use the broken line's slope as the heat leaving the ends
    naive = (q(0.0) * L if rhs_hand is not None else num_int(q, 0, L))
    T2_naive = (naive + g * (t_left + t_right)) / (2 * g)
    print(f"  (whole-bar balance using the broken line's slopes as the end heat: {fmt(g)} (T2 - {fmt(t_left)})"
          f" + {fmt(g)} (T2 - {fmt(t_right)}) = {fmt(naive)} W -> T2 = {fmt(T2_naive)} °C)")
    return T2, g, rhs


def element_table(kA, nodes, e, q):
    """2x2 small table of element e and its share of the heat. The four numbers are ∫ kA Na' Nb' dx (the two hats in the element)."""
    a, b = nodes[e - 1], nodes[e]
    h = b - a
    ids = [e, e + 1]
    ke = np.zeros((2, 2))
    for r, i in enumerate(ids):
        for c, j in enumerate(ids):
            ke[r, c] = kA * hat_slope_on(i, e, nodes) * hat_slope_on(j, e, nodes) * h
    fe = np.array([num_int(lambda x: q(x) * hat(i, nodes)(x), a, b) for i in ids])
    return ke, fe


def step4_tables(kA, q, nodes, t_left, t_right, T2_from_step3):
    print("\nstep 4: the 2x2 small table of each element, then put them together")
    n = len(nodes)
    K = np.zeros((n, n))
    f = np.zeros(n)
    for e in range(1, n):
        ke, fe = element_table(kA, nodes, e, q)
        h = nodes[e] - nodes[e - 1]
        print(f"  element {e} (nodes {e},{e + 1}), four numbers = integral of kA Na' Nb' over the element:")
        print(f"    small table [W/K]: [[{fmt(ke[0, 0])}, {fmt(ke[0, 1])}], [{fmt(ke[1, 0])}, {fmt(ke[1, 1])}]]"
              f"  = kA/h [[1, -1], [-1, 1]], kA/h = {fmt(kA / h)} W/K")
        print(f"    heat made in this element {fmt(fe.sum())} W, shared to its two nodes:"
              f" {fmt(fe[0])} W, {fmt(fe[1])} W")
        print(f"    its 2x2 equations: small table x (T{e}, T{e + 1}) = ({fmt(fe[0])}, {fmt(fe[1])})"
              f" + heat flowing into the element at its left end, at its right end")
        for r in range(2):
            for c in range(2):
                K[e - 1 + r, e - 1 + c] += ke[r, c]
        f[e - 1:e + 1] += fe
    print("  put together (node 2's two shares add up; the heat element 1 gives to element 2"
          " at x = 2 cm cancels, like the inner forces between springs):")
    for i in range(n):
        row = "  ".join(f"{fmt(K[i, j]):>3}" for j in range(n))
        extra = ""
        if i == 0:
            extra = " - (heat leaving the left end)"
        if i == n - 1:
            extra = " - (heat leaving the right end)"
        print(f"    row {i + 1}: [{row}] (T1, T2, T3) = {fmt(f[i])}{extra}")
    print(f"  T1 = {fmt(t_left)}, T3 = {fmt(t_right)} are given: rows 1 and 3 hold the unknown end heat,"
          " set them aside; move the known T1, T3 in row 2 to the right")
    rhs2 = f[1] - K[1, 0] * t_left - K[1, 2] * t_right
    T2 = rhs2 / K[1, 1]
    print(f"  row 2: {fmt(K[1, 1])} T2 = {fmt(f[1])} + {fmt(-K[1, 0])} x {fmt(t_left)}"
          f" + {fmt(-K[1, 2])} x {fmt(t_right)} = {fmt(rhs2)}  ->  T2 = {fmt(T2)} °C")
    print(f"  same as step 3 -> {verdict(abs(T2 - T2_from_step3) < 1e-9)}")
    Tn = np.array([t_left, T2, t_right])
    out_left = f[0] - K[0] @ Tn
    out_right = f[2] - K[2] @ Tn
    print(f"  rows 1 and 3 now give the heat leaving the ends: left {fmt(out_left)} W,"
          f" right {fmt(out_right)} W, total {fmt(out_left + out_right)} W")
    return K, f, Tn, out_left, out_right


# ---------------------------------------------------------------- 5. comparison
def step5_compare(kA, nodes, Tn, T_exact, Phi_exact, out_left, out_right):
    print("\nstep 5: compare with the exact solution")
    xs = [0.0, 0.01, 0.02, 0.03, 0.04]
    fem = np.interp(xs, nodes, Tn)
    print("  x [cm]        " + "".join(f"{x * 100:>8g}" for x in xs))
    print("  broken line   " + "".join(f"{fmt(v):>8}" for v in fem))
    print("  exact         " + "".join(f"{fmt(T_exact(x)):>8}" for x in xs))
    diff = [float(T_exact(x)) - v for x, v in zip(xs, fem)]
    print("  exact - broken" + "".join(f"{fmt(d):>8}" for d in diff))
    node_ok = all(abs(diff[i]) < 1e-6 for i in (0, 2, 4))
    print(f"  at the three nodes the broken line equals the exact value -> {verdict(node_ok)}"
          "  (in this example; README section 3)")
    h = nodes[1] - nodes[0]
    for e in (1, 2):
        slope_flow = -kA * (Tn[e] - Tn[e - 1]) / h
        xm = 0.5 * (nodes[e - 1] + nodes[e])
        print(f"  element {e}: heat flow from the broken line's slope {fmt(slope_flow)} W (same all along);"
              f" exact {fmt(Phi_exact(nodes[e - 1]))} W at its left end, {fmt(Phi_exact(xm))} W at its middle,"
              f" {fmt(Phi_exact(nodes[e]))} W at its right end")
    print(f"  heat leaving the ends from rows 1 and 3: {fmt(out_left)} W, {fmt(out_right)} W;"
          f" exact {fmt(-Phi_exact(0.0))} W, {fmt(Phi_exact(L))} W ->"
          f" {verdict(abs(out_left + Phi_exact(0.0)) < 1e-6 and abs(out_right - Phi_exact(L)) < 1e-6)}")


# ---------------------------------------------------------------- 6. finite volume side note
def box_vs_hat(kA, nodes, q, t_left, t_right, label):
    h = nodes[1] - nodes[0]
    g = kA / h
    box = num_int(q, nodes[1] - h / 2, nodes[1] + h / 2)       # control volume: x = 1 cm to 3 cm
    hat_w = num_int(lambda x: q(x) * hat(2, nodes)(x), 0, L)
    T2_fv = (box + g * (t_left + t_right)) / (2 * g)
    T2_fe = (hat_w + g * (t_left + t_right)) / (2 * g)
    print(f"  {label}: heat weighed by the box (1 to 3 cm) {fmt(box)} W, by the hat {fmt(hat_w)} W"
          f" -> T2 = {fmt(T2_fv)} (box) vs {fmt(T2_fe)} (hat) °C")
    return box, hat_w, T2_fv, T2_fe


def step6_box(kA, nodes, q_avg, t_left, t_right, Tn):
    print("\nstep 6 (side note): a finite-volume box around node 2 vs the finite-element hat")
    print("  box: a control volume from x = 1 cm to 3 cm; heat made inside = heat leaving its two faces,"
          " face heat from the broken line's slopes")
    print("  as a test function the box is 1 inside, 0 outside (not a hat)")
    box_vs_hat(kA, nodes, source_fn("uniform", q_avg), t_left, t_right, "uniform heat (the video)")
    box_vs_hat(kA, nodes, source_fn("middle", q_avg), t_left, t_right, "only the middle half heats (same total)")
    h = nodes[1] - nodes[0]
    T_ex_mid, _ = exact_solution("middle", q_avg, kA, t_left, t_right)
    print(f"  exact T at x = 2 cm when only the middle half heats: {fmt(T_ex_mid(0.02))} °C")
    # the finite element broken line in element 1: heat flow at its two ends (from the slope) is the same, so the element's own heat is not balanced by it
    flow1 = -kA * (Tn[1] - Tn[0]) / h
    made1 = q_avg * h
    flow2 = -kA * (Tn[2] - Tn[1]) / h
    print(f"  heat flow by the broken line's slope: {fmt(flow1)} W just left of x = 2 cm,"
          f" {fmt(flow2)} W just right of it (jumps by {fmt(flow2 - flow1)} W at the node)")
    print(f"  element 1 by the slope: {fmt(abs(flow1))} W in at one end, {fmt(abs(flow1))} W out at the other,"
          f" but it makes {fmt(made1)} W inside -> not balanced element by element")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--power", type=float, default=POWER, help="total heat made in the bar [W]")
    p.add_argument("--t-left", type=float, default=T_END, help="temperature held at x = 0 [°C]")
    p.add_argument("--t-right", type=float, default=T_END, help="temperature held at x = L [°C]")
    p.add_argument("--source", choices=["uniform", "middle"], default="uniform",
                   help="uniform: every part heats; middle: only L/4..3L/4 heats (same total)")
    args = p.parse_args()

    unit_check()
    kA = K_COND * A
    q_avg = args.power / L
    print(f"bar: L = {fmt(L * 100)} cm, A = {fmt(A * 1e4)} cm^2, k = {fmt(K_COND)} W/(m K),"
          f" kA = {fmt(kA)} W m/K")
    print(f"heat: P = {fmt(args.power)} W in total, q = P / L = {fmt(q_avg)} W/m ({args.source});"
          f" ends held at {fmt(args.t_left)} and {fmt(args.t_right)} °C")
    print(f"one cm of the bar makes {fmt(q_avg / 100)} W; k = {fmt(K_COND)} means a 1 m cube with 1 K"
          f" across it passes {fmt(K_COND)} W")

    step1_by_parts()
    T_ex, Phi_ex = step2_equation(kA, q_avg, args.t_left, args.t_right, args.source)
    nodes = np.array([0.0, L / 2, L])
    q = source_fn(args.source, q_avg)
    T2, g, rhs = step3_weak_middle_hat(kA, q, nodes, args.t_left, args.t_right)
    K, f, Tn, out_l, out_r = step4_tables(kA, q, nodes, args.t_left, args.t_right, T2)
    step5_compare(kA, nodes, Tn, T_ex, Phi_ex, out_l, out_r)
    if args.source == "uniform":
        step6_box(kA, nodes, q_avg, args.t_left, args.t_right, Tn)
    print("\nsummary: T1, T2, T3 = " + ", ".join(fmt(t) for t in Tn) + " °C")


if __name__ == "__main__":
    main()
