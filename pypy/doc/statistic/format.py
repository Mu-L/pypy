import py
import datetime
import dateutil
from dateutil import parser

import pylab
import matplotlib

def get_data(p):
    data = p.readlines()
    title = data[0].strip()
    axis = data[1].strip().split(',')
    data = [convert_data(t) for t in zip(*[l.strip().split(',') for l in data[2:]])]
    return title, axis, data

def convert_data(row):
    if not row:
        return []
    first = row[0]
    try:
        int(first)
        return [int(elt) for elt in row]
    except ValueError:
        pass
    try:
        float(first)
        return [float(elt) for elt in row]
    except ValueError:
        pass
    if first[0] == '"':
        return [elt[1:-1] for elt in row]
    return [parsedate(elt) for elt in row]

def parsedate(s):
    if len(s) <= 7:
        year, month = s.split("-")
        result = datetime.datetime(int(year), int(month), 1)
    else:
        result = parser.parse(s)
    return pylab.date2num(result)

colors = "brg"

def txt2png(p):
    print p
    title, axis, data = get_data(p)
    dates = data[0]

    release_title, release_axis, release_data = get_data( py.path.local("release_dates.csv") )
    release_dates, release_names = release_data
 
    sprint_title, sprint_axis, sprint_data = get_data( py.path.local("sprint_dates.csv") )
    sprint_locations, sprint_begin_dates, sprint_end_dates = sprint_data
 
    ax = pylab.subplot(111)
    for i, d in enumerate(data[1:]):
        args = [dates, d, colors[i]]
        pylab.plot_date(*args)

    for i, release_date in enumerate(release_dates):
        release_name = release_names[i]
        pylab.axvline(release_date, linewidth=2, color="g", alpha=0.5)
        ax.text(release_date, 0.0, release_name,
                fontsize=10,
                horizontalalignment='right',
                rotation='vertical')

    for i, location in enumerate(sprint_locations):
        begin = sprint_begin_dates[i]
        end   = sprint_end_dates[i]
        if float(begin) >= float(min(dates[0],dates[-1])):
            pylab.axvspan(begin, end, facecolor="y", alpha=0.2)
            ax.text(begin, 0.0, location,
                    fontsize=10,
                    horizontalalignment='right',
                    rotation='vertical')

    pylab.legend(axis[1:], "upper left")
    pylab.xlabel(axis[0])
    pylab.ylabel(axis[1])
    ticklabels = ax.get_xticklabels()
    pylab.setp(ticklabels, 'rotation', 45, size=9)
    ax.autoscale_view()
    ax.grid(True)
    pylab.title(title)

    pylab.savefig(p.purebasename + ".png")
    pylab.savefig(p.purebasename + ".eps")
 
if __name__ == '__main__':
    args = py.std.sys.argv
    if len(args) == 1:
        print "usage: %s <filenames> <--all>" % args[0]
        py.std.sys.exit()
    for arg in args[1:]:
        if arg == "--all":
            for p in py.path.local().listdir("*.txt"):
                py.std.os.system("python %s %s" % (args[0], p.basename))
        else:
            txt2png(py.path.local(arg))
