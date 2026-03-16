"""
Map a scale by scale degree.
"""

import argparse
import signal
import sys

import mido
import mtsespy as mts
import tuning_library as tl

from gral.utils import (
    print_scale,
    MIDI_NOTE_MAP,
    MIDDLE_C_FREQ,
    LAUNCHPAD_MIDI_INPUT_NAME,
)


def tune(scale, steps, origin, ref_freq=MIDDLE_C_FREQ):
    kbm = tl.start_scale_on_and_tune_note_to(scale_start=0, midi_note=0, freq=ref_freq)
    tuning = tl.Tuning(scale, kbm)

    print()
    print_scale(tuning, steps, origin, ref_freq)

    s, t = steps
    x0, y0 = origin

    def scale_degree(x, y):
        return (x - x0) * s + (y - y0) * t

    # Light up root and octaves
    try:
        with mido.open_output(LAUNCHPAD_MIDI_INPUT_NAME) as midi_out:
            for (x, y), n in MIDI_NOTE_MAP.items():
                r = scale_degree(x, y)
                if r % tuning.scale.count == 0:
                    midi_out.send(mido.Message("note_on", note=n, velocity=44))
                else:
                    midi_out.send(mido.Message("note_on", note=n, velocity=0))
    except OSError:
        print(f"Could not open {LAUNCHPAD_MIDI_INPUT_NAME}")
        sys.exit(1)

    # Set tuning
    with mts.Master():
        for (x, y), n in MIDI_NOTE_MAP.items():
            r = scale_degree(x, y)
            mts.set_note_tuning(tuning.frequency_for_midi_note(r), n)
        signal.pause()


def main(arg_list=None):
    parser = argparse.ArgumentParser(description="Map a scale by scale degree")
    parser.add_argument("scl_file", help="scl file containing scale to use")
    parser.add_argument(
        "-s",
        "--steps",
        nargs=2,
        type=int,
        required=True,
        help="Number of scale degrees to go up when moving along a row and up a column",
    )
    parser.add_argument(
        "-o", "--origin", nargs=2, type=int, help="Position of 1/1 on keyboard"
    )
    args = parser.parse_args(arg_list)

    scale = tl.read_scl_file(args.scl_file)
    steps = tuple(args.steps)
    origin = tuple(args.origin) if args.origin else (0, 0)

    tune(scale, steps, origin)


if __name__ == "__main__":
    main()
