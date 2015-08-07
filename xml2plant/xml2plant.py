#!/bin/env python2
import sys
import logging
import os.path
from lxml import etree
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

# Parsers
from parsers.parser import parse_classes
from parsers.parser import parse_actors

from parsers.usecase import get_usecasediagram_list
from parsers.usecase import parse_usecasediagram

from parsers.classdiagram import get_classdiagram_list
from parsers.classdiagram import parse_classdiagram

from parsers.parser import get_sequence_list
from parsers.parser import parse_sequencediagram

# Generators
from generators.sequence import generate_plantuml_sequence
from generators.usecase import generate_plantuml_usecase
from generators.classdiagram import generate_plantuml_classdiagram



def print_diagram_names(xmlnode):
    print "Usecase diagrams:" 
    for name in get_usecasediagram_list(xmlnode):
        print "  ", name

    print "Sequence diagrams:" 
    for name in get_sequence_list(xmlnode):
        print "  ", name

    print "Object and Class Diagrams:" 
    for name in get_classdiagram_list(xmlnode):
        print "  ", name


if __name__ == "__main__":
    parser = ArgumentParser(formatter_class = ArgumentDefaultsHelpFormatter)
    parser.add_argument("file", help="XML file to parse")
    parser.add_argument("-v", dest="verbose", help="Enable verbose log", action="store_true")
    parser.add_argument("-l", "--list", dest="list", help="List extractable charts", action="store_true")
    parser.add_argument("-g", "--generate", dest="generate", help="Generate all diagrams", action="store_true")
    parser.add_argument("-s", dest="sequence", help="Name of sequence diagram to generate to PlantUML")
    parser.add_argument("-u", dest="usecase", help="Name of usecase diagram to generate to PlantUML")
    parser.add_argument("-c", dest="classdiagram", help="Name of class or object diagram to generate to PlantUML")
    parser.add_argument("-r", dest="rename", help="Rename destination path to a folder without the postfix '_rpy'", action="store_true")
    options = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    tree = etree.parse(options.file)
    root = tree.getroot()

    if options.list:
        print_diagram_names(root)
        sys.exit()

    # Parse participants
    participants = {}
    parse_classes(root, participants)
    parse_actors(root, participants)

    # Generate all diagrams
    if options.generate:
        path = os.path.join( os.path.dirname(options.file), "docs")

        if options.rename:
            path = path.replace('_rpy', '')

        # Create folder if needed
        if not os.path.exists(path):
            os.makedirs(path)

        # Usecases
        for name in get_usecasediagram_list(root):
            filename = os.path.join(path, "UC_" + name.replace(" ", "_") + ".plantuml")
            print "   Generating:", filename

            # Parse
            ucdata = parse_usecasediagram(root, participants, name)
            uml = generate_plantuml_usecase(ucdata)

            # Save to file
            f = open(filename,'w')
            f.write('\n'.join(uml).encode('ascii',errors='ignore'))
            f.close()

        # Sequence diagrams
        for name in get_sequence_list(root):
            filename = os.path.join(path, "SEQ_" + name.replace(" ", "_") + ".plantuml")
            print "   Generating:", filename

            # Parse
            lifelines, seqdata = parse_sequencediagram(root, participants, name)
            uml = generate_plantuml_sequence(lifelines, seqdata)

            # Save to file
            f = open(filename,'w')
            f.write('\n'.join(uml).encode('ascii',errors='ignore'))
            f.close()

        # Class diagrams
        for name in get_classdiagram_list(root):
            filename = os.path.join(path, "CL_" + name.replace(" ", "_") + ".plantuml")
            print "   Generating:", filename

            # Parse
            data = parse_classdiagram(root, participants, name)
            uml = generate_plantuml_classdiagram(data)

            # Save to file
            f = open(filename,'w')
            f.write('\n'.join(uml).encode('ascii',errors='ignore'))
            f.close()

    # Generate sequence diagram
    elif options.sequence:
        lifelines, seqdata = parse_sequencediagram(root, participants, options.sequence)
        uml = generate_plantuml_sequence(lifelines, seqdata)
        print '\n'.join(uml).encode('ascii',errors='ignore')

    # Generate usecase diagram
    elif options.usecase:
        ucdata = parse_usecasediagram(root, participants, options.usecase)
        uml = generate_plantuml_usecase(ucdata)
        print '\n'.join(uml).encode('ascii',errors='ignore')

    # Generate class/object diagram
    elif options.classdiagram:
        data = parse_classdiagram(root, participants, options.classdiagram)
        uml = generate_plantuml_classdiagram(data)
        print '\n'.join(uml).encode('ascii',errors='ignore')

    else:
        print "No action given"

    sys.exit()

