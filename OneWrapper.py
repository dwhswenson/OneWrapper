#!/usr/bin/env python

# OneWrapper.py
#   Very simple scripts for general parallel replica exchange.
#   Written by David W.H. Swenson
#   Current version 2013-10-22

# Requires Python 2.7 or later for some of the functions from subprocess.
# Includes support for both optparse and argparse, so we're flexible with
# Py3.x.
import subprocess, re, random, os

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
        conffile=  args[1]
        self.stepnum = opts.N
        self.finished = opts.r

        self.movers = []
        moverlist = [] 

        #self.waitfile=os.get_cwd()+_"/WAITFILE"
        self.waitfile="WAITFILE"

        # now read the conffile
        # in here, we need to set the movetypes (and related arrays)
        conff = open(conffile, "r")
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

            if (re.search("(max)?(_)?(n)?step(s)?", splitter[0], re.I)):
                self.maxsteps = int(splitter[1])

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

    def update_waitlist(self):
        """Read in WAITLIST file while ignoring the replica we just
        finished; write it back out without our replica, and return the
        number of remaining entries.
        """
        import fcntl
        # open self.waitfile, lock it
        try:
            f = open(self.waitfile, 'r+')
        except:
            # open for writing and close it to create an empty file
            f = open(self.waitfile, 'w')
            f.close()
            f = open(self.waitfile, 'r+')
        fcntl.flock(f, fcntl.LOCK_EX)
        #print "Locked "+self.waitfile
        # read in the replicas, except the one that matches ours
        waitlist = []
        for ll in f:
            line=clean_line(ll)[0]
            #print "Reading "+line+" ",
            if (line!=self.finished):
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
        #print "Unlocked"
        f.close()
        return len(waitlist)

    def run(self,stepnum):
        """Main function for this calculation class.
        """
        if (self.update_waitlist()==0):
            self.stepnum = stepnum
            recur = True
            while (recur and (self.stepnum < self.maxsteps)):
                # now we get to try a move!
                move = self.movetype()
                mymover = self.movers[move]
                build_waitfile(self.waitfile, mymover)
                recur = mymover.doMove(stepnum)
                self.stepnum += mymover.step
        return

# #######################################################################

def build_waitfile(fname, mover):
    """Assuming that mover is an object with a list called replicas, this
    appends each of the replica labels to the waitfile in fname.
    """
    try:
        reps = mover.replicas
    except:
        reps = []
    f = open(fname, 'a')
    # possibly lock it, just to be safe? shouldn't be needed tho
    for rep in reps:
        f.write(rep+"\n")
    f.close()
    return len(reps)

def prep_repex_cmd(cmd, stepnum, repA, repB):
    """Puts together the array which becomes our replica exchange script
    command.
    """
    mycmd = list(cmd)
    mycmd.append(str(stepnum))
    mycmd.append(repA)
    mycmd.append(repB)
    return mycmd

# #######################################################################

class RepExSwapper(object):
    def __init__(self, owner, confline):
        self.owner=owner
        self.stepnum=owner.stepnum
        self.step = int(confline['step'])
        self.name = confline['name']
        conffile = confline['conf']
        conff = open(conffile, "r")
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
            self.onAccept(repA, repB, stepnum, stepnum+self.step)
        else:
            self.onReject(repA, repB, stepnum, stepnum+self.step)

        # If the tail call is in an external script, doMove returns false.
        # If we need the looping in here, return true.
        return self.recur

    def attempt_swap(self, repA,repB,stepnum):
        mycmd = prep_repex_cmd(self.trycmd, stepnum, repA, repB)
        res = subprocess.check_output(mycmd)
        return res

    def onAccept(self, repA, repB, stepnum, nextstep):
        mycmd = prep_repex_cmd(self.acccmd, stepnum, repA, repB)
        res = subprocess.check_output(mycmd)
        print res
        return

    def onReject(self, repA, repB, stepnum, nextstep):
        mycmd = prep_repex_cmd(self.rejcmd, stepnum, repA, repB)
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
        conffile = confline['conf']
        conff = open(conffile, "r")
        for line in conff:
            splitter = clean_line(line)
            if (re.search("run",splitter[0], re.I)):
                self.runcmd = splitter[1:]
            if (re.search("rep(lica)?s", splitter[0], re.I)):
                self.replicas = splitter[1:]
        return

    def doMove(self,stepnum):
        mycmd = list(self.runcmd)
        mycmd.append(str(stepnum))
        mycmd.append(str(stepnum+self.step))
        myrun = subprocess.check_output(mycmd)
        print myrun
        # If the tail call is in an external script, return false. If we
        # need the tail call in here, return true.
        return self.recur


import sys
if __name__ == "__main__":
    wrapper = OneWrapper(sys.argv)
    stepnum = wrapper.stepnum
    wrapper.run(stepnum)

