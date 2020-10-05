#! /usr/bin/python3

import os
import sys

if len(sys.argv) < 3:
    sys.stderr.write("Requires <out>.py <in> [<in>] ....\n")
    sys.exit(-1)

if not sys.argv[1].endswith(".py"):
    sys.stderr.write("Requires <out>.py <in> [<in>] ....\n")
    sys.exit(-1)

out = open(sys.argv[1], "w")

out.write("resources = {\n")

for in_filename in sys.argv[2:]:
    with open(in_filename) as in_file:
        data = in_file.read()
        out.write('"%s" : "' % os.path.basename(in_filename))
        for b in data:
            out.write("\\x%02x" % ord(b))
        out.write('",\n')

out.write("}")
out.close()

