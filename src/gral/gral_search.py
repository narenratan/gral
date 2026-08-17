"""
Apply Erv Wilson's Gral method.
"""

import argparse
from fractions import Fraction as F
from decimal import Decimal

import pandas as pd


def mediant(x, y):
    (a, b), (c, d) = x, y
    return (a + c, b + d)


def greater_than(x, y):
    (a, b), (c, d) = x, y
    return a * d > c * b


def stern_brocot_parents(num, denom, n_max=None):
    f = F(*num.as_integer_ratio()) / F(*denom.as_integer_ratio())
    x = (f.numerator, f.denominator)
    a, b = (0, 1), (1, 0)
    m = mediant(a, b)
    pairs = [(a, b)]
    while True:
        if greater_than(m, x):
            a, b = a, m
        else:
            a, b = m, b
        m = mediant(a, b)
        if n_max is not None and m[1] > n_max:
            break
        pairs.append((a, b))
        if m == x:
            break
    return pairs


def gral_search(m, n, n_max, k=0):
    rows = []
    for (a, c), (b, d) in stern_brocot_parents(m, n, n_max):
        for k in range(-k, k + 1):
            a_prime = (1 + k) * a + k * b
            b_prime = (1 - k) * b - k * a
            c_prime = (1 + k) * c + k * d
            d_prime = (1 - k) * d - k * c
            det = a_prime * d_prime - b_prime * c_prime
            assert det == -1
            s = -d_prime * m + b_prime * n
            t = c_prime * m - a_prime * n
            name = mediant((a, c), (b, d))
            name_prime = mediant((a_prime, c_prime), (b_prime, d_prime))
            assert name == name_prime
            rows.append(
                (
                    f"{a}/{c}",
                    f"{b}/{d}",
                    f"{name[0]}/{name[1]}",
                    k,
                    a_prime,
                    b_prime,
                    c_prime,
                    d_prime,
                    s,
                    t,
                )
            )

    df = pd.DataFrame(
        rows, columns=["left", "right", "mediant", "k", "a", "b", "c", "d", "s", "t"]
    )

    return df


def print_ascii(df):
    use_k = set(df["k"]) != {0}
    rows = []
    left_prev = None
    right_prev = None
    med_prev = None
    k_max = df["k"].max()
    blank = 2 * " "
    for row in df.itertuples():
        left = row.left
        right = row.right
        med = row.mediant
        rows.append(
            (
                left if left != left_prev else blank,
                right if right != right_prev else blank,
                blank,
                med if med != med_prev else blank,
            )
            + ((row.k,) if use_k else ())
            + (
                blank,
                row.a,
                row.b,
                blank,
                row.c,
                row.d,
                blank,
                row.s,
                row.t,
            )
        )
        if use_k and row.k == k_max and row.Index != df.index[-1]:
            rows.append(14 * ("",))
        left_prev = left
        right_prev = right
        med_prev = med
    df = pd.DataFrame(
        rows,
        columns=[
            "Left",
            "Right",
            "",
            "Mediant",
        ]
        + (["k"] if use_k else [])
        + [
            "",
            "a",
            "b",
            "",
            "c",
            "d",
            "",
            "s",
            "t",
        ],
    )
    print("\n" + df.to_string(index=False) + "\n")


def print_latex(df):
    use_k = set(df["k"]) != {0}
    if use_k:
        print(r"""\begin{tabular}{rr@{\hspace{1cm}}rr@{\hspace{1cm}}rr@{\hspace{1cm}}rr@{\hspace{1cm}}rr}
\toprule
Left    &   Right   &   Mediant &  $k$  &  $a$  &  $b$  &  $c$  &  $d$  &  $s$  &  $t$  \\
\midrule""")
    else:
        print(r"""\begin{tabular}{rr@{\hspace{1cm}}r@{\hspace{1cm}}rr@{\hspace{1cm}}rr@{\hspace{1cm}}rr}
\toprule
Left    &   Right   &   Mediant &   $a$  &  $b$  &  $c$  &  $d$  &  $s$  &  $t$  \\
\midrule""")
    left_prev = None
    right_prev = None
    med_prev = None
    k_max = df["k"].max()
    blank = 5 * " "
    for row in df.itertuples():
        left = row.left
        right = row.right
        med = row.mediant
        print(f"${left}$" if left != left_prev else blank, end=" & ")
        print(f"${right}$" if right != right_prev else blank, end=" & ")
        print(f"${med}$" if med != med_prev else blank, end=" & ")
        to_print = ([row.k] if use_k else []) + [
            row.a,
            row.b,
            row.c,
            row.d,
            row.s,
            row.t,
        ]
        print(" & ".join(f"${x}$" for x in to_print), end="")
        if use_k and row.k == k_max and row.Index != df.index[-1]:
            print(r"\vspace{0.25cm}", end="")
        print(r" \\")
        left_prev = left
        right_prev = right
        med_prev = med
    print(r"\bottomrule")
    print(r"\end{tabular}")


def print_html(df):
    use_k = set(df["k"]) != {0}
    headers = ["Left", "Right", "Mediant"] + (["k"] if use_k else []) + ["a", "b", "c", "d", "s", "t"]
    print("<table>")
    print("  <thead>")
    print("    <tr>")
    for h in headers:
        print(f"      <th>{h}</th>")
    print("    </tr>")
    print("  </thead>")
    print("  <tbody>")
    left_prev = None
    right_prev = None
    med_prev = None
    blank = ""
    for row in df.itertuples():
        left = row.left
        right = row.right
        med = row.mediant
        left_cell = left if left != left_prev else blank
        right_cell = right if right != right_prev else blank
        med_cell = med if med != med_prev else blank
        cells = [left_cell, right_cell, med_cell]
        cells += ([str(row.k)] if use_k else [])
        cells += [str(row.a), str(row.b), str(row.c), str(row.d), str(row.s), str(row.t)]
        print("    <tr>")
        for cell in cells:
            print(f"      <td>{cell}</td>")
        print("    </tr>")
        left_prev = left
        right_prev = right
        med_prev = med
    print("  </tbody>")
    print("</table>")


def print_wiki(df):
    use_k = set(df["k"]) != {0}
    headers = ["Left", "Right", "Mediant"] + (["k"] if use_k else []) + ["a", "b", "c", "d", "s", "t"]
    print('{| class="wikitable"')
    print("! " + " !! ".join(headers))
    left_prev = None
    right_prev = None
    med_prev = None
    k_max = df["k"].max()
    blank = ""
    for row in df.itertuples():
        left = row.left
        right = row.right
        med = row.mediant
        print("|-")
        left_cell = left if left != left_prev else blank
        right_cell = right if right != right_prev else blank
        med_cell = med if med != med_prev else blank
        cells = [left_cell, right_cell, med_cell]
        cells += ([str(row.k)] if use_k else [])
        cells += [str(row.a), str(row.b), str(row.c), str(row.d), str(row.s), str(row.t)]
        print("| " + " || ".join(cells))
        left_prev = left
        right_prev = right
        med_prev = med
    print("|}")


def main(arg_list=None):
    parser = argparse.ArgumentParser(description="Apply Erv Wilson's Gral method")
    parser.add_argument("m", type=str, help="Number to search for is m/n")
    parser.add_argument("n", type=str)
    parser.add_argument(
        "-N",
        "--nmax",
        type=int,
        default=None,
        help="Stop search once denominator exceeds NMAX",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=0,
        help="Include terms between -K and +K in the extended Gral method",
    )
    parser.add_argument(
        "-l",
        "--latex",
        action="store_true",
        help="Print table in LaTeX format (uses booktabs LaTeX package)",
    )
    parser.add_argument(
        "-w",
        "--wiki",
        action="store_true",
        help="Print table in MediaWiki format",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Print table in HTML format",
    )

    args = parser.parse_args(arg_list)

    N = args.nmax
    if N is None and (not args.m.isnumeric() or not args.n.isnumeric()):
        N = 100

    m = Decimal(args.m)
    n = Decimal(args.n)
    k = args.k

    df = gral_search(m, n, N, k)

    if args.latex:
        print_latex(df)
    elif args.wiki:
        print_wiki(df)
    elif args.html:
        print_html(df)
    else:
        print_ascii(df)


if __name__ == "__main__":
    main()
