#!/usr/bin/env python

"""Script to make a job script from a pytemplate file. The variables to be
replaced in the pytemplate are `$STEPNUM`, `$REPNUM`, `$NEXTSTEP`,
`$CONFFILE`, and `$REPFILE`."""

from OneWrapper import clean_line

def parsing(sysargs):
    try:
        import argparse
        # TODO: implement for newer version of Python
    except:
        import optparse
        parser=optparse.OptionParser()
        parser.add_option('-N', '--stepnum', type="int")
        parser.add_option('-r', '--rep', type="string")
        parser.add_option('-d', '--delta_step', type="int")
        parser.add_option('--base', type="string")
        parser.add_option('--conf', type="string")
        parser.add_option('--repfile', type="string")
    (opts, args) = parser.parse_args(sysargs)
    return opts, args

from QuickPyTemplate import QuickPyTemplate
import sys, re
if __name__ == "__main__":
    tmpl = QuickPyTemplate()
    opts, args = parsing(sys.argv[1:])

    # get parameters from conf file
    conff = open(opts.conf, "r")
    for line in conff:
        splitter = clean_line(line)
        if (re.search("stepstyle", splitter[0], re.I)):
            stepstyle = splitter[1]
        if (re.search("repstyle", splitter[0], re.I)):
            repstyle = splitter[1]
        if (re.search("base", splitter[0], re.I)):
            opts.base = splitter[1]
        if (re.search("tistraj", splitter[0], re.I)):
            opts.tistraj = splitter[1]
    conff.close()

    opts.nextstep = stepstyle % (opts.stepnum + opts.delta_step)
    opts.stepnum = stepstyle % (opts.stepnum)
    opts.rep = repstyle % (opts.rep)

    tmpl.set_entry("\$STEPNUM", opts.stepnum)
    tmpl.set_entry("\$REPNUM", opts.rep)
    tmpl.set_entry("\$NEXTSTEP", opts.nextstep)
    tmpl.set_entry("\$CONFFILE", opts.conf)
    tmpl.set_entry("\$REPFILE", opts.repfile)
    tmpl.set_entry("\$MYBASE", opts.base) # needed to get the conf files in

    print tmpl.replace(args[0])



