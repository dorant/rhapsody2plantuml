#!/bin/env python
import sys
import os.path
import xml.dom.minidom as md

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

if __name__ == "__main__":
    parser = ArgumentParser(formatter_class = ArgumentDefaultsHelpFormatter)
    parser.add_argument("file", help="XML file to make pretty")
    options = parser.parse_args()

    pretty_print = lambda f: '\n'.join([line for line in md.parse(open(f)).toprettyxml(indent=' '*2).split('\n') if line.strip()])

    if not os.path.isfile(options.file):
        print "File does not exist:", options.file
        sys.exit(1)

    print pretty_print(options.file)
