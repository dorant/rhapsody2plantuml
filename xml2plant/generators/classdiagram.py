#!/bin/env python2
import logging
from common import quote_if_text

from parsers.parser import PartType
from parsers.parser import EventType
from parsers.parser import MessageType


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
#        result.append("%s %s--> %s %s" % (data["source"], quote_if_text(data["sourcerole"]),
#                                  quote_if_text(data["targetrole"]), data["target"]))
        result.append("%s %s--> %s %s : %s" % (data["source"], quote_if_text(data["sourcemultiplicity"]),
                                               quote_if_text(data["targetmultiplicity"]), data["target"],
                                               data["targetrole"]))


    result.append("@enduml")
    return result    
