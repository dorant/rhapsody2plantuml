#!/bin/env python

import sys
import logging
from lxml import etree
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

from parser import print_usecase_list
from parser import print_sequencediagrams_list
from parser import print_classdiagram_list

from parser import parse_classes
from parser import parse_actors
from parser import parse_usecases
from parser import parse_sequencediagram
from parser import parse_classdiagram


def find_nearest_lifeline(position):
    global data_lifelines
    # Start with large diff and unknown participant
    smallest_dist = 99999999
    smallest_part = None

    for key, part in sorted(data_lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
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

def generate_plantuml(chartdata):
    global data_lifelines

    print "@startuml"
    print "hide footbox"
    print "title", chartdata["name"]
    print ""

    # Print order of participants
    for key, part in sorted(data_lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
        color = ""
        if part.fillstyle != 0:
            color = "#F5F5F5"

        if part.type == PartType.ACTOR:
            print 'actor %s %s' % (quote_if_space(part.name), color)
        else:
            print 'participant %s %s' % (quote_if_space(part.name), color)

        logging.debug("Position: %s", part.position)
    print ""

    # Print all events(messages/conditions and more)
    for event in sorted(chartdata["events"], key=lambda x: x.position.top_left_y):
        logging.debug("Print events: %s", event)

        # Handle messsage arrows
        if event.type == EventType.MESSAGE:
            arrow = "->"
            if event.type == MessageType.REPLY:
                arrow = "-->"
                
            print '%s %s %s : %s(%s)' % (quote_if_space(data_lifelines[event.sender].name),
                                       arrow,
                                       quote_if_space(data_lifelines[event.receiver].name),
                                       event.name, event.args)

        elif event.type == EventType.COND_START:
            print event.cond, event.text

        elif event.type == EventType.COND_ELSE:
            print event.cond, event.text

        elif event.type == EventType.COND_END:
            print "end"

# TODO: span over many lifelines
        elif event.type == EventType.NOTE:
            participant = find_nearest_lifeline(event.position)
            text = event.text
            if '\n' in text:
                # Handle multiline notes
                print 'note over %s' % (participant.name)
                print text
                print 'end note'
            else:
                print 'note over %s: %s' % (participant.name, text)

# TODO: span over many lifelines
        elif event.type == EventType.REF:
            participant = find_nearest_lifeline(event.position)
            text = event.text
            if '\n' in text:
                # Handle multiline reference
                print 'ref over %s' % (participant.name)
                print text
                print 'end ref'
            else:
                print 'ref over %s : %s' % (participant.name, text)

        elif event.type == EventType.DIVIDER:
            print "==", event.text, "=="

        logging.debug("Position: %s", event.position)

    print "@enduml"



def generate_plantuml_classdiagram(diagram):
    print "" 
    print "@startuml"
    print "title", diagram["name"]
    print ""

    for id in diagram["classes"]:

        # Check if included in a package
        add_pkg_end = None
        for pkg in diagram["packages"]:
            for name in pkg["includes"]:
                if name == diagram["classes"][id]["name"]:
                    print "package %s {" % (pkg["name"])
                    add_pkg_end = 1

        if "stereotype" in diagram["classes"][id]:
            type = "class"
            if diagram["classes"][id]["stereotype"] == "Interface":
                type = "interface"

            print "%s %s <<%s>>" % (type,
                                    diagram["classes"][id]["name"],
                                    diagram["classes"][id]["stereotype"])
        elif add_pkg_end:
            print "  class", diagram["classes"][id]["name"]

        if add_pkg_end:
            print "}"


    for data in diagram["inheritance"]:
        print data["target"], "<|--", data["source"]

    for data in diagram["associations"]:
#        print "%s %s--> %s %s" % (data["source"], quote_if_text(data["sourcerole"]),
#                                  quote_if_text(data["targetrole"]), data["target"])
        print "%s %s--> %s %s : %s" % (data["source"], quote_if_text(data["sourcemultiplicity"]),
                                  quote_if_text(data["targetmultiplicity"]), data["target"],
                                  data["targetrole"])


    print "@enduml"
    print ""



def generate_plantuml_usecase(ucdata, diagram):
    for name in diagram:
        print "@startuml"
        print "title", name
        print "left to right direction"
        print ""

        # Print actor (todo: only once!!)
        actors = []
#        for uc_guid in diagram[name]['free_ucs']:
#            actors.append(global_participants[uc_guid].name.replace(" ","_"))

        for rect in diagram[name]['rect_ucs']:
            for uc in diagram[name]['rect_ucs'][rect]['ucs']:
                # Add actors associated by usecase
                for assoc in ucdata[uc]['associations']:
                    actors.append(global_participants[assoc].name.replace(" ","_"))

                # Add actors that associates to the usecase
                for guid in global_participants:
                    # Arrow is a dependency?
                    for uc_guid in global_participants[guid].dependencies:
                        if uc_guid == uc:
                            actors.append(global_participants[guid].name.replace(" ","_"))
                            # Add actor to the usecase
                            if guid not in ucdata[uc]['dependencies']:
                                ucdata[uc]['dependencies'].append(guid)

                    # Arrow is a association?
                    for uc_guid in global_participants[guid].associations:
                        if uc_guid == uc:
                            actors.append(global_participants[guid].name.replace(" ","_"))
                            # Add actor to the usecase
                            if guid not in ucdata[uc]['associations']:
                                ucdata[uc]['associations'].append(guid)


        # remove duplicates
        actors = list(set(actors))
        for actor in actors:
            print 'actor', actor
        print ""

        # Get sequencediagram (can be within a usecase as well! Searching for tag only)
        charts = {}
        charts[""] = ""
        for chart in root.xpath(".//IMSC"):
            id = chart.xpath("_id/text()")[0]
            charts[id] = chart.xpath("_name/text()")[0]
            

        # Adding global usecases
        for uc in diagram[name]['free_ucs']:
            for assoc in ucdata[uc]['associations']:
                print '%s -- (%s  [[%s]])' % (global_participants[assoc].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])
# TODO: dependency to other usecase

#            for assoc in ucdata[uc]['dependencies']:
#                print assoc
#                print '%s -- (%s  [[%s]])' % (global_participants[assoc].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])

        # Adding boxes with usecases
        for rect in diagram[name]['rect_ucs']:
            rect_name = diagram[name]['rect_ucs'][rect]['name']
            rect_ucs = diagram[name]['rect_ucs'][rect]['ucs']
            logging.debug("%s %s", rect_name, rect_ucs)

            print 'rectangle %s {' % quote_if_space(rect_name)
            for uc in rect_ucs:
                for assoc in ucdata[uc]['associations']:
                    print '  %s -- (%s  [[%s]])' % (global_participants[assoc].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])
                for dep in ucdata[uc]['dependencies']:
                    if dep in global_participants:
                        print '  %s -- (%s  [[%s]])' % (global_participants[dep].name.replace(" ","_"), ucdata[uc]['name'], charts[ucdata[uc]['statechart']])
                        
            print "}"

        print "@enduml"
        print ""



if __name__ == "__main__":
    parser = ArgumentParser(formatter_class = ArgumentDefaultsHelpFormatter)
    parser.add_argument("file", help="XML file to parse")
    parser.add_argument("-v", dest="verbose", help="Enable verbose log", action="store_true")
    parser.add_argument("-l", "--list", dest="list", help="List extractable charts", action="store_true")
    parser.add_argument("-s", dest="sequence", help="Name of sequence diagram to generate to PlantUML")
    parser.add_argument("-u", dest="usecase", help="Name of usecase diagram to generate to PlantUML")
    parser.add_argument("-c", dest="classdiagram", help="Name of class or object diagram to generate to PlantUML")
    options = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    tree = etree.parse(options.file)
    root = tree.getroot()

    if options.list:
        print_usecase_list(root)
        print_sequencediagrams_list(root)
        print_classdiagram_list(root)
        sys.exit()

    # Parse global info
    parse_classes(root)
    parse_actors(root)

    # Parse sequence diagram
    if options.sequence:
        seqdata = parse_sequencediagram(root, options.sequence)
        generate_plantuml(seqdata)

    # Parse usecase
    elif options.usecase:
        ucdata, diagram = parse_usecases(root, options.usecase)
        generate_plantuml_usecase(ucdata, diagram)

    # Parse class
    elif options.classdiagram:
        data = parse_classdiagram(root, options.classdiagram)
        generate_plantuml_classdiagram(data)

    else:
        print "No action given"

    sys.exit()

