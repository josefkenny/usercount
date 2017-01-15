set datafile separator ","
plot "< tail -24 usercount.csv" using 1:2
daylow = GPVAL_DATA_Y_MIN
dayhigh = GPVAL_DATA_Y_MAX

plot "usercount.csv" using 1:2
wholelow = GPVAL_DATA_Y_MIN
wholehigh = GPVAL_DATA_Y_MAX
wholelast = GPVAL_DATA_X_MAX

set terminal png truecolor size 1464,660 enhanced font "./fonts/RobotoCond.ttf" 17 background rgb "#282d37"
set output 'graph.png'



# derivative functions.  Return 1/0 for first point, otherwise delta y or (delta y)/(delta x)
d(y) = ($0 == 0) ? (y1 = y, 1/0) : (y2 = y1, y1 = y, y1-y2)
d2(x,y) = ($0 == 0) ? (x1 = x, y1 = y, 1/0) : (x2 = x1, x1 = x, y2 = y1, y1 = y, (y1-y2)/(x1-x2))

# change a color of border.
set border lw 3 lc rgb "white"

# change text colors of  tics
set xtics textcolor rgb "white"
set ytics textcolor rgb "white"

# change text colors of labels
set xlabel "X" textcolor rgb "white"
set ylabel "Y" textcolor rgb "white"

# change a text color of key
set key textcolor rgb "white"

lmarg = 12
marg1 = 1
marg2 = 6
rmarg = 9


set multiplot layout 1, 2

set tics front

set xtics nomirror
set ytics nomirror

# GRAPH 1 - DAILY
set lmargin lmarg
set rmargin marg1

set yr [daylow:dayhigh]

set title "Last 24 hours" textcolor rgb "white"
set ylabel "Number of users" textcolor rgb "#93ddff"
set xlabel ""
set autoscale xfix
set xdata time
set timefmt "%s"
set format x "%a\n%k:%M"
set xtics 21600

set y2range [0:50]

set style line 12 lc rgb "#FEFEFE" lt 1 lw 5
set grid

plot "< tail -25 usercount.csv" every ::1 using 1:2 w filledcurves x1 title '' lc rgb "#2e85ad", \
        '' u ($1):(d($2)) w filledcurves x1 title '' axes x1y2 fs transparent solid 0.7 noborder lc rgb "#E9967A"


# GRAPH 2 - WHOLE
set lmargin marg2
set rmargin rmarg

set yr [wholelow:wholehigh]

set title "Since November 29th" textcolor rgb "white"
set ylabel ""
set autoscale xfix
set xdata time
set timefmt "%s"
set format x "%a\n%d %b"
set xtics 592200

set y2range [0:50]
set y2tics 5 nomirror
set y2label 'Hourly increase' textcolor rgb "#E9967A" 

set style line 12 lc rgb "#FEFEFE" lt 1 lw 5
set grid


lastday = wholelast - 84600
set arrow from lastday,wholelow to lastday,wholehigh nohead front lw 2 lc rgb "white"

plot "usercount.csv" every ::1 using 1:2 w filledcurves x1 title '' lc rgb "#2e85ad", \
        '' u ($1):(d($2)) w filledcurves x1 title '' axes x1y2 fs transparent solid 0.7 noborder lc rgb "#E9967A"




unset multiplot
