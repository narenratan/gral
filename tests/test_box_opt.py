import os
import shlex
import shutil
from fractions import Fraction as F
from pathlib import Path

import pandas as pd
import pytest

from gral.box_opt import main, box_opt
from gral.utils import read_scl_file_as_ratios

TEST_DATA = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "scl_file, arg_str, expected_output",
    [
        (
            "baglama.scl",
            "",
            """
*        *        1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    16/11    5/3      15/8    

*        12/11    5/4      *        *        *       




*        *        11/8     *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        5/4      *        *        *       



Wrote baglama-template.csv

""",
        ),
        (
            "baglama.scl",
            "-f",
            """
*        15/8     243/128  2/1     

*        5/3      27/16    16/9    

*        16/11    3/2      128/81  

5/4      81/64    4/3      1024/729

12/11    9/8      32/27    *       

*        1/1      256/243  *       




*        *        *        2/1     

*        *        *        *       

*        *        3/2      *       

5/4      *        *        11/8    

*        *        *        *       

*        1/1      *        *       



Wrote baglama-template.csv

""",
        ),
        (
            "baglama.scl",
            "-b 5/4 2/1",
            """
*        1024/729 128/81   16/9     2/1      *       

*        *        16/11    5/3      15/8     *       

256/243  32/27    4/3      3/2      27/16    243/128 

*        12/11    5/4      *        *        *       

*        1/1      9/8      81/64    *        *       




*        *        *        2/1     

*        *        *        *       

*        *        3/2      *       

*        5/4      11/8     *       

1/1      *        *        *       



Wrote baglama-template.csv

""",
        ),
        (
            "baglama.scl",
            "-w 0 1",
            """
*        5/3      15/8     *        *        *       

5/4      1024/729 128/81   16/9     2/1      *       

256/243  32/27    4/3      3/2      27/16    243/128 

*        1/1      9/8      81/64    16/11    *       

*        *        *        12/11    *        *       




5/4      11/8     *        *        2/1     

*        *        *        3/2      *       

*        1/1      *        *        *       



Wrote baglama-template.csv

""",
        ),
        (
            "baglama.scl",
            "-p 20",
            """
*        *        16/11    5/3      15/8     *       

12/11    5/4      1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    *        *        *       




*        5/4      *        *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        *        11/8     *        *       



Wrote baglama-template.csv

""",
        ),
    ],
    ids=lambda x: x if len(x) < 100 else "",
)
def test_box_opt(scl_file, arg_str, expected_output, capsys, tmp_path):
    orig_dir = Path.cwd()
    try:
        os.chdir(tmp_path)
        shutil.copy2(TEST_DATA / scl_file, tmp_path)
        arg_list = shlex.split(f"{scl_file} {arg_str}")
        main(arg_list)
        output = capsys.readouterr().out
        # Output has solver logs at the beginning
        output_tail = "\n".join(
            output.split("\n")[-(expected_output.count("\n") + 1) :]
        )
        assert output_tail == expected_output
    finally:
        os.chdir(orig_dir)


def test_template_csv(tmp_path):
    scl_file = "baglama.scl"
    orig_dir = Path.cwd()
    expected_template_df = pd.DataFrame(
        {
            "ratio": ["5/4", "11/8", "3/2", "2"],
            "x": [2, 2, 3, 5],
            "y": [-1, 2, 1, 2],
        }
    )
    try:
        os.chdir(tmp_path)
        shutil.copy2(TEST_DATA / scl_file, tmp_path)
        main([scl_file])
        template_path = f"{Path(scl_file).stem}-template.csv"
        template_df = pd.read_csv(template_path)
        assert template_df.equals(expected_template_df)
    finally:
        os.chdir(orig_dir)


def test_box_opt_cents():
    scl_file = "ratios-and-cents.scl"
    scl_path = TEST_DATA / scl_file

    with pytest.raises(ValueError) as e:
        main([str(scl_path)])
    assert str(e.value) == "Scale contains tones specified in cents: 700.0"


def test_model(tmp_path):
    ratios = read_scl_file_as_ratios(TEST_DATA / "baglama.scl")
    A_df, model = box_opt(
        ratios,
        basis=[F(5, 4), F(3, 2)],
        pitch_grid_tol=50,
        objective_weights={"box": 1.0, "X_diff": 1e-4},
    )
    output_path = tmp_path / "model.pb.txt"
    print(output_path)
    model.export_to_file(str(output_path))
    output_model_str = output_path.read_text()
    ref_model_str = (TEST_DATA / "ref-model.pb.txt").read_text()
    assert output_model_str == ref_model_str
