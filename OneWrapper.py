#!/usr/bin/env python

# OneWrapper.py
#   Very simple scripts for general parallel replica exchange.
#   Written by David W.H. Swenson
#   Current version 2013-12-09

# Prefers Python 2.7 or later for some of the functions from subprocess,
# although we duck-punch in some stuff to get Py2.6 to work. Includes
# support for both optparse and argparse, so we're flexible with Py3.x. 
import subprocess, re, random
import os, sys, errno

# A little duck-punching hack to get this to kind-of work with Python 2.6
# (why can't we just have a decent module-based python setup on our
# cluster?). Stolen from http://stackoverflow.com/a/13160748 
if "check_output" not in dir( subprocess ): # duck punch it in!
    def f(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output
    subprocess.check_output = f


def clean_line(line):
    """ Cleans out comment lines and splits up result by whitespace, so that
    we can then do the specific parsing tasks needed.
    """
    line = re.sub('\#.*', '', line) # kill comments
    line = re.sub('^\s*', '', line) # kill blank space at start
    line = re.sub('\s*$', '', line) # kill blank space at end
    splitter = re.split('\s+', line) # split line into words
    return splitter


class OneWrapper(object):

    def __init__(self,sysargs):
        opts,args = self.parsing(sysargs)
        self.conffile=  args[1]
        self.stepnum = opts.N
        self.finished = opts.r

        self.movers = []
        moverlist = [] 


        # now read the conffile
        # in here, we need to set the movetypes (and related arrays)
        conff = open(self.conffile, "r")
        for line in conff:
            splitter = clean_line(line)
            if (re.search("move(_)?type", splitter[0], re.I)):
                mymover = { }
                mymover['name'] = splitter[1]
                mymover['freq'] = splitter[2]
                mymover['step'] = splitter[3]
                mymover['type'] = splitter[4]
                mymover['conf'] = splitter[5]
                moverlist.append(mymover)

            if (re.search("^(max)?(_)?(n)?step(s)?$", splitter[0], re.I)):
                self.maxsteps = int(splitter[1])

            if (re.search("base", splitter[0], re.I)):
                self.basedir = splitter[1]

        totfreq = 0.0
        for moverline in moverlist:
            totfreq+=int(moverline['freq'])
            mover=None
            if (re.search("repex(_)?(swapper)?", moverline['type'], re.I)):
                mover=RepExSwapper(self, moverline)
                pass
            if (re.search("script(_)?(launcher)?", moverline['type'], re.I)):
                mover=ScriptLauncher(self, moverline)
                pass
            
            self.movers.append(mover)

        self.cumprob = []
        newtot = 0.0
        for moverline in moverlist:
            newtot+=int(moverline['freq'])
            self.cumprob.append(float(newtot)/float(totfreq))

        #print self.cumprob
        waitfile=self.basedir+"/WAITFILE"
        self.waiting = Waitdir(waitfile)

        return
    
    def parsing(self,sysargs):
        try:
            import argparse
            parser=argparse.ArgumentParser()
            parser.add_argument("-N", type="int", help="step number",\
                default=0)
            parser.add_argument("-r", type="string", \
                help="label of finished replica")
            (opts, args) = parser.parse_args(sysargs)
        except:
            import optparse
            parser=optparse.OptionParser()
            parser.add_option("-N", type="int", help="step number", \
                default=0)
            parser.add_option("-r", type="string", \
                help="label of finished replica")
            (opts, args) = parser.parse_args(sysargs)
        return (opts, args)

    def movetype(self):
        """Selects a random move type (number) from the list of moves parsed
        by the conf file.
        """
        rand = random.random()
        move=0
        while (self.cumprob[move] < rand):
            move+=1
        return move

    def run(self,stepnum):
        """Main function for this calculation class.
        """
        if (self.waiting.update(self.finished)==0):
            self.stepnum = stepnum
            recur = True
            while (recur and (self.stepnum < self.maxsteps)):
                # now we get to try a move!
                print "Doing move for step ", self.stepnum
                move = self.movetype()
                mymover = self.movers[move]
                self.waiting.build(mymover)
                recur = mymover.doMove(stepnum)
                self.stepnum += mymover.step
        return

# #######################################################################

# Various waiting objects: file-based or directory-based. Expected to quack
# properly with init(name), build(mover), and update(rep)
class Waitfile(object):
    """File based job control. This has been mostly abandonned."""
    
    def __init__(self, fname):
        self.fname = fname
        return

    def build(self, mover):
        """Assuming that mover is an object with a list called replicas, this
        appends each of the replica labels to the waitfile in fname.
        """
        try:
            reps = mover.replicas
        except:
            reps = []
        f = open(self.fname, 'a')
        # possibly lock it, just to be safe? shouldn't be needed tho
        for rep in reps:
            f.write(rep+"\n")
        f.close()
        return len(reps)

    def update(self, rep):
        """Read in WAITLIST file while ignoring the replica we just
        finished; write it back out without our replica, and return the
        number of remaining entries.
        """
        import fcntl
        # open waitfile, lock it
        try:
            f = open(self.fname, 'r+')
        except:
            # open for writing and close it to create an empty file
            f = open(self.fname, 'w')
            f.close()
            f = open(self.fname, 'r+')
        fcntl.flock(f, fcntl.LOCK_EX)
        print "Locked "+self.fname
        print "Removing replica", rep
        # read in the replicas, except the one that matches ours
        waitlist = []
        for ll in f:
            line=clean_line(ll)[0]
            #print "Reading "+line+" ",
            if (line!=rep):
                waitlist.append(line)
                #print "Appended!",
            #print
        # write back out the new waitfile
        f.seek(0)
        for line in waitlist:
            #print "Writing "+line
            f.write(line+"\n")
        f.truncate()
        # release the lock
        fcntl.flock(f, fcntl.LOCK_UN)
        print "There remain", len(waitlist), "replicas on nodes"
        print "Unlocked"
        f.close()
        return len(waitlist)

class Waitdir(object):
    """Directory-based job control. Each replica has a file within the
    directory; when the replica finishes, we remove that file."""

    import os.path # we assume os was already imported

    def __init__(self, dname):
        self.dname = dname
        try:
            os.makedirs(self.dname)
        except OSError as exception:
            if (exception.errno != errno.EEXIST):
                raise
        return

    def build(self, mover):
        try:
            reps = mover.replicas
        except:
            reps = []
        for rep in reps:
            fname = self.dname + "/" + rep
            with file(fname, 'a'):
                os.utime(fname, None)
        return

    def update(self, rep):
        if (rep != None):
            fname = self.dname + "/" + rep
            print "Removing "+rep
            print "fname = "+fname
            if (os.path.isfile(fname)):
                os.remove(fname)
            else:
                print "Warning: tried to remove "+fname
                print "Apparently it doesn't exist"

        nfiles=len([name for name in os.listdir(self.dname) \
                        if os.path.isfile(os.path.join(self.dname,name))])
        print "nfiles="+str(nfiles) # DEBUG
        return nfiles


def string_list(*elements):
    """Takes its arguments and makes it into a list of strings. Useful when
    generating commands.
    """
    res = []
    for elem in elements:
        res.append(str(elem))
    print res # DEBUG
    return res

# #######################################################################

class RepExSwapper(object):
    def __init__(self, owner, confline):
        self.owner=owner
        self.stepnum=owner.stepnum
        self.step = int(confline['step'])
        self.name = confline['name']
        self.conffile = confline['conf']
        conff = open(self.conffile, "r")
        self.pairs = []
        self.recur = True
        for line in conff:
            splitter = clean_line(line)
            if (re.search("(repex)?(_)?pairs", splitter[0], re.I)):
                for i in range((len(splitter)-1)/2):
                    mypair= [ splitter[2*i+1], splitter[2*i+2] ]
                    self.pairs.append(mypair)
            if (re.search("try", splitter[0], re.I)):
                self.trycmd = splitter[1:]
            if (re.search("acc", splitter[0], re.I)):
                self.acccmd = splitter[1:]
            if (re.search("rej", splitter[0], re.I)):
                self.rejcmd = splitter[1:]
            if (re.search("rep(lica)?s", splitter[0], re.I)):
                self.replicas = splitter[1:] # mostly unused here

        #print pairs
        return

    def doMove(self,stepnum):
        # select replicas
        [repA, repB] = random.choice(self.pairs)
        trial_success = self.attempt_swap(repA,repB,stepnum)
        if (trial_success):
            self.onAccept(repA, repB, stepnum)
        else:
            self.onReject(repA, repB, stepnum)

        # If the tail call is in an external script, doMove returns false.
        # If we need the looping in here, return true.
        return self.recur

    def attempt_swap(self, repA,repB,stepnum):
        mycmd = string_list(*(self.trycmd+[stepnum, self.step, \
                    repA, repB, self.owner.conffile, self.conffile]))
        res = subprocess.check_output(mycmd)
        return res

    def onAccept(self, repA, repB, stepnum):
        mycmd = string_list(*(self.acccmd+[stepnum, self.step, \
                    repA, repB, self.owner.conffile, self.conffile]))
        res = subprocess.check_output(mycmd)
        print res
        return

    def onReject(self, repA, repB, stepnum):
        mycmd = string_list(*(self.rejcmd+[stepnum, self.step, \
                    repA, repB, self.owner.conffile, self.conffile]))
        res = subprocess.check_output(mycmd)
        print res
        return

# #######################################################################

class ScriptLauncher(object):
    def __init__(self, owner, confline):
        self.owner=owner
        self.stepnum=owner.stepnum
        self.step = int(confline['step'])
        self.name = confline['name']
        self.recur = False
        self.conffile = confline['conf']
        conff = open(self.conffile, "r")
        for line in conff:
            splitter = clean_line(line)
            if (re.search("run",splitter[0], re.I)):
                self.runcmd = splitter[1:]
            if (re.search("rep(lica)?s", splitter[0], re.I)):
                self.replicas = splitter[1:]
            if (re.search("recur(s)?", splitter[0], re.I)):
                self.recur = splitter[1]
        return

    def doMove(self,stepnum):
        mycmd = string_list(*(self.runcmd+[stepnum, self.step, \
            self.owner.conffile, self.conffile]))
        myrun = subprocess.check_output(mycmd)
        print myrun
        # If the tail call is in an external script, return false. If we
        # need the tail call in here, return true.
        return self.recur

# #######################################################################

import sys
if __name__ == "__main__":
    wrapper = OneWrapper(sys.argv)
    stepnum = wrapper.stepnum
    wrapper.run(stepnum)

