#!/bin/env python
import sys
import logging
import os.path
from lxml import etree
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

from parsers.parser import PartType
from parsers.parser import EventType
from parsers.parser import MessageType

from parsers.parser import parse_classes
from parsers.parser import parse_actors

from parsers.usecase import get_usecase_list
from parsers.usecase import parse_usecasediagram

from parsers.classdiagram import get_class_list
from parsers.classdiagram import parse_classdiagram

from parsers.parser import get_sequence_list
from parsers.parser import parse_sequencediagram



def find_nearest_lifeline(lifelines, position):

    # Start with large diff and unknown participant
    smallest_dist = 99999999
    smallest_part = None

    for key, part in sorted(lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
        if smallest_part == None:
            smallest_part = part

        dist = abs(part.position.get_center_x() - position.get_center_x())
        logging.debug("Nearest lifeline: Check: %s against %s", dist, smallest_dist)

        if smallest_dist < dist:
            return smallest_part
        else:
            smallest_part = part
            smallest_dist = dist
    return smallest_part

def quote_if_space(string):
    if " " in string:
        return '"%s"' % (string)
    else:
        return string

def quote_if_text(string):
    if len(string) > 0:
        return '"%s"' % (string)
    else:
        return string

def generate_plantuml_sequence(lifelines, chartdata):
    result = []

    result.append("@startuml")
    result.append("hide footbox")
    result.append("title %s" % chartdata["name"])
    result.append("")

    # Print order of participants
    for key, part in sorted(lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
        color = ""
        if part.fillstyle != 0:
            color = "#F5F5F5"

        if part.type == PartType.ACTOR:
            result.append('actor %s %s' % (quote_if_space(part.name), color))
        else:
            result.append('participant %s %s' % (quote_if_space(part.name), color))

        logging.debug("Position: %s", part.position)
    result.append("")

    # Print all events(messages/conditions and more)
    for event in sorted(chartdata["events"], key=lambda x: x.position.top_left_y):
        logging.debug("Print events: %s", event)

        # Handle messsage arrows
        if event.type == EventType.MESSAGE:
            arrow = "->"
            if event.type == MessageType.REPLY:
                arrow = "-->"
                
            result.append('%s %s %s : %s(%s)' % (quote_if_space(lifelines[event.sender].name),
                                                 arrow,
                                                 quote_if_space(lifelines[event.receiver].name),
                                                 event.name, event.args))

        elif event.type == EventType.COND_START:
            result.append("%s %s" % (event.cond, event.text))

        elif event.type == EventType.COND_ELSE:
            result.append("%s %s" % (event.cond, event.text))

        elif event.type == EventType.COND_END:
            result.append("end")

# TODO: span over many lifelines
        elif event.type == EventType.NOTE:
            participant = find_nearest_lifeline(lifelines, event.position)
            text = event.text
            if '\n' in text:
                # Handle multiline notes
                result.append('note over %s' % (participant.name))
                result.append(text)
                result.append('end note')
            else:
                result.append('note over %s: %s' % (participant.name, text))

# TODO: span over many lifelines
        elif event.type == EventType.REF:
            participant = find_nearest_lifeline(lifelines, event.position)
            text = event.text
            if '\n' in text:
                # Handle multiline reference
                result.append('ref over %s' % (participant.name))
                result.append(text)
                result.append('end ref')
            else:
                result.append('ref over %s : %s' % (participant.name, text))

        elif event.type == EventType.DIVIDER:
            result.append("== %s ==" % event.text)

        logging.debug("Position: %s", event.position)

    result.append("@enduml")
    return result



def generate_plantuml_classdiagram(diagram):
    result = []

    result.append("@startuml")
    result.append("title %s" % diagram["name"])
    result.append("")

    # Add packages not including any classes
    add_newline = None
    for pkgid in diagram["packages"]:
        if len(diagram["packages"][pkgid]["includes"]) == 0:
            result.append("package %s {}" % diagram["packages"][pkgid]["name"])
            add_newline = 1

    if add_newline:
        result.append("")

    # Add actors definition
    add_newline = None
    for id in diagram["actors"]:
        result.append("class %s << Actor >>" % diagram["actors"][id])
        add_newline = 1

    if add_newline:
        result.append("")

    # Add classes
    for id in diagram["classes"]:

        # Check if included in a package
        add_pkg_end = None
        for pkgid in diagram["packages"]:
            for name in diagram["packages"][pkgid]["includes"]:
                if name == diagram["classes"][id]["name"]:
                    result.append("package %s {" % diagram["packages"][pkgid]["name"])
                    add_pkg_end = 1

        if "stereotype" in diagram["classes"][id]:
            type = "class"
            if diagram["classes"][id]["stereotype"] == "Interface":
                type = "interface"

            result.append("%s %s <<%s>>" % (type,
                                            diagram["classes"][id]["name"],
                                            diagram["classes"][id]["stereotype"]))
        elif add_pkg_end:
            result.append("  class %s" % diagram["classes"][id]["name"])

        if add_pkg_end:
            result.append("}")


    for data in diagram["inheritance"]:
        result.append("%s %s %s" % (data["target"], "<|--", data["source"]))

    for data in diagram["associations"]:
#        result.append("%s %s--> %s %s" % (data["source"], quote_if_text(data["sourcerole"]),
#                                  quote_if_text(data["targetrole"]), data["target"]))
        result.append("%s %s--> %s %s : %s" % (data["source"], quote_if_text(data["sourcemultiplicity"]),
                                               quote_if_text(data["targetmultiplicity"]), data["target"],
                                               data["targetrole"]))


    result.append("@enduml")
    return result    


def generate_plantuml_usecase(ucdata, participants, diagram):
    result = []
    for name in diagram:
        result.append("@startuml")
        result.append("title %s" % name)
        result.append("left to right direction")
        result.append("")

        # Print actors
        for id in participants:
            actor = participants[id].name.replace(" ","_")
            result.append('actor %s' % actor)
            logging.debug("Using actor: %s", participants[id])
        result.append("")

        # Adding global notes
        for note in diagram[name]['notes']:
            if len(note["anchor"]) == 0:
                result.append('note left')
                result.append('%s' % note["text"])
                result.append('end note')
                result.append("")

        # Adding global usecases
        for uc in diagram[name]['free_ucs']:
            # Add associations to participants
            for assoc in ucdata[uc]['associations']:
                if assoc in participants:
                    result.append('(%s  [[link]]) --> %s' % (ucdata[uc]['name'], participants[assoc].name.replace(" ","_") ))

            # Add associations to the usecase
            for id in participants:
                for uc_guid in participants[id].associations:
                    if uc_guid == uc:
                        if id not in ucdata[uc]['associations']:
                            result.append('%s --> (%s  [[link]])' % (participants[id].name.replace(" ","_"), ucdata[uc]['name'] ))

            # Add dependencies
            for dep in ucdata[uc]['dependencies']:
                if dep in ucdata:
                    result.append('(%s  [[link]]) ..> (%s  [[link]])' % (ucdata[uc]['name'], ucdata[dep]['name'] ))

        # Space if needed
        if len(diagram[name]['free_ucs']) > 0:
            result.append("")

        # Adding boxes with usecases
        for rect in diagram[name]['rect_ucs']:
            rect_name = diagram[name]['rect_ucs'][rect]['name']
            rect_ucs = diagram[name]['rect_ucs'][rect]['ucs']
            logging.debug("%s %s", rect_name, rect_ucs)

            result.append('rectangle %s {' % quote_if_space(rect_name))
            for uc in rect_ucs:
                # Add associations to participants
                for assoc in ucdata[uc]['associations']:
                    if assoc in participants:
                        result.append('  (%s  [[link]]) --> %s' % (ucdata[uc]['name'], participants[assoc].name.replace(" ","_") ))

                # Add associations to the usecase
                for id in participants:
                    for uc_guid in participants[id].associations:
                        if uc_guid == uc:
                            if id not in ucdata[uc]['associations']:
                                result.append('  %s --> (%s  [[link]])' % (participants[id].name.replace(" ","_"), ucdata[uc]['name'] ))

                # Add dependencies
                for dep in ucdata[uc]['dependencies']:
                    if dep in ucdata:
                        result.append('  (%s  [[link]]) ..> (%s  [[link]])' % (ucdata[uc]['name'], ucdata[dep]['name'] ))

            result.append("}")

        # Adding specific notes
        for note in diagram[name]['notes']:
            if len(note["anchor"]) > 0:
                anchor_name = ""
                if note["anchor"][0] in participants:
                    anchor_name = participants[note["anchor"][0]].name.replace(" ","_")

                if note["anchor"][0] in ucdata:
                    anchor_name = ucdata[note["anchor"][0]]['name']

                result.append('note left of %s' % anchor_name)
                result.append('%s' % note["text"])
                result.append('end note')

        # Done
        result.append("@enduml")
        result.append("")
    return result

def print_diagram_names(xmlnode):
    print "Usecase diagrams:" 
    for name in get_usecase_list(xmlnode):
        print "  ", name

    print "Sequence diagrams:" 
    for name in get_sequence_list(xmlnode):
        print "  ", name

    print "Object and Class Diagrams:" 
    for name in get_class_list(xmlnode):
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

        # Usecases
        for name in get_usecase_list(root):
            filename = os.path.join(path, "UC_" + name.replace(" ", "_") + ".plantuml")
            print "- Generating:", filename

            # Parse
            ucdata, uc_participants, diagram = parse_usecasediagram(root, participants, name)
            uml = generate_plantuml_usecase(ucdata, uc_participants, diagram)

            # Create folders needed
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            # Save to file
            f = open(filename,'w')
            f.write('\n'.join(uml))
            f.close()

        # Sequence diagrams
        for name in get_sequence_list(root):
            filename = os.path.join(path, "SEQ_" + name.replace(" ", "_") + ".plantuml")
            print "- Generating:", filename

            # Parse
            lifelines, seqdata = parse_sequencediagram(root, participants, name)
            uml = generate_plantuml_sequence(lifelines, seqdata)

            # Create folders needed
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            # Save to file
            f = open(filename,'w')
            f.write('\n'.join(uml))
            f.close()

        # Class diagrams
        for name in get_class_list(root):
            filename = os.path.join(path, "CL_" + name.replace(" ", "_") + ".plantuml")
            print "- Generating:", filename

            # Parse
            data = parse_classdiagram(root, participants, name)
            uml = generate_plantuml_classdiagram(data)

            # Create folders needed
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            # Save to file
            f = open(filename,'w')
            f.write('\n'.join(uml))
            f.close()

    # Generate sequence diagram
    elif options.sequence:
        lifelines, seqdata = parse_sequencediagram(root, participants, options.sequence)
        uml = generate_plantuml_sequence(lifelines, seqdata)
        print '\n'.join(uml)

    # Generate usecase diagram
    elif options.usecase:
        ucdata, uc_participants, diagram = parse_usecasediagram(root, participants, options.usecase)
        uml = generate_plantuml_usecase(ucdata, uc_participants,  diagram)
        print '\n'.join(uml)

    # Generate class/object diagram
    elif options.classdiagram:
        data = parse_classdiagram(root, participants, options.classdiagram)
        uml = generate_plantuml_classdiagram(data)
        print '\n'.join(uml)

    else:
        print "No action given"

    sys.exit()

