#!/usr/bin/env python

# need the following on startup: initial replica locations; replica swap
# pairs with probabilities

import random,sys

def clean_and_split(line):
    from re import sub, split
    line = sub('\#.*', '', line)
    line = sub('^\s*', '', line)
    line = sub('\s*$', '', line)
    splitter = split('\s+', line)
    return splitter

class Replica:
    def __init__(self):
        self.label = -1
        self.host = -1
        self.direction = 0
        return

    def set_dir(self, limit, matchdir):
        if (self.host == limit):
            self.direction=matchdir
        return

    def set_host(self, host):
        self.host = host
        return

class ReplicaSet:
    def __init__(self):
        self.reps = []
        self.swap_pairs = []
        self.swap_probs = []
        self.npairs = 0
        self.step = 0
        return

    # This version of the do_swap function just assumes that there's some
    # constant probability for each swap pair. Cheap way to simulate a real
    # replica exchange process.
    def do_swap(self):
        self.step += 1
        from math import floor
        mypair = int(floor(random.random()*self.npairs))
        xi = random.random()
        #print "Attempting to swap", self.swap_pairs[mypair],
        if ( xi <= self.swap_probs[mypair] ):
            print self.swap_pairs[mypair], "Y"
            nrepA = self.reps[self.swap_pairs[mypair][0]].host
            nrepB = self.reps[self.swap_pairs[mypair][1]].host
            foo = self.reps[nrepA]
            self.reps[nrepA] = self.reps[nrepB]
            self.reps[nrepB] = foo
            self.reps[nrepA].set_host(nrepA)
            self.reps[nrepB].set_host(nrepB)
            #print self.step, nrepA, self.reps[nrepA].label
            #print self.step, nrepB, self.reps[nrepB].label
            self.reps[nrepA].set_dir(self.max_host, -1)
            self.reps[nrepB].set_dir(self.max_host, -1)
            self.reps[nrepA].set_dir(self.min_host, 1)
            self.reps[nrepB].set_dir(self.min_host, 1)
        else:
            print self.swap_pairs[mypair], "N"
        return

    def output(self):
        for rep in self.reps:
            print "%3d " % rep.label,
        print
        return

    def full_output(self, fname=""):
        myf = sys.stdout if fname=="" else open(fname, 'w')
        for i in range(len(self.reps)):
            #mystr = sprintf( "%3d %3d", i, self.reps[i].label)
            myf.write(str(i) + " " + str(self.reps[i].label) + " " \
                    + str(self.reps[i].direction) + "\n")
        return


    def load_initial_reps(self,fname):
        myf = sys.stdin if fname=="" else open(fname, 'r')
        for line in myf:
            pass
        self.reps = []
        splitter = clean_and_split(line)
        if (len(splitter) > 1):
            i=0
            for val in splitter:
                myrep = Replica()
                myrep.label = int(val)
                myrep.set_host(i)
                self.reps.append(myrep)
                i+=1
        self.min_host = 0
        self.max_host = len(self.reps)-1
        return

    def load_swap_pairs(self,fname):
        myf = sys.stdin if fname=="" else open(fname, 'r')
        self.swap_pairs = []
        self.swap_probs = []
        for line in myf:
            splitter = clean_and_split(line)
            if (len(splitter) == 3):
                mypair = []
                mypair.append(int(splitter[0]))
                mypair.append(int(splitter[1]))
                self.swap_pairs.append(mypair)
                self.swap_probs.append(float(splitter[2]))
            else:
                print "WTF? Swap pairs has more than 3 parts:", splitter
        self.npairs = len(self.swap_pairs)
        return


def parsing(parseargs):
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('--init', type="string")
    parser.add_option('--swap', type="string")
    parser.add_option('-n', '--nsteps', type="int")
    return parser.parse_args(parseargs)

if __name__ == "__main__":
    opt, args = parsing(sys.argv)
    swapper = ReplicaSet()
    swapper.load_initial_reps(opt.init)
    swapper.load_swap_pairs(opt.swap)
    
    #swapper.output()
    swapper.reps[swapper.min_host].set_dir(swapper.min_host, 1)
    swapper.reps[swapper.max_host].set_dir(swapper.max_host, -1)
    print swapper.step
    swapper.full_output("")
    for i in range(opt.nsteps):
        print swapper.step,
        swapper.do_swap()
        #swapper.output()
        swapper.full_output("")

    swapper.full_output("final.out")

