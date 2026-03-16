import shlex
import signal
from contextlib import nullcontext
from pathlib import Path

import pytest
import mido
import mtsespy as mts

from gral.harmonic_template import main
from .mocks import mock_open_output, printer

TEST_DATA = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "scl_file, template_file, arg_str, expected_output",
    [
        (
            "baglama.scl",
            "baglama-template.csv",
            "",
            """


*        *        16/11    5/3      15/8     *       

12/11    5/4      1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    *        *        *       




*        5/4      *        *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        *        11/8     *        *       



Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "baglama.scl",
            "baglama-template.csv",
            "-o 1 2",
            """


*        *        16/11    5/3      15/8     *       

12/11    5/4      1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    *        *        *       




*        5/4      *        *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        *        11/8     *        *       



Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "genus.scl",
            "genus-template.csv",
            "",
            """


*          *          *          945/512    63/32      *          *         

*          *          189/128    3465/2048  231/128    *          *         

*          10395/8192 693/512    105/64     7/4        *          *         

2079/2048  315/256    21/16      385/256    27/16      495/256    *         

*          1155/1024  77/64      1485/1024  99/64      15/8       2/1       

*          35/32      297/256    45/32      3/2        55/32      *         

*          135/128    9/8        165/128    11/8       *          *         

*          *          33/32      5/4        *          *          *         

*          *          1/1        *          *          *          *         




*          *          7/4        *          *         

*          *          *          *          *         

*          *          *          *          2/1       

*          *          3/2        *          *         

*          *          11/8       *          *         

*          5/4        *          *          *         

1/1        *          *          *          *         



Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "baglama.scl",
            "baglama-template-2.csv",
            "",
            """Some notes mapped to the same key:
  ratio  x  y
0   5/4  3  1
1   3/2  3  1
2   5/3  5  2
3     2  5  2



*        *        16/11    *        *        *        *       

12/11    *        1024/729 128/81   16/9     5/3      15/8    

256/243  32/27    4/3      5/4      27/16    243/128  *       

1/1      9/8      81/64    *        *        *        *       




*        *        *        *        *        2/1     

*        *        *        3/2, 5/4 *        *       

1/1      *        *        *        *        *       

*        *        *        11/8     *        *       



Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "baglama.scl",
            "baglama-template-3.csv",
            "",
            """


*        *        16/11    5/3      15/8     *       

12/11    5/4      1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    *        *        *       




*        *        *        *        13/8     *       

*        *        *        *        *        *       

*        5/4      *        *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        *        11/8     *        *       



Could not open Launchpad X LPX MIDI In
""",
        ),
    ],
    ids=lambda x: x if len(x) < 100 else "",
)
def test_harmonic_template(scl_file, template_file, arg_str, expected_output, capsys):
    with pytest.raises(SystemExit) as e:
        scl_path = TEST_DATA / scl_file
        template_path = TEST_DATA / template_file
        arg_list = shlex.split(f"{scl_path} -t {template_path} {arg_str}")
        main(arg_list)
    assert e.value.code == 1
    assert capsys.readouterr().out == expected_output


def test_missing_harmonic():
    scl_file = "baglama.scl"
    template_file = "baglama-template-4.csv"
    scl_path = TEST_DATA / scl_file
    template_path = TEST_DATA / template_file
    arg_list = shlex.split(f"{scl_path} -t {template_path}")

    with pytest.raises(ValueError) as e:
        main(arg_list)
    assert str(e.value) == "Harmonics missing from template: 11/8"


def test_cents():
    scl_file = "ratios-and-cents.scl"
    template_file = "baglama-template.csv"
    scl_path = TEST_DATA / scl_file
    template_path = TEST_DATA / template_file
    arg_list = shlex.split(f"{scl_path} -t {template_path}")

    with pytest.raises(ValueError) as e:
        main(arg_list)
    assert str(e.value) == "Scale contains tones specified in cents: 700.0"


def test_harmonic_template_mocked(monkeypatch, capsys):
    """
    Test tuning and MIDI message sending with mocks.
    """
    monkeypatch.setattr(mido, "open_output", mock_open_output)
    monkeypatch.setattr(signal, "pause", lambda: None)
    monkeypatch.setattr(mts, "Master", nullcontext)
    monkeypatch.setattr(mts, "set_note_tuning", printer("set_note_tuning"))
    monkeypatch.setattr(mts, "filter_note", printer("filter_note"))

    scl_file = "baglama.scl"
    template_file = "baglama-template.csv"
    scl_path = TEST_DATA / scl_file
    template_path = TEST_DATA / template_file

    main(shlex.split(f"{scl_path} -t {template_path}"))

    expected_output = """


*        *        16/11    5/3      15/8     *       

12/11    5/4      1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    *        *        *       




*        5/4      *        *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        *        11/8     *        *       



Opening Launchpad X LPX MIDI In
note_on channel=0 note=11 velocity=3 time=0
note_on channel=0 note=21 velocity=3 time=0
note_on channel=0 note=31 velocity=3 time=0
note_on channel=0 note=41 velocity=0 time=0
note_on channel=0 note=51 velocity=0 time=0
note_on channel=0 note=61 velocity=0 time=0
note_on channel=0 note=71 velocity=0 time=0
note_on channel=0 note=81 velocity=0 time=0
note_on channel=0 note=12 velocity=3 time=0
note_on channel=0 note=22 velocity=3 time=0
note_on channel=0 note=32 velocity=3 time=0
note_on channel=0 note=42 velocity=0 time=0
note_on channel=0 note=52 velocity=0 time=0
note_on channel=0 note=62 velocity=0 time=0
note_on channel=0 note=72 velocity=0 time=0
note_on channel=0 note=82 velocity=0 time=0
note_on channel=0 note=13 velocity=3 time=0
note_on channel=0 note=23 velocity=3 time=0
note_on channel=0 note=33 velocity=3 time=0
note_on channel=0 note=43 velocity=3 time=0
note_on channel=0 note=53 velocity=0 time=0
note_on channel=0 note=63 velocity=0 time=0
note_on channel=0 note=73 velocity=0 time=0
note_on channel=0 note=83 velocity=0 time=0
note_on channel=0 note=14 velocity=0 time=0
note_on channel=0 note=24 velocity=3 time=0
note_on channel=0 note=34 velocity=3 time=0
note_on channel=0 note=44 velocity=3 time=0
note_on channel=0 note=54 velocity=0 time=0
note_on channel=0 note=64 velocity=0 time=0
note_on channel=0 note=74 velocity=0 time=0
note_on channel=0 note=84 velocity=0 time=0
note_on channel=0 note=15 velocity=0 time=0
note_on channel=0 note=25 velocity=3 time=0
note_on channel=0 note=35 velocity=3 time=0
note_on channel=0 note=45 velocity=3 time=0
note_on channel=0 note=55 velocity=0 time=0
note_on channel=0 note=65 velocity=0 time=0
note_on channel=0 note=75 velocity=0 time=0
note_on channel=0 note=85 velocity=0 time=0
note_on channel=0 note=16 velocity=0 time=0
note_on channel=0 note=26 velocity=3 time=0
note_on channel=0 note=36 velocity=3 time=0
note_on channel=0 note=46 velocity=0 time=0
note_on channel=0 note=56 velocity=0 time=0
note_on channel=0 note=66 velocity=0 time=0
note_on channel=0 note=76 velocity=0 time=0
note_on channel=0 note=86 velocity=0 time=0
note_on channel=0 note=17 velocity=0 time=0
note_on channel=0 note=27 velocity=0 time=0
note_on channel=0 note=37 velocity=0 time=0
note_on channel=0 note=47 velocity=0 time=0
note_on channel=0 note=57 velocity=0 time=0
note_on channel=0 note=67 velocity=0 time=0
note_on channel=0 note=77 velocity=0 time=0
note_on channel=0 note=87 velocity=0 time=0
note_on channel=0 note=18 velocity=0 time=0
note_on channel=0 note=28 velocity=0 time=0
note_on channel=0 note=38 velocity=0 time=0
note_on channel=0 note=48 velocity=0 time=0
note_on channel=0 note=58 velocity=0 time=0
note_on channel=0 note=68 velocity=0 time=0
note_on channel=0 note=78 velocity=0 time=0
note_on channel=0 note=88 velocity=0 time=0
note_on channel=0 note=11 velocity=44 time=0
note_on channel=0 note=32 velocity=44 time=0
note_on channel=0 note=24 velocity=44 time=0
note_on channel=0 note=36 velocity=44 time=0
Closing Launchpad X LPX MIDI In
set_note_tuning(261.6255653005986, 11)
filter_note(False, 11, 0)
set_note_tuning(275.62199471997224, 21)
filter_note(False, 21, 0)
set_note_tuning(285.409707600653, 31)
filter_note(False, 31, 0)
filter_note(True, 41, 0)
filter_note(True, 51, 0)
filter_note(True, 61, 0)
filter_note(True, 71, 0)
filter_note(True, 81, 0)
set_note_tuning(294.32876096317347, 12)
filter_note(False, 12, 0)
set_note_tuning(310.07474405996874, 22)
filter_note(False, 22, 0)
set_note_tuning(327.0319566257483, 32)
filter_note(False, 32, 0)
filter_note(True, 42, 0)
filter_note(True, 52, 0)
filter_note(True, 62, 0)
filter_note(True, 72, 0)
filter_note(True, 82, 0)
set_note_tuning(331.11985608357014, 13)
filter_note(False, 13, 0)
set_note_tuning(348.8340870674648, 23)
filter_note(False, 23, 0)
set_note_tuning(367.4959929599629, 33)
filter_note(False, 33, 0)
set_note_tuning(380.5462768008707, 43)
filter_note(False, 43, 0)
filter_note(True, 53, 0)
filter_note(True, 63, 0)
filter_note(True, 73, 0)
filter_note(True, 83, 0)
filter_note(True, 14, 0)
set_note_tuning(392.43834795089793, 24)
filter_note(False, 24, 0)
set_note_tuning(413.4329920799583, 34)
filter_note(False, 34, 0)
set_note_tuning(436.0426088343311, 44)
filter_note(False, 44, 0)
filter_note(True, 54, 0)
filter_note(True, 64, 0)
filter_note(True, 74, 0)
filter_note(True, 84, 0)
filter_note(True, 15, 0)
set_note_tuning(441.49314144476017, 25)
filter_note(False, 25, 0)
set_note_tuning(465.1121160899531, 35)
filter_note(False, 35, 0)
set_note_tuning(490.5479349386224, 45)
filter_note(False, 45, 0)
filter_note(True, 55, 0)
filter_note(True, 65, 0)
filter_note(True, 75, 0)
filter_note(True, 85, 0)
filter_note(True, 16, 0)
set_note_tuning(496.6797841253552, 26)
filter_note(False, 26, 0)
set_note_tuning(523.2511306011972, 36)
filter_note(False, 36, 0)
filter_note(True, 46, 0)
filter_note(True, 56, 0)
filter_note(True, 66, 0)
filter_note(True, 76, 0)
filter_note(True, 86, 0)
filter_note(True, 17, 0)
filter_note(True, 27, 0)
filter_note(True, 37, 0)
filter_note(True, 47, 0)
filter_note(True, 57, 0)
filter_note(True, 67, 0)
filter_note(True, 77, 0)
filter_note(True, 87, 0)
filter_note(True, 18, 0)
filter_note(True, 28, 0)
filter_note(True, 38, 0)
filter_note(True, 48, 0)
filter_note(True, 58, 0)
filter_note(True, 68, 0)
filter_note(True, 78, 0)
filter_note(True, 88, 0)
"""
    assert capsys.readouterr().out == expected_output
