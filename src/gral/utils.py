"""
Utility functions for scale mapping
"""

import math
from collections import defaultdict
from fractions import Fraction as F
from itertools import chain

import numpy as np
import pandas as pd
import tuning_library as tl
from sympy import factorrat, Rational

MIDI_NOTE_MAP = {(i, j): 10 * j + i + 11 for i in range(8) for j in range(8)}
MIDDLE_C_FREQ = 440 * 2 ** (-9 / 12)

LAUNCHPAD_MIDI_INPUT_NAME = "Launchpad X LPX MIDI In"


def read_scl_file_as_ratios(scl_file):
    scale = tl.read_scl_file(scl_file)

    cents_tones = [t for t in scale.tones if t.type == tl.kToneCents]
    if cents_tones:
        raise ValueError(
            "Scale contains tones specified in cents: "
            + ", ".join(t.string_rep.strip() for t in cents_tones)
        )

    return [F(1, 1)] + sorted(F(t.ratio_n, t.ratio_d) for t in scale.tones)


def print_scale(tuning, steps, origin, ref_freq):
    s, t = steps
    x0, y0 = origin

    df = pd.DataFrame(
        ((x, y) for x in range(0, 8) for y in range(0, 8)), columns=["x", "y"]
    )
    df["r"] = s * (df["x"] - x0) + t * (df["y"] - y0)
    df["periods"], df["degree"] = df["r"].divmod(tuning.scale.count)
    ratios = [
        F(t.ratio_n, t.ratio_d) if t.type == tl.kToneRatio else F(2 ** (t.cents / 1200))
        for t in tuning.scale.tones
    ]
    period = ratios.pop()
    ratios = [F(1, 1), *ratios]

    df["ratio"] = [period**n * ratios[r] for n, r in zip(df["periods"], df["degree"])]
    df["cents"] = [
        1200 * math.log2(tuning.frequency_for_midi_note(r) / ref_freq) for r in df["r"]
    ]
    df["cents_from_ratio"] = [1200 * math.log2(x) for x in df["ratio"]]
    assert (df.cents - df.cents_from_ratio).abs().max() < 1e-2
    df["ratio_or_blank"] = [r if r.denominator < 10_000 else " . " for r in df["ratio"]]

    df["r_label"] = df["r"].astype(str) + "."

    print_grid(df, ["r_label", "ratio_or_blank", "cents"])


def factorize(scale, reduce=True):
    factors = defaultdict(lambda: 0)
    for s in scale:
        if s == 1:
            factors[F(2), s] = 0
            continue
        for p, n in factorrat(Rational(s)).items():
            if reduce and p != 2:
                twos = int(math.log2(p))
                factors[F(p, 2**twos), s] = n
                factors[F(2), s] += n * twos
            else:
                factors[F(p), s] += n
    return factors


def wide_df(input_dict):
    data = defaultdict(list)
    A = sorted(set(k[0] for k in input_dict))
    B = sorted(set(k[1] for k in input_dict))
    for a in A:
        for b in B:
            data[b].append(input_dict.get((a, b), 0))
    return pd.DataFrame(data, columns=B, index=A)


def _format(x):
    if isinstance(x, F):
        return f"{x.numerator}/{x.denominator}"
    if isinstance(x, float):
        return str(round(x))
    if isinstance(x, list):
        return r", ".join(_format(y) for y in x)
    return str(x)


def grid_df(df, col, fill="."):
    grid = df.pivot_table(
        index="y",
        columns="x",
        values=col,
        aggfunc=lambda x: list(dict.fromkeys(x)) if len(x) > 1 else x,
    )
    return grid.reindex(
        index=range(grid.index.max(), grid.index.min() - 1, -1),
        columns=range(grid.columns.min(), grid.columns.max() + 1),
    ).fillna(fill)


def print_grid(df, cols, col_width=None):
    grid_dfs = []
    for i, col in enumerate(cols):
        grid_dfs.append(grid_df(df, col, fill="* " if i == 0 else ""))
    if col_width is None:
        col_width = max(
            len(_format(x))
            for x in chain.from_iterable(np.ravel(gdf) for gdf in grid_dfs)
        )
    for i in range(len(grid_dfs[0])):
        for gdf in grid_dfs:
            print(" ".join(f"{_format(x):{col_width}}" for x in gdf.values[i]))
        print()
    return col_width
