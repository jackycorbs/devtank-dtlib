#! /usr/bin/python

import os
import sys
import time
import re

if len(sys.argv) < 3:
    sys.stderr.write("Requires <out>.py <in> [<in>] ....\n")
    sys.exit(-1)

if not sys.argv[1].endswith(".py"):
    sys.stderr.write("Requires <out>.py <in> [<in>] ....\n")
    sys.exit(-1)

out = open(sys.argv[1], "w")

out.write("resources = {\n")

st_mtime = os.stat(sys.argv[0]).st_mtime

for in_filename in sys.argv[2:]:
    with open(in_filename) as in_file:
        data = in_file.read()
        out.write('"%s" : "' % in_filename)
        for b in data:
            out.write("\\x%02x" % ord(b))
        out.write('",\n')
    stat = os.stat(in_filename)
    if stat.st_mtime > st_mtime:
        st_mtime = stat.st_mtime

out.write("}")
out.close()

os.utime(sys.argv[1], (time.time(), st_mtime+1))
