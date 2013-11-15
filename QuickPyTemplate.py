#/usr/bin/env python

# QuickPyTemplate
#   I use this little script to generate input file templates when I know
#   I'll be using a lot of them.
#
# David W.H. Swenson, probably developed sometime in 2009

class QuickPyTemplate(object):

    def __init__(self):
        self.mydict = {}


    def set_entry(self, key, value):
        self.mydict[key] = value
        return

    def replace(self, filename):
        from re import sub, match, search, compile
        myfile = open(filename, "r")
        newf = []
        for line in myfile:
            #line = sub('\s*$', '', line) # chop off \n
            for entry in self.mydict.keys():
                if (search(entry, line)):
                    line = sub(entry, self.mydict[entry], line)

            newf.append(line)

        return "".join(newf)

