import shlex
import signal
from contextlib import nullcontext
from pathlib import Path

import pytest
import mido
import mtsespy as mts

from gral.scale_degree import main
from .mocks import mock_open_output, printer

TEST_DATA = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "scl_file, arg_str, expected_output",
    [
        (
            "baglama.scl",
            "-s 1 2",
            """
14.      15.      16.      17.      18.      19.      20.      21.     
16/9     15/8     243/128  2/1      512/243  24/11    9/4      64/27   
996      1088     1110     1200     1290     1351     1404     1494    

12.      13.      14.      15.      16.      17.      18.      19.     
5/3      27/16    16/9     15/8     243/128  2/1      512/243  24/11   
884      906      996      1088     1110     1200     1290     1351    

10.      11.      12.      13.      14.      15.      16.      17.     
3/2      128/81   5/3      27/16    16/9     15/8     243/128  2/1     
702      792      884      906      996      1088     1110     1200    

8.       9.       10.      11.      12.      13.      14.      15.     
1024/729 16/11    3/2      128/81   5/3      27/16    16/9     15/8    
588      649      702      792      884      906      996      1088    

6.       7.       8.       9.       10.      11.      12.      13.     
81/64    4/3      1024/729 16/11    3/2      128/81   5/3      27/16   
408      498      588      649      702      792      884      906     

4.       5.       6.       7.       8.       9.       10.      11.     
32/27    5/4      81/64    4/3      1024/729 16/11    3/2      128/81  
294      386      408      498      588      649      702      792     

2.       3.       4.       5.       6.       7.       8.       9.      
12/11    9/8      32/27    5/4      81/64    4/3      1024/729 16/11   
151      204      294      386      408      498      588      649     

0.       1.       2.       3.       4.       5.       6.       7.      
1/1      256/243  12/11    9/8      32/27    5/4      81/64    4/3     
0        90       151      204      294      386      408      498     

Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "baglama.scl",
            "-s 2 3",
            """
21.      23.      25.      27.      29.      31.      33.      35.     
64/27    81/32    2048/729 3/1      10/3     32/9     243/64   1024/243
1494     1608     1788     1902     2084     2196     2310     2490    

18.      20.      22.      24.      26.      28.      30.      32.     
512/243  9/4      5/2      8/3      32/11    256/81   27/8     15/4    
1290     1404     1586     1698     1849     1992     2106     2288    

15.      17.      19.      21.      23.      25.      27.      29.     
15/8     2/1      24/11    64/27    81/32    2048/729 3/1      10/3    
1088     1200     1351     1494     1608     1788     1902     2084    

12.      14.      16.      18.      20.      22.      24.      26.     
5/3      16/9     243/128  512/243  9/4      5/2      8/3      32/11   
884      996      1110     1290     1404     1586     1698     1849    

9.       11.      13.      15.      17.      19.      21.      23.     
16/11    128/81   27/16    15/8     2/1      24/11    64/27    81/32   
649      792      906      1088     1200     1351     1494     1608    

6.       8.       10.      12.      14.      16.      18.      20.     
81/64    1024/729 3/2      5/3      16/9     243/128  512/243  9/4     
408      588      702      884      996      1110     1290     1404    

3.       5.       7.       9.       11.      13.      15.      17.     
9/8      5/4      4/3      16/11    128/81   27/16    15/8     2/1     
204      386      498      649      792      906      1088     1200    

0.       2.       4.       6.       8.       10.      12.      14.     
1/1      12/11    32/27    81/64    1024/729 3/2      5/3      16/9    
0        151      294      408      588      702      884      996     

Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "baglama.scl",
            "-s 3 4 -o 1 2",
            """
17.      20.      23.      26.      29.      32.      35.      38.     
2/1      9/4      81/32    32/11    10/3     15/4     1024/243 128/27  
1200     1404     1608     1849     2084     2288     2490     2694    

13.      16.      19.      22.      25.      28.      31.      34.     
27/16    243/128  24/11    5/2      2048/729 256/81   32/9     4/1     
906      1110     1351     1586     1788     1992     2196     2400    

9.       12.      15.      18.      21.      24.      27.      30.     
16/11    5/3      15/8     512/243  64/27    8/3      3/1      27/8    
649      884      1088     1290     1494     1698     1902     2106    

5.       8.       11.      14.      17.      20.      23.      26.     
5/4      1024/729 128/81   16/9     2/1      9/4      81/32    32/11   
386      588      792      996      1200     1404     1608     1849    

1.       4.       7.       10.      13.      16.      19.      22.     
256/243  32/27    4/3      3/2      27/16    243/128  24/11    5/2     
90       294      498      702      906      1110     1351     1586    

-3.      0.       3.       6.       9.       12.      15.      18.     
8/9      1/1      9/8      81/64    16/11    5/3      15/8     512/243 
-204     0        204      408      649      884      1088     1290    

-7.      -4.      -1.      2.       5.       8.       11.      14.     
3/4      27/32    243/256  12/11    5/4      1024/729 128/81   16/9    
-498     -294     -90      151      386      588      792      996     

-11.     -8.      -5.      -2.      1.       4.       7.       10.     
81/128   8/11     5/6      15/16    256/243  32/27    4/3      3/2     
-792     -551     -316     -112     90       294      498      702     

Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "cents.scl",
            "-s 1 2",
            """
14.  15.  16.  17.  18.  19.  20.  21. 
 .   8/1   .    .    .    .   16/1  .  
3175 3600 3825 4025 4300 4375 4800 5025

12.  13.  14.  15.  16.  17.  18.  19. 
 .    .    .   8/1   .    .    .    .  
2825 3100 3175 3600 3825 4025 4300 4375

10.  11.  12.  13.  14.  15.  16.  17. 
4/1   .    .    .    .   8/1   .    .  
2400 2625 2825 3100 3175 3600 3825 4025

8.   9.   10.  11.  12.  13.  14.  15. 
 .    .   4/1   .    .    .    .   8/1 
1900 1975 2400 2625 2825 3100 3175 3600

6.   7.   8.   9.   10.  11.  12.  13. 
 .    .    .    .   4/1   .    .    .  
1425 1625 1900 1975 2400 2625 2825 3100

4.   5.   6.   7.   8.   9.   10.  11. 
 .   2/1   .    .    .    .   4/1   .  
775  1200 1425 1625 1900 1975 2400 2625

2.   3.   4.   5.   6.   7.   8.   9.  
 .    .    .   2/1   .    .    .    .  
425  700  775  1200 1425 1625 1900 1975

0.   1.   2.   3.   4.   5.   6.   7.  
1/1   .    .    .    .   2/1   .    .  
0    225  425  700  775  1200 1425 1625

Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "ratios-and-cents.scl",
            "-s 1 2",
            """
14.  15.  16.  17.  18.  19.  20.  21. 
20/3 8/1  9/1  10/1  .   40/3 16/1 18/1
3284 3600 3804 3986 4300 4484 4800 5004

12.  13.  14.  15.  16.  17.  18.  19. 
5/1   .   20/3 8/1  9/1  10/1  .   40/3
2786 3100 3284 3600 3804 3986 4300 4484

10.  11.  12.  13.  14.  15.  16.  17. 
4/1  9/2  5/1   .   20/3 8/1  9/1  10/1
2400 2604 2786 3100 3284 3600 3804 3986

8.   9.   10.  11.  12.  13.  14.  15. 
 .   10/3 4/1  9/2  5/1   .   20/3 8/1 
1900 2084 2400 2604 2786 3100 3284 3600

6.   7.   8.   9.   10.  11.  12.  13. 
9/4  5/2   .   10/3 4/1  9/2  5/1   .  
1404 1586 1900 2084 2400 2604 2786 3100

4.   5.   6.   7.   8.   9.   10.  11. 
5/3  2/1  9/4  5/2   .   10/3 4/1  9/2 
884  1200 1404 1586 1900 2084 2400 2604

2.   3.   4.   5.   6.   7.   8.   9.  
5/4   .   5/3  2/1  9/4  5/2   .   10/3
386  700  884  1200 1404 1586 1900 2084

0.   1.   2.   3.   4.   5.   6.   7.  
1/1  9/8  5/4   .   5/3  2/1  9/4  5/2 
0    204  386  700  884  1200 1404 1586

Could not open Launchpad X LPX MIDI In
""",
        ),
        (
            "nonoctave.scl",
            "-s 1 2",
            """
14.  15.  16.  17.  18.  19.  20.  21. 
 .    .    .    .    .    .    .    .  
3177 3603 3828 4028 4303 4378 4804 5029

12.  13.  14.  15.  16.  17.  18.  19. 
 .    .    .    .    .    .    .    .  
2827 3102 3177 3603 3828 4028 4303 4378

10.  11.  12.  13.  14.  15.  16.  17. 
 .    .    .    .    .    .    .    .  
2402 2627 2827 3102 3177 3603 3828 4028

8.   9.   10.  11.  12.  13.  14.  15. 
 .    .    .    .    .    .    .    .  
1901 1976 2402 2627 2827 3102 3177 3603

6.   7.   8.   9.   10.  11.  12.  13. 
 .    .    .    .    .    .    .    .  
1426 1626 1901 1976 2402 2627 2827 3102

4.   5.   6.   7.   8.   9.   10.  11. 
 .    .    .    .    .    .    .    .  
775  1201 1426 1626 1901 1976 2402 2627

2.   3.   4.   5.   6.   7.   8.   9.  
 .    .    .    .    .    .    .    .  
425  700  775  1201 1426 1626 1901 1976

0.   1.   2.   3.   4.   5.   6.   7.  
1/1   .    .    .    .    .    .    .  
0    225  425  700  775  1201 1426 1626

Could not open Launchpad X LPX MIDI In
""",
        ),
    ],
    ids=lambda x: x if len(x) < 100 else "",
)
def test_scale_degree(scl_file, arg_str, expected_output, capsys):
    with pytest.raises(SystemExit) as e:
        scl_path = TEST_DATA / scl_file
        arg_list = shlex.split(f"{scl_path} {arg_str}")
        main(arg_list)
    assert e.value.code == 1
    assert capsys.readouterr().out == expected_output


def test_scale_degree_mocked(monkeypatch, capsys):
    """
    Test tuning and MIDI message sending with mocks.
    """
    monkeypatch.setattr(mido, "open_output", mock_open_output)
    monkeypatch.setattr(signal, "pause", lambda: None)
    monkeypatch.setattr(mts, "Master", nullcontext)
    monkeypatch.setattr(mts, "set_note_tuning", printer("set_note_tuning"))

    scl_file = "baglama.scl"
    scl_path = TEST_DATA / scl_file
    main(shlex.split(f"{scl_path} -s 1 2"))
    expected_output = """
14.      15.      16.      17.      18.      19.      20.      21.     
16/9     15/8     243/128  2/1      512/243  24/11    9/4      64/27   
996      1088     1110     1200     1290     1351     1404     1494    

12.      13.      14.      15.      16.      17.      18.      19.     
5/3      27/16    16/9     15/8     243/128  2/1      512/243  24/11   
884      906      996      1088     1110     1200     1290     1351    

10.      11.      12.      13.      14.      15.      16.      17.     
3/2      128/81   5/3      27/16    16/9     15/8     243/128  2/1     
702      792      884      906      996      1088     1110     1200    

8.       9.       10.      11.      12.      13.      14.      15.     
1024/729 16/11    3/2      128/81   5/3      27/16    16/9     15/8    
588      649      702      792      884      906      996      1088    

6.       7.       8.       9.       10.      11.      12.      13.     
81/64    4/3      1024/729 16/11    3/2      128/81   5/3      27/16   
408      498      588      649      702      792      884      906     

4.       5.       6.       7.       8.       9.       10.      11.     
32/27    5/4      81/64    4/3      1024/729 16/11    3/2      128/81  
294      386      408      498      588      649      702      792     

2.       3.       4.       5.       6.       7.       8.       9.      
12/11    9/8      32/27    5/4      81/64    4/3      1024/729 16/11   
151      204      294      386      408      498      588      649     

0.       1.       2.       3.       4.       5.       6.       7.      
1/1      256/243  12/11    9/8      32/27    5/4      81/64    4/3     
0        90       151      204      294      386      408      498     

Opening Launchpad X LPX MIDI In
note_on channel=0 note=11 velocity=44 time=0
note_on channel=0 note=21 velocity=0 time=0
note_on channel=0 note=31 velocity=0 time=0
note_on channel=0 note=41 velocity=0 time=0
note_on channel=0 note=51 velocity=0 time=0
note_on channel=0 note=61 velocity=0 time=0
note_on channel=0 note=71 velocity=0 time=0
note_on channel=0 note=81 velocity=0 time=0
note_on channel=0 note=12 velocity=0 time=0
note_on channel=0 note=22 velocity=0 time=0
note_on channel=0 note=32 velocity=0 time=0
note_on channel=0 note=42 velocity=0 time=0
note_on channel=0 note=52 velocity=0 time=0
note_on channel=0 note=62 velocity=0 time=0
note_on channel=0 note=72 velocity=0 time=0
note_on channel=0 note=82 velocity=0 time=0
note_on channel=0 note=13 velocity=0 time=0
note_on channel=0 note=23 velocity=0 time=0
note_on channel=0 note=33 velocity=0 time=0
note_on channel=0 note=43 velocity=0 time=0
note_on channel=0 note=53 velocity=0 time=0
note_on channel=0 note=63 velocity=0 time=0
note_on channel=0 note=73 velocity=0 time=0
note_on channel=0 note=83 velocity=0 time=0
note_on channel=0 note=14 velocity=0 time=0
note_on channel=0 note=24 velocity=0 time=0
note_on channel=0 note=34 velocity=0 time=0
note_on channel=0 note=44 velocity=0 time=0
note_on channel=0 note=54 velocity=0 time=0
note_on channel=0 note=64 velocity=0 time=0
note_on channel=0 note=74 velocity=0 time=0
note_on channel=0 note=84 velocity=44 time=0
note_on channel=0 note=15 velocity=0 time=0
note_on channel=0 note=25 velocity=0 time=0
note_on channel=0 note=35 velocity=0 time=0
note_on channel=0 note=45 velocity=0 time=0
note_on channel=0 note=55 velocity=0 time=0
note_on channel=0 note=65 velocity=0 time=0
note_on channel=0 note=75 velocity=0 time=0
note_on channel=0 note=85 velocity=0 time=0
note_on channel=0 note=16 velocity=0 time=0
note_on channel=0 note=26 velocity=0 time=0
note_on channel=0 note=36 velocity=0 time=0
note_on channel=0 note=46 velocity=0 time=0
note_on channel=0 note=56 velocity=0 time=0
note_on channel=0 note=66 velocity=0 time=0
note_on channel=0 note=76 velocity=44 time=0
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
note_on channel=0 note=68 velocity=44 time=0
note_on channel=0 note=78 velocity=0 time=0
note_on channel=0 note=88 velocity=0 time=0
Closing Launchpad X LPX MIDI In
set_note_tuning(261.62600000000003, 11)
set_note_tuning(285.41018181818185, 21)
set_note_tuning(310.0752592592592, 31)
set_note_tuning(331.1204062500002, 41)
set_note_tuning(367.4966035665295, 51)
set_note_tuning(392.439, 61)
set_note_tuning(436.0433333333335, 71)
set_note_tuning(465.112888888889, 81)
set_note_tuning(275.6224526748971, 12)
set_note_tuning(294.32925, 22)
set_note_tuning(327.03250000000014, 32)
set_note_tuning(348.83466666666675, 42)
set_note_tuning(380.54690909090914, 52)
set_note_tuning(413.43367901234564, 62)
set_note_tuning(441.49387500000023, 72)
set_note_tuning(490.54875000000015, 82)
set_note_tuning(285.41018181818185, 13)
set_note_tuning(310.0752592592592, 23)
set_note_tuning(331.1204062500002, 33)
set_note_tuning(367.4966035665295, 43)
set_note_tuning(392.439, 53)
set_note_tuning(436.0433333333335, 63)
set_note_tuning(465.112888888889, 73)
set_note_tuning(496.68060937500024, 83)
set_note_tuning(294.32925, 14)
set_note_tuning(327.03250000000014, 24)
set_note_tuning(348.83466666666675, 34)
set_note_tuning(380.54690909090914, 44)
set_note_tuning(413.43367901234564, 54)
set_note_tuning(441.49387500000023, 64)
set_note_tuning(490.54875000000015, 74)
set_note_tuning(523.2520000000001, 84)
set_note_tuning(310.0752592592592, 15)
set_note_tuning(331.1204062500002, 25)
set_note_tuning(367.4966035665295, 35)
set_note_tuning(392.439, 45)
set_note_tuning(436.0433333333335, 55)
set_note_tuning(465.112888888889, 65)
set_note_tuning(496.68060937500024, 75)
set_note_tuning(551.2449053497942, 85)
set_note_tuning(327.03250000000014, 16)
set_note_tuning(348.83466666666675, 26)
set_note_tuning(380.54690909090914, 36)
set_note_tuning(413.43367901234564, 46)
set_note_tuning(441.49387500000023, 56)
set_note_tuning(490.54875000000015, 66)
set_note_tuning(523.2520000000001, 76)
set_note_tuning(570.8203636363637, 86)
set_note_tuning(331.1204062500002, 17)
set_note_tuning(367.4966035665295, 27)
set_note_tuning(392.439, 37)
set_note_tuning(436.0433333333335, 47)
set_note_tuning(465.112888888889, 57)
set_note_tuning(496.68060937500024, 67)
set_note_tuning(551.2449053497942, 77)
set_note_tuning(588.6585, 87)
set_note_tuning(348.83466666666675, 18)
set_note_tuning(380.54690909090914, 28)
set_note_tuning(413.43367901234564, 38)
set_note_tuning(441.49387500000023, 48)
set_note_tuning(490.54875000000015, 58)
set_note_tuning(523.2520000000001, 68)
set_note_tuning(570.8203636363637, 78)
set_note_tuning(620.1505185185184, 88)
"""
    assert capsys.readouterr().out == expected_output
