#!/bin/env python
import logging
from common import quote_if_text

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

    # Add actors definition
    add_newline = None
    for id in diagram["actors"]:
        result.append("class %s << Actor >>" % diagram["actors"][id])
        add_newline = 1

    if add_newline:
        result.append("")

    # Add classes
    '''
    TEMPORARY REMOVED
    for id in diagram["classes"]:

        # Check if included in a package
        add_pkg_end = None
        for pkgid in diagram["packages"]:
            for class_id in diagram["packages"][pkgid]["includes"]:
                if class_id == id:
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
    '''

    # Add types
    add_newline = None
    for id in diagram["types"]:
        result.append("class %s << Type >>" % (diagram["types"][id]["name"]))
        add_newline = 1

    if add_newline:
        result.append("")

    for data in diagram["inheritance"]:
        result.append("%s %s %s" % (data["target"], "<|--", data["source"]))

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


    result.append("@enduml")
    return result    
