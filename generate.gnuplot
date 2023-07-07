# We need this to make the script work on some versions of gnuplot
set term dumb

if (!exists("csvname")) csvname="mastostats.csv"
if (!exists("graphname")) graphname="graph.png"
if (!exists("servername")) servername="tooot.im"

# derivative functions.  Return 1/0 for first point, otherwise delta y or (delta y)/(delta x)
d(y) = ($0 == 0) ? (y1 = y, 1/0) : (y2 = y1, y1 = y, y1-y2)
d2(x,y) = ($0 == 0) ? (x1 = x, y1 = y, 1/0) : (x2 = x1, x1 = x, y2 = y1, y1 = y, (y1-y2)/(x1-x2))

# Set length of time for the entire graph
day = 24*60*60
week = 7*day
timespan = week

# Set tic width
tic_width = day

# We're going to be using comma-separated values, so set this up
set datafile separator ","

# 'Pre-plot' the two charts "invisibly" first, to get the bounds of the data
# Interestingly, if you have your terminal set up with 'sixel' output, that's where they'll appear! Neato.

# Set pre-plot settings common to each plot
set xrange [time(0) - timespan:]

# Plot 'usercount' of the past week and get bounds (for GRAPH 1 y1)
plot csvname using 1:2
usercountlow = GPVAL_DATA_Y_MIN
usercounthigh = GPVAL_DATA_Y_MAX

# Plot derivative of 'usercount' of the past week and get bounds (for GRAPH 1 y2)
plot csvname using ($1):(d($2))
uc_derivative_low = GPVAL_DATA_Y_MIN
uc_derivative_high = GPVAL_DATA_Y_MAX

# Plot derivative of 'tootscount' of the past week and get bounds (for GRAPH 2 y1)
plot csvname using ($1):(d($3))
tootslow  = GPVAL_DATA_Y_MIN
tootshigh = GPVAL_DATA_Y_MAX
tootslast = GPVAL_DATA_X_MAX

###############################################################################
# SETUP
###############################################################################

# Set up our fonts and such
set terminal png truecolor size 1464,330 enhanced font "./fonts/RobotoCond.ttf" 12 background rgb "#282d37"
set output graphname

# Set border colour and line width
set border lw 3 lc rgb "white"

# Set colours of the tics
set xtics textcolor rgb "white"
set ytics textcolor rgb "white"

# Set text colors of labels
set xlabel "X" textcolor rgb "white"
set ylabel "Y" textcolor rgb "white"

# Set the text colour of the key
set key textcolor rgb "white"

# Draw tics after the other elements, so they're not overlapped
set tics front

# Set layout into multiplot mode (2 rows by 1 column = 2 plots)
set multiplot layout 1, 2

# Make sure we don't draw tics on the opposite side of the graph
set xtics nomirror
set ytics nomirror



# Set margin sizes
tmarg = 1       # Top margin
cmarg = 0       # Centre margin
bmarg = 2.5     # Bottom margin

lmarg = 12      # Left margin
rmarg = 9       # Right margin



###############################################################################
# GRAPH 1
# Current usercount & the derivative (rate of new users joining) (last 7 days)
###############################################################################

# Set top graph margins
set tmargin tmarg
set lmargin lmarg
set rmargin rmarg

# Set Y axis
set yr [usercountlow:usercounthigh]
if (usercountlow == usercounthigh) set yr [usercountlow:usercounthigh+1]
set ylabel servername."\nNumber of users" textcolor rgb "#93ddff" offset 1,0,0

# Set Y2 axis
set y2r [0:uc_derivative_high * 2]
if (uc_derivative_high == 0) set y2r [-1:1]
set y2tics 10 nomirror
set y2label 'Hourly increase' textcolor rgb "#7ae9d8"

# Set X axis
set xdata time
set xrange [time(0) - timespan:]
set timefmt "%s"
set xlabel ""
set autoscale xfix

# Make the tics invisible, but continue to show the grid
set tics scale 0
set xtics tic_width
set format x ""


# Overall graph style
set style line 12 lc rgb "#FEFEFE" lt 1 lw 5
set grid

# Plot the graph
plot csvname every ::1 using 1:2 w filledcurves x1 title '' lc rgb "#2e85ad", \
        '' u ($1):(d($2)) w filledcurves x1 title '' axes x1y2 fs transparent solid 0.7 noborder lc rgb "#7ae9d8"



###############################################################################
# GRAPH 2
# Number of toots per hour
###############################################################################

# Unset things from the previous graph
unset y2tics        # Remove y2 tics (only one y axis on this graph)
unset y2label       # Remove y2 label (only one y axis on this graph)

# Set bottom graph margins
set tmargin cmarg
set bmargin bmarg
set lmargin lmarg
set rmargin rmarg

# Set Y axis
set yr [0:tootshigh]
set ylabel "Toots per hour" textcolor rgb "#E9967A"

# Set X axis
set xdata time
set xrange [time(0) - timespan:]
set timefmt "%s"
set format x "%a\n%d %b"
set xtics tic_width

# Overall graph style
set style line 12 lc rgb "#FEFEFE" lt 1 lw 5
set grid

# Plot the graph
plot csvname every ::1 using ($1):(d($3)) w filledcurves x1 title '' lc rgb "#E9967A"


# I think this needs to be here for some reason
unset multiplot