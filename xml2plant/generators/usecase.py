#!/bin/env python2
import logging
from common import quote_if_space

from parsers.parser import PartType
from parsers.parser import EventType
from parsers.parser import MessageType


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
