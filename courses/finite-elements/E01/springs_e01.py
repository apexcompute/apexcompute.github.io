# Copyright (c) 2026 the course author. All rights reserved. For personal learning only.
"""E01: three springs in a chain; build K u = f one step at a time.

    wall |--[k1]--o--[k2]--o--[k3]--o  --> F
         1        2        3        4      (node numbers)

Node 1 is pinned to the wall (displacement 0); force F pulls on node 4, positive to the right.
Units: force in N, displacement in mm, spring stiffness k in N/mm.

The script does five things and prints the matrix at every step:
  1. each spring's own 2x2 matrix (the element matrix);
  2. add them one by one into the 4x4 big matrix (assembly), printing after each one;
  3. can the 4x4 be solved as it is? Does moving the whole chain need a force?
  4. pin node 1 (cross out row 1 and column 1), solve the 3x3, check by hand, find the wall force;
  5. make the middle spring twice as stiff, redo it, and list which cells of the big matrix changed.

Usage:
  python3 springs_e01.py                     default k = 30 20 60, F = 60, compare with k2 = 40
  python3 springs_e01.py --k 30 20 0         change it and play (README section 4)
  python3 springs_e01.py --k2-new 60         another middle spring for the comparison
NumPy only; the data structure is my own: one spring is (left node, right node, k).
"""
import argparse

import numpy as np

# ---------------------------------------------------------------- unit check
# Each quantity is stored as (power of N, power of mm). K u must have the same unit as f: N.
UNITS = {"k": (1, -1), "u": (0, 1), "f": (1, 0)}


def unit_check():
    k_u = tuple(a + b for a, b in zip(UNITS["k"], UNITS["u"]))
    ok = k_u == UNITS["f"]
    print("unit check: K [N/mm] * u [mm] -> N, f is N:", "OK" if ok else "FAIL")
    if not ok:
        raise SystemExit("unit mismatch")


# ---------------------------------------------------------------- small helpers
def show(title, a, fmt="{:7.1f}", labels=None):
    """Print a matrix or vector; labels are the node numbers of rows and columns (from 1)."""
    print(title)
    a = np.atleast_2d(a)
    if labels is not None and a.shape[0] > 1:
        print("        " + "".join(f"node{j}".rjust(9) for j in labels))
    for i, row in enumerate(a):
        head = f"  node{labels[i]:<2d}" if labels is not None and a.shape[0] > 1 else "  "
        print(head + "".join(fmt.format(x).rjust(9) for x in row))


def spring_matrix(k):
    """Stiffness matrix of one spring (one element).

    Positive to the right. Left end moves ua, right end moves ub; the spring stretches ub - ua.
    What this matrix gives: the forces the outside must put on the two end nodes to hold these displacements.
      left end: k (ua - ub)    right end: k (ub - ua)
    That is [[k, -k], [-k, k]] times [ua, ub]. The spring's own pull on its end nodes is the exact opposite.
    """
    return np.array([[k, -k], [-k, k]], dtype=float)


def assemble(springs, n_nodes, trace=True):
    """Add each spring's 2x2 into the n_nodes x n_nodes big matrix.

    springs: [(left node, right node, k), ...], nodes counted from 1.
    A spring only touches the rows and columns of its two end nodes: 4 cells in all.
    """
    K = np.zeros((n_nodes, n_nodes))
    for s, (a, b, k) in enumerate(springs, start=1):
        ke = spring_matrix(k)
        rows = [a - 1, b - 1]            # position in the big matrix (numpy counts from 0)
        for i in range(2):
            for j in range(2):
                K[rows[i], rows[j]] += ke[i, j]
        if trace:
            print(f"\nadd spring {s} (node {a} -> node {b}, k = {k:g} N/mm) "
                  f"into cells ({a},{a}) ({a},{b}) ({b},{a}) ({b},{b})")
            show("  K so far [N/mm]:", K, labels=range(1, n_nodes + 1))
    return K


def fix_node(K, f, node):
    """Fix one node (displacement 0): cross out its row and column.

    Cross out the column: it multiplies this node's displacement, which is 0, so it adds nothing.
    Cross out the row: its right side is the force from the wall on the node, not known beforehand; leave it out,
    and once the displacements are solved, use this row to get the wall force.
    This only works for "displacement 0": if the node is pinned at a known nonzero displacement, this column
    does not give 0; move it to the right side first (f minus this column x the known displacement), then cross out (README section 3).
    """
    keep = [i for i in range(K.shape[0]) if i != node - 1]
    return K[np.ix_(keep, keep)], f[keep], keep


def run(springs, n_nodes, force, fixed, trace=True, tag=""):
    print("\n" + "=" * 64)
    print(f"case {tag}: k = " + ", ".join(f"{k:g}" for _, _, k in springs) +
          f" N/mm, F = {force:g} N at node {n_nodes}, node {fixed} fixed")
    print("=" * 64)

    # 1. stiffness matrix of each spring
    if trace:
        print("\nstep 1: stiffness matrix of each spring [N/mm]")
        for s, (a, b, k) in enumerate(springs, start=1):
            show(f"  spring {s} (nodes {a},{b}):", spring_matrix(k), labels=[a, b])
        ke = spring_matrix(springs[0][2])
        demo = ke @ np.array([0.0, 2.0])
        print(f"  check one matrix-vector product: spring 1 with u = (0, 2) mm "
              f"-> outside forces needed at its two ends ({demo[0]:g}, {demo[1]:g}) N")

    # 2. assembly
    if trace:
        print("\nstep 2: assembly, one spring at a time")
    K = assemble(springs, n_nodes, trace=trace)
    f = np.zeros(n_nodes)
    f[n_nodes - 1] = force
    show("\nfull stiffness matrix K [N/mm]:", K, labels=range(1, n_nodes + 1))
    show(f"force vector f [N] (node {fixed}: force from the wall, not known yet, "
         "written as 0 for now):", f, fmt="{:7.1f}")
    if trace:
        print("each row is the force balance at one node "
              "(K u = outside force needed at that node):")
        for i in range(n_nodes):
            terms = " ".join(f"{K[i, j]:+g} u{j + 1}" for j in range(n_nodes) if K[i, j] != 0)
            terms = terms or "0"
            rhs = f"R{fixed} (wall, unknown)" if i == fixed - 1 else f"{f[i]:g}"
            print(f"  node {i + 1}: {terms} = {rhs}")

    # 3. can it be solved without fixing anything?
    shift = np.ones(n_nodes)
    if trace:
        print("\nstep 3: can we solve the 4x4 as it is?")
        print("  move the whole chain 1 mm to the right, u = (1, 1, 1, 1) mm:")
        print("  K u =", np.array2string(K @ shift, precision=1), "N  (no force needed)")
        print(f"  rank of K = {np.linalg.matrix_rank(K)} of {n_nodes}"
              " -> no unique answer as it is")
        print("  add up all four rows: left side", np.array2string(K.sum(axis=0), precision=1),
              f"x u = 0 always; outside forces without the wall add up to {f.sum():g} N")
        print("  -> without the wall: no solution; with the wall's R1 balancing it:"
              " a solution plus any shift is still a solution")

    # 4. fix one end, solve, check
    Kr, fr, keep = fix_node(K, f, fixed)
    labels = [i + 1 for i in keep]
    rank_r = np.linalg.matrix_rank(Kr)
    if trace:
        print(f"\nstep 4: hold node {fixed} (u{fixed} = 0): "
              f"cross out row {fixed} and column {fixed}")
        show("  reduced K [N/mm]:", Kr, labels=labels)
        show("  reduced f [N]:", fr)
    if rank_r < Kr.shape[0]:
        print(f"  reduced K has rank {rank_r} of {Kr.shape[0]}: still no unique answer.")
        print("  some part of the chain is not tied to the wall (a spring with k = 0?).")
        return K, None
    ur = np.linalg.solve(Kr, fr)
    u = np.zeros(n_nodes)
    u[keep] = ur
    reaction = K[fixed - 1] @ u - f[fixed - 1]
    print("\ndisplacements u [mm]:",
          "  ".join(f"u{i + 1} = {x:g}" for i, x in enumerate(u)))
    resid = np.abs(Kr @ ur - fr).max()
    print("check K u = f on the free nodes: max |K u - f| < 1e-9 N ->",
          "PASS" if resid < 1e-9 else "FAIL")
    reaction = 0.0 if abs(reaction) < 1e-9 else reaction   # drop -0 and rounding noise
    total = reaction + force
    total = 0.0 if abs(total) < 1e-9 else total
    print(f"force from the wall on node {fixed}: {reaction:g} N "
          f"(applied F = {force:g} N; sum = {total:g} N)")

    # By hand: in series, every spring carries the same force F, stretches F / k; add them up one by one
    stretch = [force / k for _, _, k in springs]
    hand = np.concatenate([[0.0], np.cumsum(stretch)])
    print("hand calc: each spring carries F, stretch = F / k = " +
          ", ".join(f"{x:g}" for x in stretch) + " mm -> u = " +
          ", ".join(f"{x:g}" for x in hand) + " mm ->",
          "PASS" if np.allclose(hand, u) else "FAIL")
    k_eq = 1.0 / sum(1.0 / k for _, _, k in springs)
    print(f"equivalent stiffness of the chain: {k_eq:g} N/mm, "
          f"F / k_eq = {force / k_eq:g} mm at node {n_nodes}")
    return K, u


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--k", type=float, nargs=3, default=[30.0, 20.0, 60.0],
                   metavar=("K1", "K2", "K3"), help="three spring stiffnesses [N/mm]")
    p.add_argument("--force", type=float, default=60.0, help="pull at node 4 [N]")
    p.add_argument("--k2-new", type=float, default=None,
                   help="middle spring for the comparison [N/mm] (default: 2 x K2)")
    args = p.parse_args()

    unit_check()
    k1, k2, k3 = args.k
    k2_new = 2 * k2 if args.k2_new is None else args.k2_new

    def chain(ka, kb, kc):
        return [(1, 2, ka), (2, 3, kb), (3, 4, kc)]

    K_a, u_a = run(chain(k1, k2, k3), 4, args.force, fixed=1, trace=True, tag="A")
    K_b, u_b = run(chain(k1, k2_new, k3), 4, args.force, fixed=1, trace=False,
                   tag=f"B (middle spring {k2:g} -> {k2_new:g})")

    print("\n" + "=" * 64)
    print(f"compare: middle spring k2 {k2:g} -> {k2_new:g} N/mm")
    print("=" * 64)
    diff = K_b - K_a
    show("K(B) - K(A) [N/mm]:", diff, labels=range(1, 5))
    cells = [(i + 1, j + 1) for i in range(4) for j in range(4) if diff[i, j] != 0]
    print(f"cells that changed: {len(cells)} of 16 ->",
          " ".join(f"({i},{j}) {K_a[i - 1, j - 1]:g}->{K_b[i - 1, j - 1]:g}"
                   for i, j in cells))
    if u_a is not None and u_b is not None:
        print("displacements [mm]  A: " + "  ".join(f"{x:g}" for x in u_a) +
              "   B: " + "  ".join(f"{x:g}" for x in u_b))
        moved = [i + 1 for i in range(4) if not np.isclose(u_a[i], u_b[i])]
        print("nodes whose displacement changed:", moved)


if __name__ == "__main__":
    main()
