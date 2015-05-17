#!/bin/env python
import logging

from parsers.parser import Participant
from parsers.parser import PartType

def get_usecase_list(xml_node):
    result = []
    for usecase in xml_node.findall("ISubsystem/Declaratives/IRPYRawContainer/IUCDiagram"):
        name = usecase.xpath("_name/text()")[0]
        result.append(name)
    return result


def parse_usecases(xml_node):

    data_usecases = {}
    for usecase in xml_node.findall("ISubsystem/UseCases/IRPYRawContainer/IUseCase"):
        name = usecase.xpath("_name/text()")[0]
        id = usecase.xpath("_id/text()")[0]

        statechart = ""
        statechart_list = usecase.xpath("Diagrams/IRPYRawContainer/IHandle/_id/text()")
        if len(statechart_list) > 0:
            statechart = statechart_list[0]

        depends = []
        for depend_node in usecase.xpath("Dependencies/IRPYRawContainer/IDependency"):
            if depend_node.xpath("_dependsOn/INObjectHandle/_m2Class/text()")[0] == "IUseCase":
                depend_id = depend_node.xpath("_dependsOn/INObjectHandle/_id/text()")[0]
                # Remove duplets
                if depend_id not in depends:
                    depends.append(depend_id)

        associations = []
        for assoc_node in usecase.xpath("Associations/IRPYRawContainer/IAssociationEnd"):
            if assoc_node.xpath("_otherClass/IClassifierHandle/_m2Class/text()")[0] == "IActor":
                assoc_id = assoc_node.xpath("_otherClass/IClassifierHandle/_id/text()")[0]
                # Remove duplets
                if assoc_id not in associations:
                    associations.append(assoc_id)

        data_usecase = {}
        data_usecase['name'] = name
        data_usecase['dependencies'] = depends
        data_usecase['associations'] = associations
        data_usecase['statechart'] = statechart
        data_usecases[id] = data_usecase
        logging.debug("Parsed usecase: %s", data_usecase)
    return data_usecases


def parse_usecasediagram(xml_node, global_participants, find_name):

    # Get all usecases
    data_usecases = parse_usecases(xml_node)

    participants = {}
    data_diagrams = {}

    # Get the usecase diagram
    for diagram in xml_node.xpath("ISubsystem/Declaratives/IRPYRawContainer/IUCDiagram[_name='" + find_name + "']"):
        name = diagram.xpath("_name/text()")[0]
        logging.debug("Parsing uc-diagram: %s", name)

        # Parse boxes in diagram
        data_diagram_rects = {}
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIBox"):
            id = cgi.xpath("_id/text()")[0]

            box_name = ""
            box_name_list = cgi.xpath("m_name/CGIText/m_str/text()")
            if len(box_name_list) > 0:
                box_name = box_name_list[0]

            data_diagram_rect = {}
            data_diagram_rect['name'] = box_name
            data_diagram_rect['ucs']  = []
            data_diagram_rects[id] = data_diagram_rect

        # Parse usecases in diagram
        data_diagram_ucs = []
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass"):
            id = cgi.xpath("m_pModelObject/IHandle/_id/text()")[0]

            # Handle usecase
            if len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IUseCase']")):
                parent = cgi.xpath("m_pParent/text()")[0]
                assert id in data_usecases

                if parent in data_diagram_rects:
                    data_diagram_rects[parent]['ucs'].append(id)
                else:
                    data_diagram_ucs.append(id)

            # Handle participants
            elif len(cgi.xpath("m_pModelObject/IHandle[_m2Class='IActor']")):
                if id in global_participants:
                    participants[id] = global_participants[id]
                else:
                    actor_name = cgi.xpath("m_pModelObject/IHandle/_name/text()")[0]
                    participants[id] = Participant(PartType.ACTOR, actor_name)
            else:
                assert None

        # Parse notes in diagram
        data_diagram_notes = []
        for cgi in diagram.xpath("_graphicChart/CGIClassChart/CGIAnnotation"):
            logging.debug("Found note")
            id = cgi.xpath("_id/text()")[0]

            data_note = {}
            data_note["anchor"] = []  # List of GUIDs (lines)
            data_note["text"] = ""    # Text of note

            # Get text
            text_list = cgi.xpath("m_name/CGIText/m_str/text()")
            if len(text_list) > 0:
                data_note["text"] = text_list[0]

            # Get anchors to note
            for cgi_anchor in diagram.xpath("_graphicChart/CGIClassChart/CGIAnchor[m_pSource='" + id + "']"):
                logging.debug("Found anchor to note")

                target_list = cgi_anchor.xpath("m_pTarget/text()")
                assert len(target_list) == 1

                # Get where its pointing
                for cgi_anchor_object in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + target_list[0] + "']/m_pModelObject/IHandle/_id/text()"):
                    data_note["anchor"].append(cgi_anchor_object)

            for cgi_anchor in diagram.xpath("_graphicChart/CGIClassChart/CGIAnchor[m_pTarget='" + id + "']"):
                logging.debug("Found anchor to note")

                source_list = cgi.xpath("m_pSource/text()")
                assert len(source_list) == 1

                # Get where its pointing
                for cgi_anchor_object in diagram.xpath("_graphicChart/CGIClassChart/CGIBasicClass[_id='" + source_list[0] + "']/m_pModelObject/IHandle/_id/text()"):
                    data_note["anchor"].append(cgi_anchor_object)

            data_diagram_notes.append(data_note)


        logging.debug("Parsed free usecases: %s", data_diagram_ucs)
        logging.debug("Parsed uc-diagram boxes: %s", data_diagram_rects)
        logging.debug("Parsed uc-diagram notes: %s", data_diagram_notes)
                    
        # Add results
        data_diagram = {}
        data_diagram["rect_ucs"] = data_diagram_rects
        data_diagram["free_ucs"] = data_diagram_ucs
        data_diagram["notes"] = data_diagram_notes
        data_diagrams[name] = data_diagram

    return data_usecases, participants, data_diagrams
