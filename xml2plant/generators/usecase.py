#!/bin/env python2
import logging
from common import quote_restricted_chars

def print_arrows(diagram, uc, indent, result):
    uc_appended = False

    if len(uc.linked_diagram_name) > 0:
        link = "  [[SEQ_%s.plantuml]]" % (uc.linked_diagram_name.replace(" ", "_"))
    else:
        link = ""

    for arrow in diagram.associations:
        if arrow.source == uc.id:
            if arrow.target in diagram.participants:
                uc_appended = True
                result.append('%s(%s%s) -- %s' % (indent,
                                                   uc.name,
                                                   link,
                                                   diagram.participants[arrow.target].name.replace(" ","_") ))
            
        elif arrow.target == uc.id:
            if arrow.source in diagram.participants:
                uc_appended = True
                result.append('%s%s -- (%s%s)' % (indent,
                                                   diagram.participants[arrow.source].name.replace(" ","_"),
                                                   uc.name,
                                                   link))

    for arrow in diagram.dependencies:
        if arrow.source == uc.id:
            if arrow.target in diagram.participants:
                uc_appended = True
                result.append('%s(%s%s) ..> %s' % (indent,
                                                   uc.name,
                                                   link,
                                                   diagram.participants[arrow.target].name.replace(" ","_") ))

        elif arrow.target == uc.id:
            if arrow.source in diagram.participants:
                uc_appended = True
                result.append('%s%s ..> (%s%s)' % (indent,
                                                   diagram.participants[arrow.source].name.replace(" ","_"),
                                                   uc.name,
                                                   link))

    # Make sure we show it even without arrows
    if not uc_appended:
        result.append('%s(%s%s)' % (indent,
                                    uc.name, 
                                    link))

    # # Add dependencies
    # for dep_id in uc.dependencies:
    #     for other_uc in diagram.ucs:
    #         if dep_id == other_uc.id:
    #             uc_appended = True
    #             result.append('(%s  [[link]]) ..> (%s  [[link]])' % (uc.name, 
    #                                                                  diagram.ucs[dep_id].name ))

    #     for box_id in diagram.boxes:
    #         for other_uc in diagram.boxes[box_id].ucs:
    #             if dep_id == other_uc.id:
    #                 uc_appended = True
    #                 result.append('(%s  [[link]]) ..> (%s  [[link]])' % (uc.name, 
    #                                                                      diagram.boxes[box_id].ucs[dep_id].name ))
          
    # ====== BOXED =========
    # # Add associations to participants
    # for assoc_id in uc.associations:
    #     if assoc_id in diagram.participants:
    #         uc_appended = True
    #         result.append('  (%s  [[link]]) --> %s' % (uc.name, diagram.participants[assoc].name.replace(" ","_") ))

    # # Add associations to the usecase
    # for part_id in diagram.participants:
    #     for assoc_id in diagram.participants[id].associations:
    #         if assoc_id == uc.id:
    #             if assoc_id not in uc.associations:
    #                 uc_appended = True
    #                 result.append('  %s --> (%s  [[link]])' % (participants[id].name.replace(" ","_"), uc.name ))

    # # Add dependencies
    # for dep_id in uc.dependencies:
    #     for other_uc in diagram.ucs:
    #         if dep_id == other_uc.id:
    #             uc_appended = True
    #             result.append('(%s  [[link]]) ..> (%s  [[link]])' % (uc.name, 
    #                                                                  diagram.ucs[dep_id].name ))

    #     for box_id in diagram.boxes:
    #         for other_uc in diagram.boxes[box_id].ucs:
    #             if dep_id == other_uc.id:
    #                 uc_appended = True
    #                 result.append('(%s  [[link]]) ..> (%s  [[link]])' % (uc.name, 
    #                                                                      diagram.boxes[box_id].ucs[dep_id].name ))

          


def generate_plantuml_usecase(diagram):

    result = []
    result.append("@startuml")
    result.append("title %s" % diagram.name)
    result.append("left to right direction")
    result.append("")

    # Print actors
    for id in diagram.participants:
        actor = diagram.participants[id].name.replace(" ","_")
        result.append('actor %s' % actor)
        logging.debug("Using actor: %s", diagram.participants[id])
    result.append("")

    # Adding global notes (without anchors)
    for note in diagram.notes:
        if len(note.anchors) == 0:
            result.append('note left')
            result.append('%s' % note.text)
            result.append('end note')
            result.append("")

    # Adding global usecases
    for uc in diagram.ucs:
        print_arrows(diagram, uc, "", result)

    # Space if needed
    if len(diagram.ucs) > 0:
        result.append("")

    # Adding boxes with usecases
    for box_id in diagram.boxes:
        rect_name = diagram.boxes[box_id].name
        result.append('rectangle %s {' % quote_restricted_chars(rect_name))
        logging.debug("%s", rect_name)

        for uc in diagram.boxes[box_id].ucs:
            print_arrows(diagram, uc, "    ", result)


        result.append("}")
        result.append("")

    # Adding specific notes
    for note in diagram.notes:
        if len(note.anchors) > 0:
            anchor_name = ""
            if note.anchors[0] in diagram.participants:
                anchor_name = diagram.participants[note.anchors[0]].name.replace(" ","_")

            for uc in diagram.ucs:
                if note.anchors[0] == uc.id:
                    anchor_name = uc.name

            for box_id in diagram.boxes:
                for uc in diagram.boxes[box_id].ucs:
                    if note.anchors[0] == uc.id:
                        anchor_name = uc.name

            result.append('note left of %s' % anchor_name)
            result.append('%s' % note.text)
            result.append('end note')
            result.append("")

    # Done
    result.append("@enduml")
    result.append("")
    return result
