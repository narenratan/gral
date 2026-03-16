"""
Find a nice harmonic template for a given scale.
"""

import argparse
import math
from fractions import Fraction as F
from pathlib import Path

from ortools.sat.python import cp_model
import pandas as pd

from gral.utils import factorize, wide_df, print_grid, read_scl_file_as_ratios

DIRECTIONS = ["x", "y"]
FLIP = {"x": "y", "y": "x"}

M = 10**2  # Bounds on X are [-M, M]
R = 10**2  # Rounding factor for cents values (only used for pitch grid)


def _format_key(k):
    return ",".join(map(str, k)) if isinstance(k, tuple) else str(k)


class Model(cp_model.CpModel):
    def new_int_vars(self, index, *, name, bounds):
        return {
            k: self.new_int_var(*bounds, name=f"{name}[{_format_key(k)}]")
            for k in index
        }

    def new_bool_vars(self, index, *, name):
        return {k: self.new_bool_var(name=f"{name}[{_format_key(k)}]") for k in index}

    def add_constraint(self, expr, *, name):
        return self.add(expr).with_name(name)


def add_decision_variables(model, scale):
    V = factorize(scale)

    harmonics = sorted(set(h for h, _ in V))

    A_index = [(d, h) for d in DIRECTIONS for h in harmonics]

    A = model.new_int_vars(
        A_index,
        name="A",
        bounds=(-M, M),
    )

    X_index = [(d, s) for d in DIRECTIONS for s in scale]
    X = model.new_int_vars(
        X_index,
        name="X",
        bounds=(-M, M),
    )

    for d, s in X:
        model.add_constraint(
            sum(A[d, h] * V[h, s] for h in harmonics) == X[d, s],
            name=f"mapping[{d},{s}]",
        )

    return X, A


def add_increasing_pitch_constraint(model, scale, X):
    diff_index = [(s, t, d) for s in scale for t in scale for d in DIRECTIONS if s < t]

    same_coord = model.new_bool_vars(diff_index, name="same_coord")
    for s, t, d in diff_index:
        model.add_constraint(
            X[d, s] == X[d, t], name="same_coordinate"
        ).only_enforce_if(same_coord[s, t, d])
        model.add_constraint(
            X[d, s] != X[d, t], name="different_coordinate"
        ).only_enforce_if(~same_coord[s, t, d])
        model.add_constraint(
            X[d, s] < X[d, t], name="smaller_coordinate"
        ).only_enforce_if(same_coord[s, t, FLIP[d]])


def add_basis_constraint(model, X, basis):
    a = X["x", basis[0]]
    b = X["y", basis[0]]
    c = X["x", basis[1]]
    d = X["y", basis[1]]
    ad = model.new_int_var(-(M**2), M**2, name="ad")
    bc = model.new_int_var(-(M**2), M**2, name="bc")
    model.add_multiplication_equality(ad, [a, d]).with_name("def_ad")
    model.add_multiplication_equality(bc, [b, c]).with_name("def_bc")
    sign = model.new_bool_var(name="sign")
    model.add_constraint(ad - bc == -1 + 2 * sign, name="basis")


def add_pitch_grid_constraint(model, scale, X, pitch_grid_tol):
    cents = {s: round(R * 1200 * math.log2(s)) for s in scale}

    g = model.new_int_vars(DIRECTIONS, name="g", bounds=(0, R * 1200))

    pitch = model.new_int_vars(scale, name="pitch", bounds=(0, R * 1200))
    abs_pitch_diff = model.new_int_vars(
        scale, name="abs_pitch_diff", bounds=(0, R * 1200)
    )
    for s in scale:
        model.add_constraint(
            abs_pitch_diff[s] >= (pitch[s] - cents[s]), name=f"abs_plus[{s}]"
        )
        model.add_constraint(
            abs_pitch_diff[s] >= -(pitch[s] - cents[s]), name=f"abs_minus[{s}]"
        )
        model.add_constraint(
            abs_pitch_diff[s] <= R * pitch_grid_tol, name=f"max_abs_pitch_diff[{s}]"
        )

    gX = model.new_int_vars(X, name="gX", bounds=(-R * M * 1200, R * M * 1200))
    for d, s in gX:
        model.add_multiplication_equality(gX[d, s], [g[d], X[d, s]]).with_name(
            f"def_gX[{d},{s}]"
        )
    for s in scale:
        model.add_constraint(
            pitch[s] == sum(gX[d, s] for d in DIRECTIONS),
            name=f"def_pitch{s}",
        )
    return g


def add_diff_variables(model, scale, X):
    diff_index = [(s, t, d) for s in scale for t in scale for d in DIRECTIONS if s < t]
    X_diff_plus = model.new_int_vars(
        diff_index,
        name="X_diff_plus",
        bounds=(0, 2 * M),
    )
    X_diff_minus = model.new_int_vars(
        diff_index,
        name="X_diff_minus",
        bounds=(0, 2 * M),
    )
    for s, t, d in X_diff_plus:
        model.add_constraint(
            X[d, s] - X[d, t] == X_diff_plus[s, t, d] - X_diff_minus[s, t, d],
            name=f"def_X_diff[{s},{t},{d}]",
        )
    X_diff_abs = {k: X_diff_plus[k] + X_diff_minus[k] for k in X_diff_plus}
    return X_diff_abs


def add_box_variables(model, X):
    box_up = model.new_int_vars(DIRECTIONS, name="box_up", bounds=(0, M))
    box_down = model.new_int_vars(DIRECTIONS, name="box_down", bounds=(0, M))

    for d, s in X:
        model.add_constraint(X[d, s] <= box_up[d], name=f"box_up[{s},{d}]")
        model.add_constraint(-box_down[d] <= X[d, s], name=f"box_down[{s},{d}]")

    return box_up, box_down


def add_objective(model, scale, X, objective_weights):
    # Break symmetry between x and y directions
    direction_weights = {"x": 1.0, "y": 1.01}

    obj = 0

    if objective_weights["box"] != 0:
        box_up, box_down = add_box_variables(model, X)
        obj += objective_weights["box"] * sum(
            direction_weights[d] * (box_up[d] + box_down[d]) for d in DIRECTIONS
        )

    if objective_weights["X_diff"] != 0:
        X_diff_abs = add_diff_variables(model, scale, X)
        obj += objective_weights["X_diff"] * sum(
            direction_weights[d] * X_diff_abs[s, t, d] for s, t, d in X_diff_abs
        )

    model.minimize(obj)


def solve_model(model, X, A, g):
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    status = solver.solve(model)
    if status == cp_model.INFEASIBLE:
        raise ValueError("Infeasible model")

    X_sol = {k: solver.value(v) for k, v in X.items()}
    A_sol = {k: solver.value(v) for k, v in A.items()}
    g_sol = {k: solver.value(v) for k, v in g.items()}

    return X_sol, A_sol, g_sol


def _sol_to_df(sol):
    df = wide_df(sol).T
    df.index.name = "ratio"
    return df.reset_index()


def build_result(X_sol, A_sol, g_sol, *, flip):
    if flip:
        X_sol = {(FLIP[d], s): v for (d, s), v in X_sol.items()}
        A_sol = {(FLIP[d], s): v for (d, s), v in A_sol.items()}
        g_sol = {FLIP[d]: v for d, v in g_sol.items()}

    g_df = pd.DataFrame.from_dict(g_sol, orient="index").T

    return _sol_to_df(X_sol), _sol_to_df(A_sol), g_df


def print_result(X_df, A_df, g_df):
    if not g_df.empty:
        print("\n\n")
        decimals = round(math.log10(R))
        for d in DIRECTIONS:
            print(f"g[{d}] = {g_df[d].iloc[0]/R:{4 + decimals}} cents")
    print("\n\n")
    col_width = print_grid(X_df, ["ratio"])
    print("\n\n")
    A_df = A_df.copy()
    A_df.loc[len(A_df)] = [F(1, 1), 0, 0]
    print_grid(A_df, ["ratio"], col_width)
    print("\n")


def box_opt(scale, *, objective_weights, basis=None, pitch_grid_tol=None, flip=False):
    model = Model()

    X, A = add_decision_variables(model, scale)

    add_increasing_pitch_constraint(model, scale, X)

    if basis:
        add_basis_constraint(model, X, basis)

    g = {}
    if pitch_grid_tol:
        g = add_pitch_grid_constraint(model, scale, X, pitch_grid_tol)

    add_objective(model, scale, X, objective_weights)

    X_sol, A_sol, g_sol = solve_model(model, X, A, g)

    X_df, A_df, g_df = build_result(X_sol, A_sol, g_sol, flip=flip)

    print_result(X_df, A_df, g_df)

    return A_df, model


def main(arg_list=None):
    parser = argparse.ArgumentParser(
        description="Find a nice harmonic template for a scale"
    )
    parser.add_argument("scl_file", help="scl file containing scale to use")
    parser.add_argument(
        "-b",
        "--basis",
        nargs=2,
        type=F,
        help="Scale notes to form a basis on the keyboard",
    )
    parser.add_argument(
        "-w",
        "--weights",
        nargs=2,
        type=float,
        default=[1e0, 1e-4],
        help="Weights for the box size and note position differences in the objective function",
    )
    parser.add_argument(
        "-p",
        "--pitch-grid",
        type=int,
        help="Largest difference in cents allowed from some regular grid of pitches",
    )
    parser.add_argument(
        "-f",
        "--flip",
        action="store_true",
        help="Flip the x and y directions of the harmonic template found",
    )
    args = parser.parse_args(arg_list)

    objective_weights = dict(zip(["box", "X_diff"], args.weights))

    ratios = read_scl_file_as_ratios(args.scl_file)

    A_df, _ = box_opt(
        ratios,
        objective_weights=objective_weights,
        basis=args.basis,
        pitch_grid_tol=args.pitch_grid,
        flip=args.flip,
    )

    template_filename = f"{Path(args.scl_file).stem}-template.csv"
    A_df.to_csv(template_filename, index=False)
    print(f"Wrote {template_filename}\n")


if __name__ == "__main__":
    main()
