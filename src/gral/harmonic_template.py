"""
Map a scale using a harmonic template.
"""

import argparse
import signal
import sys
from fractions import Fraction as F

import mido
import mtsespy as mts
import pandas as pd

from gral.utils import (
    factorize,
    print_grid,
    read_scl_file_as_ratios,
    wide_df,
    MIDI_NOTE_MAP,
    MIDDLE_C_FREQ,
    LAUNCHPAD_MIDI_INPUT_NAME,
)


def tune(X_df, A_df, origin=None):
    if origin is None:
        x0 = -X_df["x"].min()
        y0 = -X_df["y"].min()
    else:
        x0, y0 = origin
    X_df.index.name = "ratio"
    X_df = X_df.reset_index()

    duplicated = X_df.duplicated(subset=["x", "y"], keep=False)
    if duplicated.any():
        print("Some notes mapped to the same key:")
        print(X_df.loc[duplicated].reset_index(drop=True))
        X_df = X_df.drop_duplicates(subset=["x", "y"])

    print("\n\n")
    col_width = print_grid(X_df, ["ratio"])
    print("\n\n")
    A_df.loc[F(1)] = (0, 0)
    A_df = A_df.reset_index().rename(columns={"index": "ratio"})
    print_grid(A_df, ["ratio"], col_width)
    print("\n")

    X_df = X_df.set_index(["x", "y"])

    A_df = A_df.set_index(["x", "y"])

    template = sorted(set(A_df.index) | {(0, 0)})

    # Light up keys
    try:
        with mido.open_output(LAUNCHPAD_MIDI_INPUT_NAME) as midi_out:
            for (x, y), n in MIDI_NOTE_MAP.items():
                dx, dy = x - x0, y - y0
                if (dx, dy) in X_df.index:
                    midi_out.send(mido.Message("note_on", note=n, velocity=3))
                else:
                    midi_out.send(mido.Message("note_on", note=n, velocity=0))
            for dx, dy in template:
                x = x0 + dx
                y = y0 + dy
                if (x, y) in MIDI_NOTE_MAP:
                    midi_out.send(
                        mido.Message("note_on", note=MIDI_NOTE_MAP[x, y], velocity=44)
                    )
    except OSError:
        print(f"Could not open {LAUNCHPAD_MIDI_INPUT_NAME}")
        sys.exit(1)

    # Set tuning
    with mts.Master():
        for (x, y), n in MIDI_NOTE_MAP.items():
            dx, dy = x - x0, y - y0
            if (dx, dy) in X_df.index:
                ratio = X_df.loc[(dx, dy), "ratio"]
                freq = MIDDLE_C_FREQ * ratio
                mts.set_note_tuning(freq, n)
                mts.filter_note(False, n, 0)
            else:
                mts.filter_note(True, n, 0)
        signal.pause()


def read_template(filename):
    template = pd.read_csv(filename)
    template.index = [F(x) for x in template["ratio"]]
    return template.drop(columns="ratio").T


def main(arg_list=None):
    parser = argparse.ArgumentParser(description="Map a scale with a harmonic template")
    parser.add_argument("scl_file", help="scl file containing scale to use")
    parser.add_argument(
        "-t", "--template", required=True, help="csv file containing harmonic template"
    )
    parser.add_argument(
        "-o", "--origin", nargs=2, type=int, help="Position of 1/1 on keyboard"
    )
    args = parser.parse_args(arg_list)

    A = read_template(args.template)

    ratios = read_scl_file_as_ratios(args.scl_file)

    V = wide_df(factorize(ratios))

    missing_harmonics = set(V.index) - set(A.columns)
    if missing_harmonics:
        raise ValueError(
            "Harmonics missing from template: " + ", ".join(map(str, missing_harmonics))
        )
    X = A.loc[:, V.index] @ V

    tune(X.T, A.T, args.origin)


if __name__ == "__main__":
    main()
