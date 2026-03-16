# GRAL

Scripts accompanying the article *Another look at Wilson's keyboard mapping system*.

## gral-search

Apply the Gral method to 10/17:
```
> gral-search 10 17

Left Right    Mediant     a  b     c  d     s  t
 0/1   1/0        1/1     0  1     1  0    17 10
       1/1        1/2     0  1     1  1     7 10
 1/2              2/3     1  1     2  1     7  3
       2/3        3/5     1  2     2  3     4  3
       3/5        4/7     1  3     2  5     1  3
 4/7             7/12     4  3     7  5     1  2
7/12            10/17     7  3    12  5     1  1
```

Find the moments of symmetry from stacking a generator of 707.22 cents within
an octave of 1200 cents:
```
> gral-search 707.22 1200

 Left Right    Mediant     a  b     c  d          s      t
  0/1   1/0        1/1     0  1     1  0    1200.00 707.22
        1/1        1/2     0  1     1  1     492.78 707.22
  1/2              2/3     1  1     2  1     492.78 214.44
        2/3        3/5     1  2     2  3     278.34 214.44
        3/5        4/7     1  3     2  5      63.90 214.44
  4/7             7/12     4  3     7  5      63.90 150.54
 7/12            10/17     7  3    12  5      63.90  86.64
10/17            13/22    10  3    17  5      63.90  22.74
      13/22      23/39    10 13    17 22      41.16  22.74
      23/39      33/56    10 23    17 39      18.42  22.74
33/56            56/95    33 23    56 39      18.42   4.32
```


## scale-degree

Map the scale in `baglama.scl` by scale degree using x step size 1, y step size 3:
```
> scale-degree baglama.scl -s 1 3

21.      22.      23.      24.      25.      26.      27.      28.     
64/27    5/2      81/32    8/3      2048/729 32/11    3/1      256/81  
1494     1586     1608     1698     1788     1849     1902     1992    

18.      19.      20.      21.      22.      23.      24.      25.     
512/243  24/11    9/4      64/27    5/2      81/32    8/3      2048/729
1290     1351     1404     1494     1586     1608     1698     1788    

15.      16.      17.      18.      19.      20.      21.      22.     
15/8     243/128  2/1      512/243  24/11    9/4      64/27    5/2     
1088     1110     1200     1290     1351     1404     1494     1586    

12.      13.      14.      15.      16.      17.      18.      19.     
5/3      27/16    16/9     15/8     243/128  2/1      512/243  24/11   
884      906      996      1088     1110     1200     1290     1351    

9.       10.      11.      12.      13.      14.      15.      16.     
16/11    3/2      128/81   5/3      27/16    16/9     15/8     243/128 
649      702      792      884      906      996      1088     1110    

6.       7.       8.       9.       10.      11.      12.      13.     
81/64    4/3      1024/729 16/11    3/2      128/81   5/3      27/16   
408      498      588      649      702      792      884      906     

3.       4.       5.       6.       7.       8.       9.       10.     
9/8      32/27    5/4      81/64    4/3      1024/729 16/11    3/2     
204      294      386      408      498      588      649      702     

0.       1.       2.       3.       4.       5.       6.       7.      
1/1      256/243  12/11    9/8      32/27    5/4      81/64    4/3     
0        90       151      204      294      386      408      498     
```
If a Novation Launchpad X is connected, the tuning is set with MTS-ESP.

The position of 1/1 on the keyboard can be set with `-o`, e.g.
`scale-degree baglama.scl -s 1 3 -o 2 1`.


## harmonic-template

Map the scale in `baglama.scl` by the harmonic template in `template.csv`:
```
> harmonic-template baglama.scl -t template.csv



*        5/3      15/8     *        *        *       

5/4      1024/729 128/81   16/9     2/1      *       

256/243  32/27    4/3      3/2      27/16    243/128 

*        1/1      9/8      81/64    16/11    *       

*        *        *        12/11    *        *       




5/4      11/8     *        *        2/1     

*        *        *        3/2      *       

*        1/1      *        *        *    


```

Here `template.csv` contains the harmonic template in the form:
```
ratio,x,y
2,3,2
3/2,2,1
5/4,-1,2
11/8,0,2
```

If a Novation Launchpad X is connected, the tuning is set with MTS-ESP.

The position of 1/1 on the keyboard can be set with `-o`, e.g.
`harmonic-template baglama.scl -t template.csv -o 2 1`.

## box-opt

Find a harmonic template which maps the scale in `baglama.scl` into a small box
on the keyboard:
```
> box-opt baglama.scl
...


*        *        1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    16/11    5/3      15/8    

*        12/11    5/4      *        *        *       




*        *        11/8     *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        5/4      *        *        *       



Wrote baglama-template.csv
```

Specify that 5/4 and 2/1 should form a keyboard basis:
```
> box-opt baglama.scl -b 5/4 2/1
...


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
```

The optimization minimizes two things:
- the size of the box the scale fits into on the keyboard
- the sum of the (taxicab) distances between each scale note

The weights for each term can be specified with `-w`. For example to ignore the
box size and consider only the sum of distances you can run
`box-opt baglama.scl -w 0 1`.

If you'd like the keyboard mapping to be close to a regular grid of pitches,
you can pass a pitch grid tolerance with `-p`. For example:
```
> box-opt baglama.scl -p 20
...


g[x] = 203.08 cents
g[y] =  85.32 cents



*        *        16/11    5/3      15/8     *       

12/11    5/4      1024/729 128/81   16/9     2/1     

256/243  32/27    4/3      3/2      27/16    243/128 

1/1      9/8      81/64    *        *        *       




*        5/4      *        *        *        2/1     

*        *        *        3/2      *        *       

1/1      *        *        *        *        *       

*        *        *        11/8     *        *       



Wrote baglama-template.csv
```
The step sizes for the grid are printed; here every note is within 20 cents of
a grid with x step size 203.08 cents, y step size 85.32 cents.
