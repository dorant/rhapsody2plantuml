#!/bin/env python
import logging
from common import quote_if_text
from common import quote_restricted_chars

from parsers.parser import PartType
from parsers.parser import EventType
from parsers.parser import MessageType

def get_namespace(diagram, class_id, class_name):
    for pkgid in diagram["packages"]:
        for id in diagram["packages"][pkgid]["includes"]:
            if class_id == id:
                return diagram["packages"][pkgid]["name"] + "::" + class_name
    return class_name


def generate_plantuml_classdiagram(diagram):
    result = []

    result.append("@startuml")
    result.append("title %s" % diagram["name"])
    result.append("")
    result.append("set namespaceSeparator ::")
    result.append("")

    # Add packages not including any classes
    '''
    add_newline = None
    for pkgid in diagram["packages"]:
        if len(diagram["packages"][pkgid]["includes"]) == 0:
            result.append("package %s {}" % diagram["packages"][pkgid]["name"])
            add_newline = 1

    if add_newline:
        result.append("")
    '''

    # Add global/floating notes
    note_number = 0
    for noteid in diagram["notes"]:
        if len(diagram["notes"][noteid]["anchors"]) == 0:
            text = diagram["notes"][noteid]["text"]
        
            result.append("note as N%s" % note_number)
            result.append(text)
            result.append("end note")
            result.append("")
            note_number += 1

    # Add actors definition
    add_newline = None
    for id in diagram["actors"]:
        result.append("class %s << Actor >>" % diagram["actors"][id])
        add_newline = 1

    if add_newline:
        result.append("")

    # Add classes with stereotypes or that is not referenced in other way
    for id in diagram["classes"]:
        name = diagram["classes"][id]["name"]

        # Add interface tags
        if diagram["classes"][id]["stereotype"] == "Interface":
            type = "interface"
            add_newline = 1

            result.append("%s %s <<%s>>" % (type,
                                            get_namespace(diagram, id, name),      
                                            diagram["classes"][id]["stereotype"]))
        else:
            # Check if not added in other way
            class_found = None

            # Check in inheritance
            for data in diagram["inheritance"]:
                if data["target_id"] == id or data["source_id"] == id:
                    class_found = 1

            # Check in associations
            if not class_found:
                for data in diagram["associations"]:
                    if data["target_id"] == id or data["source_id"] == id:
                        class_found = 1

            if not class_found:
                result.append("%s %s" % ("class",
                                         get_namespace(diagram, id, name)))


    if add_newline:
        result.append("")

    # Add types
    add_newline = None
    for id in diagram["types"]:
        result.append("class %s << Type >>" % (diagram["types"][id]["name"]))
        add_newline = 1

    if add_newline:
        result.append("")

    for data in diagram["inheritance"]:
        target_name = get_namespace(diagram, data["target_id"], data["target"])
        source_name = get_namespace(diagram, data["source_id"], data["source"])

        result.append("%s %s %s" % (target_name, "<|--", source_name))

    for data in diagram["associations"]:
        targetrole = ""
        if data["targetrole"]:
            targetrole = " : %s" % (data["targetrole"])

        dot = ""
        if len(data["sourcemultiplicity"]) == 0:
            dot = "*"

        result.append("%s%s%s-->%s%s%s" % (get_namespace(diagram, data["source_id"], data["source"]),
                                           quote_if_text(data["sourcemultiplicity"]),
                                           dot,
                                           quote_if_text(data["targetmultiplicity"]),
                                           get_namespace(diagram, data["target_id"], data["target"]),
                                           targetrole))
    result.append("")


    # Adding specific notes
    for noteid in diagram["notes"]:
        if len(diagram["notes"][noteid]["anchors"]) > 0:
            text = diagram["notes"][noteid]["text"]

            anchor_name = ""
            anchor_id = ""

            logging.debug("Anchorname: %s", anchor_name)
            for search_anchor_id in diagram["notes"][noteid]["anchors"]:                
                logging.debug("Search for %s", search_anchor_id)
                for id in diagram["actors"]:
                    if search_anchor_id == id:
                        anchor_name = diagram["actors"][id]
                        anchor_id = id
                        logging.debug("FOUND Anchorname: %s", anchor_name)

                for id in diagram["types"]:
                    if search_anchor_id == id:
                        anchor_name = diagram["types"][id]["name"]
                        anchor_id = id
                        logging.debug("FOUND Anchorname: %s", anchor_name)

                for id in diagram["classes"]:
                    if search_anchor_id == id:
                        anchor_name = diagram["classes"][id]["name"]
                        anchor_id = id
                        logging.debug("FOUND Anchorname: %s", anchor_name)

            if anchor_name:
                anchor_name = get_namespace(diagram, anchor_id, anchor_name)
                logging.debug("WITH namespace: %s", anchor_name)

                result.append('note right of %s' % quote_restricted_chars(anchor_name))
            else:
                result.append("note as N%s" % note_number)
                note_number += 1
            result.append(text)
            result.append("end note")
            result.append("")

    result.append("@enduml")
    return result    
